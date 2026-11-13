# Audit: who-can-act

Audit date: 2026-11-13. Tree audited: `e58c850` (`Publish a read-only map of local tools that can act as you.`, 2026-09-12). Host: Linux, CPython 3.12.3. No application code, config, or dependency was changed. The scanner was not pointed at a real home directory. Fixtures lived under `/tmp/wca-empty`, `/tmp/wca-fixture`, and `/tmp/wca-jsonc` and used synthetic names only.

Tracked files at audit time: `.gitignore`, `LICENSE`, `README.md`, `examples/report.example.md`, `records/WA-0001-public-github.md`, `skill/SKILL.md`, `who_can_act.py`.

## Summary

who-can-act is a public, local, read-only inventory of Cursor MCP servers, Claude Desktop MCP config, and Chrome/Edge extensions, implemented as one Python standard-library script plus a README, MIT license, synthetic example report, Cursor skill, and one accepted publish record. On Python 3.12.3 it compiles, prints a markdown table, and exits 0 for an empty home and for a temporary home filled with synthetic JSON. The GitHub project was created 2026-09-12, still has that single commit, zero open issues, zero Actions runs, and no release. Maturity is **working**: the CLI does the scan the README describes when the Windows default paths exist. It is not a production service. There is no test suite, no CI, no package, and the redaction and path logic have the gaps below.

## Stack and hosting

- Language and runtime: Python, standard library only (`argparse`, `json`, `pathlib`, `re`, `sys`). No `pyproject.toml`, `requirements.txt`, `setup.cfg`, or `Pipfile`.
- Interface: markdown table on stdout, optional `--out` path (`who_can_act.py:229-264`).
- Source host: public GitHub repo `konstantinbozukov/who-can-act`, default branch `master`, MIT license, language Python. Created 2026-09-12. `has_pages` is false. Description matches the README: a read-only inventory of local MCP servers and extensions.
- Execution host: the user's own computer. The process does not open a socket. There is no Supabase, Vercel, AWS, Docker, or database client in the tree.
- Neighbors, named in prose only: `who-approved`, and `ideas/023-who-can-act/intake.md` inside `tech-business-ideas` (`records/WA-0001-public-github.md:33`). That intake file is not in this repository.

## Deploy path

There is no deploy. Users clone the repo and run the script (`README.md:11-15`). `README.md:27` states it is not a hosted dashboard. The publish record says the blast radius is the public name and README, there is no hosted user data, and the kill switch is to archive the GitHub repo (`records/WA-0001-public-github.md:27-29`).

Checked and absent:

- `.github/workflows` is not in the tree. GitHub Actions `list_workflow_runs` returned `total_count` 0.
- The GitHub releases list was empty. Tags were not listed separately.
- GitHub Pages is off (`has_pages` false).
- No Dockerfile, no `vercel.json`, no `netlify.toml`, no `fly.toml`, no cloud-formation or terraform files.

Publishing a change is a git push to `master`. Nothing builds or promotes it after that.

## Environment variables

The application reads no environment variables. `who_can_act.py` does not call `os.environ` or `getenv`. No `.env` or `.env.example` is tracked. `.gitignore` lists `.env` and `.env.*`.

There are no application configuration names to publish. Cursor and Claude MCP configs can contain an `env` object. Those keys belong to the user's MCP servers, not to this repo. In a synthetic fixture the Cursor key name was collected on the row and then omitted from the rendered table (see bugs). The synthetic value was not printed.

## Tests

No test files, no CI, and no install step beyond the system Python. Nothing was installed with pip. pytest, ruff, flake8, mypy, and pyright were not on PATH.

