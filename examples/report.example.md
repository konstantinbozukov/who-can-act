# who-can-act report

Read-only. Secrets redacted. Nothing was revoked. Credentials were not tested.

| Rank | Name | Can act as you via | Source |
|------|------|--------------------|--------|
| high | gmail | https://gmailmcp.example/mcp/v1 | ~/.cursor/mcp.json |
| high | cursor-ide-browser | browser | Cursor project MCP catalog |
| high | Password manager | broad: cookies, `<all_urls>` | Chrome |
| medium | notes-mcp | npx example-mcp | ~/.cursor/mcp.json |
| low | Dictionary | limited | Chrome |

## Next (you, not this tool)

- Revoke what you do not recognize in the host product (Cursor, Chrome, Google Account).
- For Google third-party apps this CLI cannot see, open your Google account permissions page yourself.
- Do not paste this report into a public gist if it names private projects.
