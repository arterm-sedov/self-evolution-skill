# Adapters — where the log and rules live

The workflow needs two stable locations: the always-on rules file that receives recurring findings, and the discovery log. This file names them. Skill installation across hosts — skill directories, links, copy mode — is a separate concern; see `docs/installation.md` in the repository.

## Rules file

| Host | File to update | Notes |
| --- | --- | --- |
| Any host | `AGENTS.md` | Shared default; read by Codex, Cursor, OpenCode, Copilot, and Claude Code when no `CLAUDE.md` is present |
| Claude Code | `CLAUDE.md` | Optional; wins over `AGENTS.md`. To load both, import `@AGENTS.md` or set Project instructions to `claude-md-and-agents-md` |
| Cursor | `.cursor/rules/*.mdc` | For path-scoped or Cursor-only rules; `AGENTS.md` still works |
| GitHub Copilot | `.github/copilot-instructions.md` | Keep consistent with `AGENTS.md` |
| OpenCode | `AGENTS.md` | Rules can also live in OpenCode configuration |

Pick the file the host actually reads. A rule written into a file the host ignores is worse than no rule. Keep one source of truth; do not copy the same rule into three files.

## Discovery log

Default: `docs/discovery-log.md`.

| Situation | Location |
| --- | --- |
| Normal project | `docs/discovery-log.md` |
| Skill vendored into the repository | `.agents/skills/self-evolution/references/discovery_log.md` |
| Personal notes across repositories | user-scope skill directory; never commit machine paths |

Copy the starter from the skill's `references/discovery_log.md`, then record the choice.

## Record the wiring

Add this to the rules file:

```markdown
## Self-evolution wiring

- Discovery log: `docs/discovery-log.md` (newest first)
- Rules file: `AGENTS.md`
- Refresh cadence: monthly; summarize, verify, supersede, prune with approval
- Pruning requires operator approval.
```

## Branch sync

Rules and skill files usually cherry-pick cleanly; generated artifacts do not. When findings live on a feature branch, ask whether to propagate the documentation commit. Do not cherry-pick or push on your own.

## See also

- `docs/installation.md` — skill directories per host, junction vs symlink, bootstrap scripts
- `docs/research/Adapters_Compatibility_Research_20261028/` — evidence and version notes