| Command | Result |
| --- | --- |
| `python3 --version` | `Python 3.12.3` |
| `python3 -m py_compile who_can_act.py` | exit 0 |
| `python3 who_can_act.py --help` | exit 0. Usage is `who_can_act.py [-h] [--out OUT]`. |
| `python who_can_act.py --help` | exit 127, `python: command not found` |
| `HOME=/tmp/wca-empty python3 who_can_act.py` | exit 0. Table cell: `nothing found in default scan paths`. |
| `python3 -m unittest discover -s /workspace -v` | `Ran 0 tests in 0.000s`, `NO TESTS RAN`, exit 5 |
| `python3 -m pytest` | `/usr/bin/python3: No module named pytest`, exit 1 |

Coverage is none. The unittest and pytest commands did not pass. The compile and the empty-home smoke did.

A second, uncommitted fixture under `HOME=/tmp/wca-fixture` exercised `python3 who_can_act.py` end to end (exit 0) and is the source of the behavior notes below. A third home, `/tmp/wca-jsonc`, held a `mcp.json` with a `//` comment.

## Bugs and likely bugs

Verified means the fixture or command showed it. Code-evident means the line does it and this audit did not execute that branch.

1. **Wrong Chrome version wins.** `who_can_act.py:178` sets `latest = max(versions, key=lambda p: p.name)`. Folder names sort as strings, so `1.9.0_0` is greater than `1.10.0_0`. Fixture: manifest name `Old Dictionary` in `1.9.0_0` and `New Dictionary` in `1.10.0_0`. The report included `Old Dictionary` and did not include `New Dictionary`. The `version` field inside the manifest is never read.

2. **MCP URLs are copied into the report with query strings intact.** `who_can_act.py:75` uses `url` as the "can" cell, then `redact` (`who_can_act.py:15-21`). The regex does not strip query parameters. Fixture: a synthetic `https` URL with an `api_key` query was printed unchanged in the table.

3. **`sk-` redaction stops at the first extra hyphen.** `who_can_act.py:16` uses `sk-[a-z0-9]+`. A synthetic value with a segment after a second hyphen came back as `[redacted]` plus that tail. A synthetic `ghp_` value was fully replaced. A synthetic `github_pat_` value and a synthetic `AKIA` prefix were unchanged. `Bearer` plus a token was fully replaced.

4. **JSON with comments is treated as "no servers".** `who_can_act.py:26-30` returns `None` on `JSONDecodeError`, and `who_can_act.py:67-71` then uses an empty server map. Fixture file with a `//` comment: `scan_cursor_mcp` returned `[]`. TODO: confirm with Konstantin whether his `mcp.json` files are strict JSON. Cursor configs are often strict JSON; if a comment is ever present, the whole user MCP list disappears with no error.

5. **Env key names are collected and then dropped.** Cursor scan stores them at `who_can_act.py:76-82`. `render` (`who_can_act.py:201-208`) has columns Rank, Name, Can act as you via, and Source. Fixture key name `EXAMPLE_TOKEN` was on the row and absent from the report. Claude scan never reads `env` and hardcodes the em dash (`who_can_act.py:127`). Fixture Claude server `slack` had an env key; the row still said `—`.

6. **Markdown table breaks on `|` in a name.** `who_can_act.py:206-208` interpolates name, can, and source with no escaping. Fixture server name `notes|inject` rendered as an extra column.

7. **Source cells are absolute paths.** `who_can_act.py:79` and `who_can_act.py:125` store `str(path)`. The fixture report contained `/tmp/wca-fixture/.cursor/mcp.json` and the Claude path under that home. On a real machine that is the username and profile path. The example report uses `~/.cursor/mcp.json` (`examples/report.example.md:8`).

8. **Browser and Claude scans are Windows `AppData` paths only.** Claude: `who_can_act.py:112`. Chrome and Edge: `who_can_act.py:239-258`. There is no `sys.platform` branch. A synthetic extension placed at `Library/Application Support/Google/Chrome/...` (`Mac Only Ext`, with `<all_urls>`) did not appear. A synthetic extension under Chrome `Profile 1` (`Profile One Ext`) did not appear. Edge was not given a fixture; the code uses the same Default-profile pattern as Chrome. TODO: confirm with Konstantin that Windows-only paths are intentional. The README does not say Windows-only (`README.md:5`).

