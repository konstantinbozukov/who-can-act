# who-can-act

Okta will discover shadow agents if you already bought Okta. **who-can-act** is for everyone else.

It prints a **read-only** list of local tools that can act as you: Cursor MCP servers, optional Claude desktop MCP, Chrome/Edge extensions. It does not revoke anything, does not test whether keys still work, and does not print secrets.

## Install

Python 3, standard library only:

```text
git clone https://github.com/konstantinbozukov/who-can-act
cd who-can-act
python who_can_act.py
```

Optional Cursor skill: copy `skill/SKILL.md` to `.cursor/skills/who-can-act/SKILL.md` in a repo.

## What you get

A markdown table ranked **high / medium / low**. High means Gmail, browser control, or an extension with broad permissions. The report is yours to delete.

See [examples/report.example.md](examples/report.example.md) for the shape (synthetic; not a real machine).

## What this is not

Not a pentest. Not a keylogger. Not auto-revoke. Not a hosted dashboard. Adjacent to [who-approved](https://github.com/konstantinbozukov/who-approved) (human accept before irreversible steps) and to inbox-list cleanup — this one is the permission surface.

## License

MIT. See [LICENSE](LICENSE).
