# AGENTS.md

Rules for Cursor agents working in `who-can-act`. Findings and evidence are in `docs/AUDIT.md` (audit date 2026-11-13, commit `e58c850`).

## What this is

`who-can-act` prints a read-only markdown inventory of local tools that can act as the user: Cursor MCP servers, Claude Desktop MCP config, and Chrome/Edge extensions. It ranks rows high / medium / low. It does not revoke access, does not test whether credentials work, and is not a hosted dashboard.

The safety contract is the module docstring in `who_can_act.py` and the rules in `skill/SKILL.md`. Keep that contract. A live scan can still contain private paths and, because redaction is incomplete, credential material. Treat stdout and `--out` files as sensitive. Never commit them.

Owner: Konstantin Bozukov. Public repo: `https://github.com/konstantinbozukov/who-can-act`. Default branch: `master`.

## Stack

- Python, standard library only: `argparse`, `json`, `pathlib`, `re`, `sys`.
- Output is markdown on stdout, plus an optional `--out` file.
- No package, no web framework, no database, no network calls.

This audit ran the script with Python 3.12.3. The README says "Python 3". TODO: confirm with Konstantin the minimum Python version he wants supported.

## Folder layout

```text
who_can_act.py                 CLI. All scan, rank, redact, and render logic.
README.md                      Install and product boundaries.
LICENSE                        MIT, Copyright (c) 2026 Konstantin Bozukov.
.gitignore                     Ignores .env, virtualenvs, bytecode, and live reports.
examples/report.example.md     Synthetic report shape. Not a real machine.
records/WA-0001-public-github.md
                               Accepted decision to publish the public repo.
skill/SKILL.md                 Optional Cursor skill. Copy, do not require it to run the CLI.
docs/AUDIT.md                  Evidence-based audit. Read it before changing behavior.
```

There is no `src/`, no test directory, no `pyproject.toml`, no `.github/`, and no application config file.

## Install

No dependency install. From a clone:

```text
git clone https://github.com/konstantinbozukov/who-can-act
cd who-can-act
```

Do not add a dependency, lockfile, or virtualenv requirement unless Konstantin asks.

## Run

Documented command, from `README.md`:

```text
python who_can_act.py
```

Verified on the Linux audit host (Python 3.12.3):

```text
python3 who_can_act.py --help
```

Exit 0. The only flag is `--out`, which also writes the markdown to a file.

```text
python who_can_act.py --help
```

Exit 127 on that host (`python: command not found`). TODO: confirm with Konstantin that the documented `python` command is the one to keep for his Windows machines.

Smoke the CLI without reading a real home directory:

```text
mkdir -p /tmp/wca-empty
HOME=/tmp/wca-empty python3 who_can_act.py
```

Verified: exit 0, and the table says nothing was found in the default scan paths.

`main` always uses `Path.home()` (`who_can_act.py:235`). There is no `--home` flag. Chrome, Edge, and Claude paths are built only under Windows `AppData` (`who_can_act.py:112`, `who_can_act.py:239-258`). TODO: confirm with Konstantin whether non-Windows scan paths are in scope.

## Test

No tests are in the tree. Verified from the repo root:

```text
python3 -m py_compile who_can_act.py
```

Exit 0.

```text
python3 -m unittest discover -s /workspace -v
```

`Ran 0 tests in 0.000s`, `NO TESTS RAN`, exit 5.

```text
python3 -m pytest
```

`/usr/bin/python3: No module named pytest`, exit 1. pytest is not a project dependency. Do not install it into the repo to invent a suite.

After a behavior change, compile with `python3 -m py_compile who_can_act.py` and run against a temporary `HOME` that contains only synthetic JSON. Do not point that run at a real MCP config, and do not commit the report.

## Lint

No linter, formatter, or type-check config is in the repo. `ruff`, `flake8`, `mypy`, and `pyright` were not on the audit host PATH. There is no lint command to run. Do not add one unless Konstantin asks.

## Build

There is no build, package, or `pyproject.toml`. The shebang is `#!/usr/bin/env python3`. The file mode in git is not executable (`644`), so run it with the interpreter. Shipping is the source file itself.

## Deploy

Nothing is deployed. Runtime is the user's computer. The source is the public GitHub repo on `master`.

Verified absent: `.github/workflows`, GitHub Actions runs (zero), GitHub releases (none), GitHub Pages (`has_pages` false). `README.md:27` says this is not a hosted dashboard. `records/WA-0001-public-github.md:29` says there is no hosted user data, and the kill switch is to archive the GitHub repo.

Do not add a host, a container, or a pipeline in a drive-by change.

## External services

The CLI does not call Supabase, Vercel, AWS, or any other network API. Imports stop at the standard library. No `os.environ` reads.

The README and the decision record name two other Konstantin repos as neighbors, not as runtime dependencies:

- `who-approved` (human accept before irreversible steps)
- `tech-business-ideas`, path cited as `ideas/023-who-can-act/intake.md` (that file is not in this repo)

TODO: confirm with Konstantin whether that intake note is still the product constraint.

## Conventions inferred from the code

- One module, functions only, no classes. The safety contract stays at the top of `who_can_act.py`.
- `from __future__ import annotations`, type hints, `pathlib`, and `argparse`.
- A scan row is a `dict` with string keys `source`, `name`, `can`, `env_keys`, and `rank`.
- Ranks are the words `high`, `medium`, and `low`. An empty display cell is the em dash `—`.
- Unreadable or invalid JSON is skipped (`load_json` returns `None`). The scan continues.
- High MCP rank is a substring match on `gmail`, `google`, `browser`, `app-control`, `slack`, and `github` (`who_can_act.py:38`). The README's definition of high is narrower (`README.md:21`). Do not "fix" that mismatch unless Konstantin picks one rule.
- `examples/report.example.md` stays synthetic. The real report shape is produced by `render`.
- Decision records in `records/` use YAML front matter (`id`, `title`, `status`, `date`, `irreversible`, `proposed_by`, `accepted_by`) and a short why / alternatives / blast radius.
- `skill/SKILL.md` is optional. It tells an agent to run the CLI, show the report, and refuse to publish a live scan. Point public examples at `examples/report.example.md`.

## Never touch

- Secrets, raw MCP JSON, and live scan output. `.gitignore` ignores `.env`, `.env.*`, `report.md`, and `*.report.md`. Other `--out` paths are not ignored. Do not commit them.
- Production data. This repo has none. Do not add a database or a dump.
- Migrations. This repo has none. Do not add a migration tool or schema history.
- Store or deploy config. This repo has none. Do not add Supabase, Vercel, AWS, Docker, or CI config unless Konstantin asks.
- `records/WA-0001-public-github.md`, unless he asks to amend that decision. `accepted_at` is earlier than `proposed_at` (`records/WA-0001-public-github.md:8-10`). TODO: confirm with Konstantin before rewriting it.
- Revoke, delete, or credential-probe actions. This tool only reads local files. Do not extend it into auto-revoke or a key checker.
