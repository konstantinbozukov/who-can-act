# who-can-act

[![License: MIT](https://img.shields.io/github/license/konstantinbozukov/who-can-act)](./LICENSE)

Read-only inventory of local tools that can act as you: Cursor MCP servers, Claude Desktop MCP config, and Chrome/Edge extensions.

Okta will discover shadow agents if you already bought Okta. **who-can-act** is for everyone else. It does not revoke anything, does not test whether keys still work, does not open a network socket, and does not print secrets on purpose — treat the report as sensitive anyway.

## Why this exists

MCP servers and browser extensions can read mail, drive a browser, or hold API keys, often without a single list of what is connected. This script reads the local config and extension folders you already have and prints a ranked markdown table. That is the whole job.

## 30-second run

Python 3, standard library only. Nothing to pip install.

```bash
git clone https://github.com/konstantinbozukov/who-can-act
cd who-can-act
python3 who_can_act.py
```

(`python who_can_act.py` is the same script, if `python` is what you have on PATH.)

The only flag is `--out`, which also writes the markdown to a file:

```bash
python3 who_can_act.py --out report.md
```

Prefer a filename that stays out of git. The repo ignores `report.md` and `*.report.md`; other `--out` paths are not ignored.

## What you get

A markdown table ranked **high / medium / low**, then a short "you, not this tool" reminder. High, in the current code, is an MCP name or kind that matches `gmail`, `google`, `browser`, `app-control`, `slack`, or `github`, or a browser extension with broad permissions (for example `<all_urls>`, cookies, history). Medium is other configured MCP servers. Low is a limited extension.

The report shape (synthetic, not a real machine) is in [examples/report.example.md](examples/report.example.md).

The report is yours to delete. Do not paste a live scan into a public gist if it names private projects or still contains a secret the regex missed.

Optional Cursor skill: copy `skill/SKILL.md` to `.cursor/skills/who-can-act/SKILL.md` in a repo.

## What is scanned

| Source | Path (per OS) |
|--------|----------------|
| Cursor MCP | `~/.cursor/mcp.json` and `~/.cursor/projects/*/mcps/*/SERVER_METADATA.json` — all OSes |
| Claude Desktop MCP | Windows: `%APPDATA%\Claude\claude_desktop_config.json`; macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`; Linux: `~/.config/Claude/claude_desktop_config.json` |
| Chrome extensions | Windows: `%LOCALAPPDATA%\Google\Chrome\User Data\Default\Extensions`; macOS: `~/Library/Application Support/Google/Chrome/Default/Extensions`; Linux: `~/.config/google-chrome/Default/Extensions` and `~/.config/chromium/Default/Extensions` |
| Edge extensions | Windows: `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Extensions`; macOS: `~/Library/Application Support/Microsoft Edge/Default/Extensions`; Linux: `~/.config/microsoft-edge/Default/Extensions` |

MCP configs may include `//` or `/* */` comments (JSONC-style); the script strips comments before parsing. Non-default browser profiles, remote/cloud agents, and Google third-party OAuth grants that are not in these files are out of scope. Redaction is best-effort (query-string parameters and common token prefixes); treat stdout and `--out` files as sensitive.

## Scope and non-goals

Not a pentest. Not a keylogger. Not auto-revoke. Not a hosted dashboard. Not an npm or PyPI package.

## Related

- In-repo human accept before irreversible steps: [who-approved](https://github.com/konstantinbozukov/who-approved)
- Optional runtime consult before an x402 payment: [agent-trust-layer](https://github.com/konstantinbozukov/agent-trust-layer)

## License

MIT. See [LICENSE](LICENSE).