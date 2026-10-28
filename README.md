# Self-Evolution Skill

[![Status](https://img.shields.io/badge/status-ready-green.svg)](https://github.com/arterm-sedov/self-evolution-skill/issues)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`self-evolution` turns the end of a working session into durable project memory. It routes each discovery to one home — a skill, a rule, a reference, or a decision log — and keeps a newest-first discovery journal as a staging area that is pruned only with operator approval.

## Why this skill

AI agents forget everything between sessions. The same debugging cycle, environment quirk, or silent failure gets rediscovered weeks later, in a different session, by a different operator. The usual fixes fail in opposite directions: ad-hoc notes turn into an unread diary, and no notes at all guarantee a repeat.

`self-evolution` treats documentation as a routing problem instead of a writing problem:

| Approach | Newest-first | Routing rules | Approval-gated pruning | Bloat detection | Dependencies |
| --- | --- | --- | --- | --- | --- |
| `self-evolution` | Yes | Yes | Yes | Yes | None |
| Ad-hoc notes | No | No | No | No | None |
| CHANGELOG | No | Release-only | N/A | No | None |
| ADR directory | No | Decisions only | N/A | No | None |
| Agent memory file | Depends | No | No | No | None |

## The loop

| Phase | Action |
| --- | --- |
| Before work | Read the newest log entries for the domain you are about to touch |
| During work | Note symptom, cause, and fix while they are fresh |
| After work | Classify each finding and route it to exactly one home |
| Periodically | Summarize, refresh, supersede, and prune the log; apply only after approval |

## Routing

| Finding | Destination |
| --- | --- |
| Workflow gap or repeatable procedure | Skill `SKILL.md` or its `references/` |
| Rule that must always hold | Project rules file (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, …) |
| IDs, endpoints, naming, API quirks | Skill `references/` or `docs/` |
| Decision with rationale | ADR or decision log |
| Unclassified session discovery | Discovery log |

A finding is worth recording when it cost more than one attempt, contradicts the docs, will recur, or changed a decision. Everything else is noise.

## Usage

Copy `skills/self-evolution/` into a supported Agent Skills directory. The host discovers the skill through `SKILL.md`; the helper script is optional. For the host matrix, Claude Code bridge, and Windows junction vs POSIX symlink guidance, see [docs/installation.md](docs/installation.md).

```bash
python skills/self-evolution/scripts/log_health.py skills/self-evolution/references/discovery_log.md
python skills/self-evolution/scripts/log_health.py <log-path> --json
python skills/self-evolution/scripts/log_health.py <log-path> --max-age-days 90
```

The checker reports structural errors (bad dates, duplicate day headings, newest-first violations), stale blocks, size-budget overruns, near-duplicate bullets, overlong entries, absolute paths, credential-like strings, and entries still marked `[superseded by …]` that await an approved purge. It never edits the log.

Run the tests with the standard library only:

```bash
python -m unittest discover -s tests -v
```

## Repository layout

```text
skills/self-evolution/
├── SKILL.md                          # workflow and routing rules
├── references/
│   ├── adapters.md                   # rules file and discovery-log placement
│   ├── discovery-log-format.md       # format, ordering, refresh, pruning rubric
│   ├── discovery_log.md              # starter log for a project
│   └── examples.md                   # worked good/bad entries
└── scripts/
    └── log_health.py                 # validator and health report
docs/
├── installation.md                   # host roots, links, copy mode
└── research/                         # evidence behind the adapter guidance
tests/
└── test_log_health.py
evals/
└── evals.json                        # future evaluation prompts
```

## Quality bar

After documenting, a fresh session should be able to act on the entry without asking a question. If it cannot, the entry is a diary line, not knowledge.

## Adjacent skills

- [human-search-skill](https://github.com/arterm-sedov/human-search-skill) — web discovery and extraction
- [meeting-minutes-skill](https://github.com/arterm-sedov/meeting-minutes-skill) — evidence-grounded meeting records
- [doc-restructure-skill](https://github.com/arterm-sedov/doc-restructure-skill) — deterministic Markdown restructuring
- [browser-switch-skill](https://github.com/arterm-sedov/browser-switch-skill) — choosing a browser automation route
- [cmw-kb-skills](https://github.com/arterm-sedov/cmw-kb-skills) — Comindware knowledge base workflows

## License

MIT — see [LICENSE](LICENSE).
