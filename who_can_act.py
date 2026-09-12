#!/usr/bin/env python3
"""Read-only inventory of local tools that can act as you.

Does not print secrets, test credentials, or revoke access.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECRET_VAL = re.compile(
    r"(?i)(sk-[a-z0-9]+|ghp_[a-z0-9]+|xox[baprs]-[a-z0-9-]+|bearer\s+\S+|AIza[0-9A-Za-z_-]{20,})"
)
def redact(value: object) -> str:
    text = str(value)
    text = SECRET_VAL.sub("[redacted]", text)
    if len(text) > 120:
        return text[:117] + "..."
    return text


def load_json(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


MSG_NAME = re.compile(r"^__MSG_(.+)__$")


def rank_mcp(name: str, kind: str) -> str:
    blob = f"{name} {kind}".lower()
    if any(w in blob for w in ("gmail", "google", "browser", "app-control", "slack", "github")):
        return "high"
    return "medium"


def locale_message(ext_version: Path, key: str, default_locale: str | None) -> str | None:
    locales = []
    if default_locale:
        locales.append(default_locale)
    locales.extend(["en", "en_US", "en_GB"])
    seen: set[str] = set()
    for loc in locales:
        if loc in seen:
            continue
        seen.add(loc)
        data = load_json(ext_version / "_locales" / loc / "messages.json")
        if isinstance(data, dict):
            entry = data.get(key)
            if entry is None:
                lower = {str(k).lower(): v for k, v in data.items()}
                entry = lower.get(key.lower())
            if isinstance(entry, dict) and entry.get("message"):
                return str(entry["message"])
    return None


def scan_cursor_mcp(home: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_names: set[str] = set()
    cfg = home / ".cursor" / "mcp.json"
    data = load_json(cfg)
    servers = {}
    if isinstance(data, dict):
        servers = data.get("mcpServers") or data.get("servers") or {}
    if isinstance(servers, dict):
        for name, spec in servers.items():
            spec = spec if isinstance(spec, dict) else {}
            kind = spec.get("url") or spec.get("command") or spec.get("type") or "configured"
            env_keys = sorted((spec.get("env") or {}).keys()) if isinstance(spec.get("env"), dict) else []
            rows.append(
                {
                    "source": str(cfg),
                    "name": str(name),
                    "can": redact(kind),
                    "env_keys": ", ".join(env_keys) if env_keys else "—",
                    "rank": rank_mcp(str(name), str(kind)),
                }
            )
            seen_names.add(str(name).lower())
    projects = home / ".cursor" / "projects"
    if projects.is_dir():
        for meta in projects.glob("*/mcps/*/SERVER_METADATA.json"):
            payload = load_json(meta)
            if not isinstance(payload, dict):
                continue
            name = str(payload.get("serverName") or payload.get("serverIdentifier") or meta.parent.name)
            if name.lower() in seen_names:
                continue
            ident = str(payload.get("serverIdentifier") or "")
            can = ident or meta.parent.name
            seen_names.add(name.lower())
            rows.append(
                {
                    "source": "Cursor project MCP catalog",
                    "name": name,
                    "can": redact(can),
                    "env_keys": "—",
                    "rank": rank_mcp(name, can),
                }
            )
    return rows


def scan_claude(home: Path) -> list[dict[str, str]]:
    path = home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    data = load_json(path)
    if not isinstance(data, dict):
        return []
    servers = data.get("mcpServers") or {}
    rows = []
    if isinstance(servers, dict):
        for name, spec in servers.items():
            spec = spec if isinstance(spec, dict) else {}
            kind = spec.get("url") or spec.get("command") or "claude mcp"
            rows.append(
                {
                    "source": str(path),
                    "name": str(name),
                    "can": redact(kind),
                    "env_keys": "—",
                    "rank": rank_mcp(str(name), str(kind)),
                }
            )
    return rows


def manifest_name(manifest: dict, ext_version: Path) -> str:
    raw = manifest.get("name")
    default_locale = manifest.get("default_locale")
    if isinstance(raw, str):
        match = MSG_NAME.match(raw)
        if match:
            resolved = locale_message(ext_version, match.group(1), str(default_locale) if default_locale else None)
            if resolved:
                return resolved
        elif not raw.startswith("__MSG_"):
            return raw
    short = manifest.get("short_name")
    if isinstance(short, str) and not short.startswith("__MSG_"):
        return short
    return str(raw or "extension")


def extension_flags(manifest: dict) -> str:
    perms: list[str] = []
    for key in ("permissions", "optional_permissions", "host_permissions"):
        val = manifest.get(key) or []
        if isinstance(val, list):
            perms.extend(str(x) for x in val)
    labels: list[str] = []
    if any(p in ("<all_urls>", "*://*/*") for p in perms):
        labels.append("all sites")
    elif any(p.startswith("*://") or p.startswith("http") for p in perms):
        labels.append("many sites")
    for token in ("cookies", "history", "clipboardRead", "nativeMessaging", "debugger"):
        if token in perms:
            labels.append(token)
    if not labels:
        return "limited"
    return "broad: " + ", ".join(labels)


def scan_extensions(root: Path, browser: str) -> list[dict[str, str]]:
    if not root.is_dir():
        return []
    rows = []
    for ext_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        versions = [p for p in ext_dir.iterdir() if p.is_dir()]
        if not versions:
            continue
        latest = max(versions, key=lambda p: p.name)
        manifest = load_json(latest / "manifest.json")
        if not isinstance(manifest, dict):
            continue
        flags = extension_flags(manifest)
        rows.append(
            {
                "source": browser,
                "name": manifest_name(manifest, latest),
                "can": flags,
                "env_keys": "—",
                "rank": "high" if flags.startswith("broad") else "low",
            }
        )
    return rows


def render(rows: list[dict[str, str]]) -> str:
    lines = [
        "# who-can-act report",
        "",
        "Read-only. Secrets redacted. Nothing was revoked. Credentials were not tested.",
        "",
        "| Rank | Name | Can act as you via | Source |",
        "|------|------|--------------------|--------|",
    ]
    order = {"high": 0, "medium": 1, "low": 2}
    for row in sorted(rows, key=lambda r: (order.get(r["rank"], 9), r["name"].lower())):
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['can']} | {row['source']} |"
        )
    if not rows:
        lines.append("| — | — | nothing found in default scan paths | — |")
    lines.extend(
        [
            "",
            "## Next (you, not this tool)",
            "",
            "- Revoke what you do not recognize in the host product (Cursor, Chrome, Google Account).",
            "- For Google third-party apps this CLI cannot see, open your Google account permissions page yourself.",
            "- Do not paste this report into a public gist if it names private projects.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List local MCP servers and extensions that can act as you."
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Write markdown here as well as stdout",
    )
    args = parser.parse_args()
    home = Path.home()
    rows: list[dict[str, str]] = []
    rows.extend(scan_cursor_mcp(home))
    rows.extend(scan_claude(home))
    chrome = (
        home
        / "AppData"
        / "Local"
        / "Google"
        / "Chrome"
        / "User Data"
        / "Default"
        / "Extensions"
    )
    edge = (
        home
        / "AppData"
        / "Local"
        / "Microsoft"
        / "Edge"
        / "User Data"
        / "Default"
        / "Extensions"
    )
    rows.extend(scan_extensions(chrome, "Chrome"))
    rows.extend(scan_extensions(edge, "Edge"))
    report = render(rows)
    sys.stdout.write(report)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