9. **One site is labeled "many sites" and ranked high.** `who_can_act.py:160-161` treats any permission starting with `http` (so every `https://` host) as `many sites`. `who_can_act.py:167` and `who_can_act.py:189` then mark that `broad` and `high`. Fixture extension `One Site` with only `https://example.test/*` rendered as `broad: many sites`, rank high.

10. **Rank keywords are wider than the README.** `who_can_act.py:38` marks high when the name or kind contains `gmail`, `google`, `browser`, `app-control`, `slack`, or `github`. `README.md:21` defines high as Gmail, browser control, or an extension with broad permissions. Fixture server `plain-github` with `"type": "stdio"` rendered rank high and can-cell `stdio`. Direct call: `rank_mcp("google-calendar", "x")` returned `high`. `filesystem` stayed `medium`.

11. **Same display name hides a second server.** `who_can_act.py:94-95` skips a project-catalog server whose lowercased name was already seen. Fixture: `gmail` in `mcp.json` plus a project-catalog `gmail` with a different identifier. The report had one `gmail` row.

12. **`--out` to a missing directory crashes after stdout.** `who_can_act.py:262-264` writes stdout first, then `write_text`. Command: `HOME=/tmp/wca-fixture python3 who_can_act.py --out /tmp/wca-no-such-dir/out.md`. Stdout still started with `# who-can-act report`. Exit 1, `FileNotFoundError` for that path.

13. **Capability string drops args.** `who_can_act.py:75` keeps `url`, else `command`, else `type`. Fixture `gmail` command `npx` with args was rendered as `npx` only. Headers are not read. A secret in `args` is therefore not printed; the report also does not say what the process will run.

14. **Optional extension permissions are counted as granted.** Code-evident, not fixture-tested: `who_can_act.py:153-156` merges `optional_permissions` with `permissions` and `host_permissions` before labeling.

15. **Decision record timestamps are out of order.** `records/WA-0001-public-github.md:8-10`: `proposed_at` is `2026-09-12T15:30:00Z` and `accepted_at` is `2026-09-12T15:28:00Z`. The git commit itself is later that day (`2026-09-12 14:57:17 -0700`).

16. **Documented interpreter was missing on the audit host.** `README.md:14` says `python who_can_act.py`. That command exited 127 here. `python3` worked. TODO: confirm with Konstantin which command the README should show.

## Security

No committed secret was found. Every tracked file was read. `git log -p --all` matched a token-like pattern only on the redaction regex already in `who_can_act.py:16`. No `.env` file is in the tree. GitHub reports secret scanning and secret-scanning push protection as enabled for this repo. This audit did not read the secret-scanning alerts API.

Risks that are in the current behavior:

- **Stdout and `--out` can still carry credentials.** Query strings on MCP URLs are printed (`who_can_act.py:75`, `who_can_act.py:15-21`). The `sk-` pattern leaves a tail, and `github_pat_` / `AKIA` shapes are not in the regex. The tool's own claim is that secrets are redacted (`who_can_act.py:4`, `who_can_act.py:199`). Env *values* were not printed in the fixture, because the code keeps only key names and then drops those names too.
- **Absolute paths put the OS username in the report** (`who_can_act.py:79`, `who_can_act.py:125`). The report text tells the user not to paste it into a public gist (`who_can_act.py:218`).
- **Live reports are only partly gitignored.** `.gitignore:8-10` ignores `report.md` and `*.report.md`, and keeps `examples/report.example.md`. An `--out` path such as `docs/scan.md` is not ignored. The publish record says live scan reports must not be committed (`records/WA-0001-public-github.md:29`).
- **Untrusted names are copied into markdown the skill tells an agent to show.** `who_can_act.py:206-208` and `skill/SKILL.md:14-15`. A local extension or MCP name can break the table or carry instruction text. This is a local file the user already has, not a remote payload. The skill also says to refuse publishing a live scan and to redact anything that still looks like a secret (`skill/SKILL.md:16-18`).
- **No network, no revoke, no credential probe.** Confirmed by reading the module: no `urllib`, `socket`, `subprocess`, or HTTP client. That part of the contract holds.
- **Dependabot security updates are disabled** on the GitHub repo. There is no third-party dependency for Dependabot to update. See the next section.

