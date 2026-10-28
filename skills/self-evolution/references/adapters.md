# Adapters — placing the skill in a host project

The methodology is host-neutral; the file names are not. Pick one rules file and one log location, record the choice, and keep it stable. Drift between three half-maintained copies is worse than no documentation.

## Project rules file per host

| Host | Always-on project rules | Skill location |
| --- | --- | --- |
| Claude Code | `CLAUDE.md` (or `.claude/CLAUDE.md`) | `.claude/skills/<name>/SKILL.md` |
| OpenCode | `AGENTS.md` | `.opencode/skills/` or `.agents/skills/<name>/SKILL.md` |
| Codex | `AGENTS.md` | `AGENTS.md` skill conventions of the host |
| Cursor | `.cursor/rules/*.mdc` | `.cursor/rules/` or project skills |
| GitHub Copilot | `.github/copilot-instructions.md` | host-dependent |
| Generic repository | `AGENTS.md` or `CONTRIBUTING.md` | `skills/<name>/SKILL.md` |

If the repository already has an always-on rules file, extend it. Do not introduce a second one that agents may or may not load.

## Choose the discovery log location

| Situation | Recommended location | Trade-off |
| --- | --- | --- |
| Project skill travels with the repository | `.agents/skills/self-evolution/references/discovery_log.md` | Nearest to the workflow; moves with the skill |
| Log shared by humans and several tools | `docs/discovery-log.md` | Easy to link from README and PR templates |
| Multiple repositories, one operator | Personal skill directory | Never commit machine-specific paths |

Keep one log per repository. In a monorepo, add a package column or a `## <package>` subheading only when independent teams genuinely need separate timelines; otherwise a single newest-first log stays searchable.

## Record the wiring

Add a short block to the rules file so future sessions do not guess:

```markdown
## Self-evolution wiring

- Discovery log: `docs/discovery-log.md` (newest first, one date heading per day)
- Rules file: this file
- Skills: `skills/<name>/SKILL.md`
- Pruning requires operator approval.
```

Why: a copied skill usually retains the reference paths from its original repository. One wiring block prevents a session from writing into a stale path.

## Shared branches and generated artifacts

Rules, skill files, and prose documentation are usually portable across branches. Generated artifacts — build output, imported snapshots, RAG corpora, LLM bundles, version-specific IDs — are not: they embed branch names, site URLs, and database identifiers.

When documenting on a feature branch, separate the advice commit from generated output and ask before propagating. Advise; never cherry-pick or push automatically.

## Multi-agent teams

- One log file, newest-first, with one date heading per day.
- On merge conflict, keep both date blocks and re-sort; do not discard the other session's findings.
- Attribute ownership through the repository's normal review flow, not by prefixing entries with an agent name.
- If two agents document the same fact, keep the clearer wording and merge the exact strings from both.
