---
name: who-can-act
description: >-
  Runs the local who-can-act inventory of MCP servers and browser extensions
  that can act as the user. Use when the user asks what agents have access,
  what MCP is connected, shadow agents, or who-can-act. Read-only; never
  revoke, never test stolen credentials, never print secrets.
---

# who-can-act

## Rules

1. Run `python who_can_act.py` from this repo (or the path the user gives).
2. Show the markdown report. Do not add exploit steps, payloads, or “try this key against the API.”
3. Redact anything that still looks like a secret if it appears in tool output.
4. Do not revoke OAuth grants, delete MCP servers, or uninstall extensions unless the user explicitly asks to do that themselves in the host product — this skill only inventories.
5. If they want a public post of the report, refuse to publish a live scan; point at `examples/report.example.md`.