## Dependencies and staleness

No third-party runtime or test dependency is declared, so there is no outdated package list and no lockfile to drift. `pip` is not part of the documented install. Dependabot security updates are disabled; with an empty dependency set that does not leave a known vulnerable package unpinned.

The repo itself has not moved since 2026-09-12 (`e58c850`). The GitHub releases list was empty. The script is not packaged and the file is mode `644`, so the shebang is unused unless someone chmod's it. There is no pinned interpreter. Only CPython 3.12.3 was executed in this audit.

## Top 5 improvements

Ranked by value against effort. Effort is relative to this one-file repo.

1. **Make redaction match the promise, and escape the table.** Highest value, small effort. Before a URL or command is printed, drop userinfo and query strings, treat an `sk-` value as more than one hyphenated segment, and cover the other prefixes the current regex misses (`who_can_act.py:15-21`). Escape `|` and newlines in `render` (`who_can_act.py:206-208`). Prefer `~` over the absolute home path (`who_can_act.py:79`). This is the change that protects the report the tool exists to print.

2. **Select the extension version by numeric order or by the manifest `version`.** High value, small effort. Replace the string `max` at `who_can_act.py:178`. The fixture showed a newer folder being ignored. One comparison function plus a fixture locks it.

3. **Add `--home` and a stdlib `unittest` module.** High value, medium effort. `main` always calls `Path.home()` (`who_can_act.py:235`), and `unittest discover` currently collects nothing. A home override plus fixtures for redaction, version order, rank, JSON comments, and the empty report would have caught the items above. Keep the tests on the standard library so the "no dependency" install stays true. Document `python3` if Konstantin wants Linux in the README.

4. **Scan the paths of the OS the user is on, including non-Default browser profiles.** High value for the public README, medium effort. Today Claude, Chrome, and Edge are only Windows `AppData` Default paths (`who_can_act.py:112`, `who_can_act.py:239-258`). The macOS-shaped fixture and the `Profile 1` fixture were invisible. TODO: confirm with Konstantin before building this. On his Windows laptop the Default path is the one the code already uses, so this item matters more to other people who clone the public repo.

5. **Print the env key names already collected, and align the rank rule with the README.** Medium value, small effort. The Cursor row already has `env_keys` (`who_can_act.py:76-82`) and `render` drops them. Claude should collect key names the same way, still without values (`who_can_act.py:127`). Separately, decide whether `github` / `google` / `slack` substrings should force high (`who_can_act.py:38`) or whether the README's narrower definition (`README.md:21`) is the rule. A server named `plain-github` with type `stdio` is high today.

## Open questions

- Are Windows Default-profile paths the intended support matrix, or should macOS, Linux, and extra Chrome/Edge profiles be scanned?
- Should an MCP URL be printed at all, or only its scheme and host, with query strings always removed?
- Should env var *names* from MCP configs appear in the table? They are collected for Cursor and currently discarded. Values should stay unprinted.
- Is the high-rank keyword list (`google`, `github`, `slack`, and the others at `who_can_act.py:38`) intentional, given `README.md:21`?
- Is the `accepted_at` / `proposed_at` order in `records/WA-0001-public-github.md` a mistake to correct, and should later decisions get new `records/WA-####` files?
- Which Python versions must keep working? Only 3.12.3 was run here. The README says "Python 3".
- Should per-repo `.cursor/mcp.json` files be scanned, or only `~/.cursor/mcp.json` and the catalog under `~/.cursor/projects`?
- Is distribution supposed to stay "clone and run", with no package and no GitHub release?
- `records/WA-0001-public-github.md:20` cites a public-GitHub ceiling and `ideas/023-who-can-act/intake.md` in another repo. Is that constraint still binding?
