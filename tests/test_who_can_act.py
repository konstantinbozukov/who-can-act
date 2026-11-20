#!/usr/bin/env python3
"""Unit tests for who_can_act — synthetic homes only."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import who_can_act as wca


class LoadJsonTests(unittest.TestCase):
    def test_strict_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.json"
            path.write_text('{"a": 1}', encoding="utf-8")
            self.assertEqual(wca.load_json(path), {"a": 1})

    def test_jsonc_line_comment_and_trailing_comma(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mcp.json"
            path.write_text(
                '{\n// cursor config\n"mcpServers": {\n"x": {},\n},\n}',
                encoding="utf-8",
            )
            data = wca.load_json(path)
            self.assertIsInstance(data, dict)
            self.assertIn("mcpServers", data)

    def test_jsonc_block_comment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "block.json"
            path.write_text('{"a": 1 /* hidden */, "b": 2}', encoding="utf-8")
            self.assertEqual(wca.load_json(path), {"a": 1, "b": 2})


class RedactTests(unittest.TestCase):
    def test_sk_token(self) -> None:
        self.assertEqual(wca.redact("key sk-abc123-def456 here"), "key [redacted] here")

    def test_ghp_and_github_pat(self) -> None:
        self.assertIn("[redacted]", wca.redact("ghp_abcdef1234567890"))
        self.assertIn("[redacted]", wca.redact("github_pat_11AAAA"))

    def test_query_string_secrets(self) -> None:
        out = wca.redact("https://mcp.example/v1?api_key=supersecret&other=1")
        self.assertIn("api_key=[redacted]", out)
        self.assertIn("other=1", out)

    def test_akia_prefix(self) -> None:
        self.assertIn("[redacted]", wca.redact("AKIAIOSFODNN7EXAMPLE"))


class RankMcpTests(unittest.TestCase):
    def test_high_keywords(self) -> None:
        for name in ("gmail", "my-browser-tool", "slack-mcp", "plain-github"):
            self.assertEqual(wca.rank_mcp(name, "stdio"), "high")

    def test_medium_default(self) -> None:
        self.assertEqual(wca.rank_mcp("filesystem", "npx"), "medium")


class PathDiscoveryTests(unittest.TestCase):
    def test_windows_claude_path(self) -> None:
        home = Path("/home/user")
        with mock.patch.object(sys, "platform", "win32"):
            paths = wca.claude_config_paths(home)
        self.assertEqual(
            paths[0],
            home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json",
        )

    def test_darwin_claude_path(self) -> None:
        home = Path("/Users/me")
        with mock.patch.object(sys, "platform", "darwin"):
            paths = wca.claude_config_paths(home)
        self.assertTrue(
            str(paths[0]).endswith("Library/Application Support/Claude/claude_desktop_config.json")
        )

    def test_linux_claude_and_browsers(self) -> None:
        home = Path("/home/me")
        with mock.patch.object(sys, "platform", "linux"):
            claude = wca.claude_config_paths(home)
            chrome = wca.chrome_extension_roots(home)
            edge = wca.edge_extension_roots(home)
        self.assertEqual(claude[0], home / ".config" / "Claude" / "claude_desktop_config.json")
        self.assertIn(home / ".config" / "google-chrome" / "Default" / "Extensions", chrome)
        self.assertIn(home / ".config" / "chromium" / "Default" / "Extensions", chrome)
        self.assertEqual(edge[0], home / ".config" / "microsoft-edge" / "Default" / "Extensions")


class ScanIntegrationTests(unittest.TestCase):
    def _write_cursor_mcp(self, home: Path, body: str) -> None:
        cfg = home / ".cursor"
        cfg.mkdir(parents=True)
        (cfg / "mcp.json").write_text(body, encoding="utf-8")

    def test_scan_cursor_mcp_jsonc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self._write_cursor_mcp(
                home,
                '{"mcpServers": {"notes": {"command": "npx notes"}},}',
            )
            rows = wca.scan_cursor_mcp(home)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "notes")
            self.assertEqual(rows[0]["rank"], "medium")

    def test_scan_claude_linux_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cfg = home / ".config" / "Claude"
            cfg.mkdir(parents=True)
            (cfg / "claude_desktop_config.json").write_text(
                json.dumps({"mcpServers": {"mail": {"url": "https://example/mcp"}}}),
                encoding="utf-8",
            )
            with mock.patch.object(sys, "platform", "linux"):
                rows = wca.scan_claude(home)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "mail")

    def test_scan_windows_claude_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cfg = home / "AppData" / "Roaming" / "Claude"
            cfg.mkdir(parents=True)
            (cfg / "claude_desktop_config.json").write_text(
                json.dumps({"mcpServers": {"x": {"command": "foo"}}}),
                encoding="utf-8",
            )
            with mock.patch.object(sys, "platform", "win32"):
                rows = wca.scan_claude(home)
            self.assertEqual(len(rows), 1)

    def test_scan_chrome_extension_linux(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            ext_root = home / ".config" / "google-chrome" / "Default" / "Extensions" / "abc" / "1.0_0"
            ext_root.mkdir(parents=True)
            (ext_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "Test Ext",
                        "permissions": ["cookies", "<all_urls>"],
                    }
                ),
                encoding="utf-8",
            )
            with mock.patch.object(sys, "platform", "linux"):
                rows = wca.collect_rows(home)
            names = {r["name"] for r in rows}
            self.assertIn("Test Ext", names)


class RenderTests(unittest.TestCase):
    def test_render_empty(self) -> None:
        out = wca.render([])
        self.assertIn("nothing found in default scan paths", out)
        self.assertIn("# who-can-act report", out)

    def test_render_sorts_high_first(self) -> None:
        rows = [
            {"rank": "low", "name": "z", "can": "limited", "env_keys": "—", "source": "Chrome"},
            {"rank": "high", "name": "a", "can": "browser", "env_keys": "—", "source": "mcp"},
        ]
        out = wca.render(rows)
        self.assertLess(out.index("| high | a |"), out.index("| low | z |"))


class CliOutTests(unittest.TestCase):
    def test_out_flag_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "report.md"
            with mock.patch.object(wca, "collect_rows", return_value=[]):
                with mock.patch.object(sys, "argv", ["who_can_act.py", "--out", str(out_path)]):
                    with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                        code = wca.main()
            self.assertEqual(code, 0)
            self.assertTrue(out_path.is_file())
            self.assertEqual(stdout.getvalue(), out_path.read_text(encoding="utf-8"))


class RedactInScanTests(unittest.TestCase):
    def test_mcp_url_query_redacted_in_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cfg = home / ".cursor"
            cfg.mkdir()
            (cfg / "mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "remote": {
                                "url": "https://mcp.example/v1?api_key=leakme&token=also"
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            rows = wca.scan_cursor_mcp(home)
            self.assertEqual(len(rows), 1)
            self.assertIn("[redacted]", rows[0]["can"])
            self.assertNotIn("leakme", rows[0]["can"])


if __name__ == "__main__":
    unittest.main()