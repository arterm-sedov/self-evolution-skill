# Worked examples

Each example shows the raw observation, the entry that survived, and the home it belongs to. The point is calibration: what is worth keeping, and how much detail the next session actually needs.

## 1. Windows build encoding

Raw: the docs build kept failing with a stack trace inside colorama until two environment variables were set.

Entry:

> **mkdocs on Windows.** Build crashes with a colorama `UnicodeEncodeError` on Material progress output. Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` in the shell profile; per-command variables do not survive new terminals.

Home: project skill `mkdocs-build`, references section. It recurs and has a fixed fix.

## 2. Silent query failure

Raw: a graph query returned `false` with no error; two hours of bisecting showed one predicate was unbound.

Entry:

> **Triples fail silently.** An unbound predicate returns `false`, not an error. Bisect by wrapping subsets in `assert:count`; system-name mismatches (Cyrillic vs Latin, case) are the usual cause.

Home: discovery log first, because the exact debugging recipe may still evolve; migrate to the query skill after a second confirmation.

## 3. Credential plumbing

Raw: the tunnel script reads SQL passwords from the OS keyring; each operator must store their own.

Entry:

> **Keyring key format.** `tool:{profile}:sql_password`, stored per operator. Reading `IdentityFile` from SSH config lets the script pick up keys without extra flags.

Home: skill reference. It is a stable interface detail, and every operator needs it.

Bad variant of the same finding: "Passwords are in keyring now." — no key format, no way to act.

## 4. Decision with alternatives

Raw: the team compared cherry-picking generated HTML with rebuilding it on the target branch and chose rebuilding.

Entry:

> **Generated HTML is rebuilt, not cherry-picked.** Exports embed branch-specific site URL and article IDs; carrying them across versions produces broken links. Cherry-pick source docs, then rebuild.

Home: decision log or architecture note. The log gets a one-line pointer if discoverability is a concern.

## 5. Tool ordering

Raw: native search was tried first, then a browser fallback was added after blocked scrapes.

Entry:

> **Extraction ladder.** Native fetch → static scraper → browser rendering. Escalate only on block pages, non-HTML responses, or content that is thin after conversion.

Home: the owning skill's `SKILL.md` — it changes how the task is executed, so it must load with the skill.

## 6. Stale entry to fix, not delete

Log says category `909` is the default target. Code now defaults to `812`.

Action: propose the correction with evidence (`scripts/clone.py` default), keep the entry until the operator approves the rewrite. Deleting would hide that operators may still remember the old behavior.

## Rewrite patterns

| Weak entry | Why weak | Stronger entry |
| --- | --- | --- |
| "Fixed deploy." | No symptom, no fix | "Deploy fails when `.env` has a trailing space after the key name; the loader keeps it in the value and auth breaks. Trim values in `.env`." |
| "Use `--legacy-peer-deps`." | Missing context | "`npm ci` fails on peer conflicts in the docs theme; use `npm install --legacy-peer-deps` only for the theme package, not the app workspace." |
| "Updated the map." | Unactionable | "New KB links require an entry in `hyperlinks_mkdocs_to_kb_map.md` before the anchor is used, otherwise the build warns `Could not find cross-reference target`." |
| "Long story about the outage." | Diary | "Postgres pool exhausted at 100 connections under 4 workers; cap workers at 3 or raise `max_connections` before enabling the fourth." |

## What not to write

- "Remember to be careful with migrations." — no executable action.
- "Token is `ghp_...`." — a secret; rotate it and describe the mechanism instead.
- "Works on my machine." — no reproducible condition.
- A copy of the commit message — git already carries it.
