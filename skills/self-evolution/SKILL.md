---
name: self-evolution
description: Capture what a session learned so the next session starts smarter, and keep that knowledge current. Use after any non-trivial task — debugging, integration, migration, refactor, tooling fix — to route discoveries, gotchas, and decisions into durable project memory; also use before starting similar work to review what earlier sessions already learned, and periodically to summarize, refresh, supersede, and purge the discovery log with operator approval. Trigger when the user says document what we learned, add to the discovery log, write this down for next time, update the skill or rules, clean up stale notes, or asks why a previous decision was made.
license: MIT
metadata:
  compatibility: Any Agent Skills host that can read and write files. The optional log-health script needs Python 3.10+ and uses only the standard library.
---

# Self-evolution

Agents forget between sessions; repositories should not. A non-trivial task usually produces two or three facts that were expensive to discover and cheap to store. The danger is symmetric: record nothing and the next session repeats the debugging; record everything and the notes become an unread diary.

Treat session knowledge as a routing problem. Every finding gets exactly one durable home, the discovery log stays a staging area rather than an archive, and nothing is deleted without the operator's approval.

## Run the loop

| Phase | Action |
| --- | --- |
| Before work | Read the newest log entries that touch the area |
| During work | Note the symptom, cause, and fix while they are fresh |
| After work | Classify each finding and route it to one home |
| Periodically | Summarize, refresh, supersede, and prune the log; apply only after approval |

### Before starting

Read the discovery log from the top. Entries are newest-first, so a partial or truncated read still sees the most recent gotchas. Search it for the domain you are about to touch: tool names, file paths, service names, error text.

Most costly mistakes are domain-specific and will not surface through generic code search. A two-minute review regularly saves a repeated debugging cycle.

If the project has no log yet, copy `references/discovery_log.md` to the chosen location and record the wiring described in [references/adapters.md](references/adapters.md). Do this once per repository, not once per session.

### After finishing

Apply the 30-second test. Record a finding when at least one is true:

- it cost more than one attempt, build, or debugging cycle;
- it contradicts the documentation or intuition;
- it will recur — same repository, stack, service, or operator workflow;
- it changed a decision (tool, ordering, path, permission).

Do not record transient state, one-off typos, secrets, absolute machine paths, or anything already stated in durable docs. If the finding is already written down, improve that text instead of adding a second copy.

## Route each finding to one home

| Finding | Destination | Why there |
| --- | --- | --- |
| Workflow gap or repeatable multi-step procedure | A skill: `SKILL.md` or its `references/` | Loaded only when relevant; executable instructions live next to the tools |
| Rule that must hold on every task | Project rules file (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules`, `CONTRIBUTING.md`) | Always in context; keep it short and imperative |
| Reference detail: IDs, endpoints, naming, API quirks | `references/` of the owning skill, or `docs/` | Too detailed for rules, too stable for the log |
| Decision with rationale and alternatives | Architecture decision record or decision log, when the repository keeps one | Future readers need the why, not only the what |
| Session-level discovery, not yet classified | Discovery log | Cheap capture now; migrate once it proves useful |

Prefer extending an existing skill or rule over creating a new file. Two half-relevant documents are harder to use than one accurate one.

## Write an entry people can act on

Format: one bullet, `symptom → cause → fix`, one or two lines. Include the exact string that matters: command, flag, error text, ID, file name.

Why newest-first: agents read the file under context pressure; the most recent lessons must survive truncation. Keep one `## YYYY-MM-DD` heading per day and merge new bullets into today's block instead of adding a second heading for the same date.

A good entry passes the fresh-session test: someone with no memory of the task can apply it without asking a question.

Bad: "Fixed the build issue with the env var."

Good: "`mkdocs build` crashes on Windows with a colorama `UnicodeEncodeError` on Material progress output unless `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` are set. Set both in the shell profile, not per command."

Bad: "Examples category is 909."

Good: "Clone new example articles into category `909` with `--target-category-id 909`; the default target drops them into the wrong subtree and published links break."

## Prune with approval, never alone

The log is a staging area. Entries that proved useful across sessions belong in a skill or rule; entries already covered by durable docs can leave.

1. Read the log newest-first.
2. For each bullet, check whether the fact already lives in the rules file, skill files, README, or the code itself.
3. Classify it:

    - **Migrate** — still valuable, wrong home; name the destination and the one-line rule to add there.
    - **Prune** — absorbed or redundant; safe to delete once the durable home exists.
    - **Keep** — operational detail, not documented elsewhere, or still the best entry point for agents.
    - **Supersede** — a newer fact overrides it; add the new entry, mark the old one, then remove it after approval.
    - **Fix** — stale or wrong; propose corrected wording instead of deleting.

4. Present a short table: entry (date + gist) → status → proposed action → destination.
5. Ask explicitly whether to apply the proposal. Apply only what was approved.

Why approval: the operator owns the conventions, knows which branches are shared, and may deliberately keep a reminder in the log even when a rule also covers it. Silent deletion destroys trust in the log faster than a stale entry does.

### Refresh before it rots

Pruning alone leaves stale facts in place. Run a refresh pass monthly, before a release, after a large refactor, and whenever the checker reports size or staleness:

1. **Summarize** clusters of related bullets into one durable entry or skill rule. Keep the exact command, flag, error text, or ID; a summary that loses the actionable string is worse than the original.
2. **Verify** every fact against the current code, configuration, or vendor documentation. A fact that no longer holds is Fix or Supersede, never Keep.
3. **Supersede** when a new fact contradicts an old one. The new entry says `Supersedes YYYY-MM-DD: <old gist>`; after approval the old entry is marked `[superseded by YYYY-MM-DD]` and then removed. Never leave two unmarked contradictory facts.
4. **Purge** absorbed, superseded, or redundant entries only after the operator approves the table.
5. **Archive** before destructive purge when the log is not tracked in Git.

If two entries conflict and the current truth is unknown, keep both, label the conflict `[conflict — verify]`, and ask which fact is current. Guessing is how a log starts lying.

## Detect bloat and propose a skill

During delta analysis, watch for clusters: several bullets describing one workflow, repeated command blocks, or a rules file turning into a cookbook. Rules files should stay short; long playbooks belong in skills that load only when relevant.

When a cluster appears, propose a skill: name, one-line description, which entries move out, and which file shrinks. Do not create the skill until the operator agrees — they know ownership, naming, and whether an existing skill should absorb the material instead.

## Keep the log healthy

Run the bundled checker before and after a cleanup pass:

```bash
python scripts/log_health.py skills/self-evolution/references/discovery_log.md
python scripts/log_health.py <log-path> --json
python scripts/log_health.py <log-path> --max-age-days 90 --max-entries 100
```

It reports structural errors (bad dates, duplicate day headings, newest-first violations), stale blocks, size-budget overruns, near-duplicate bullets, overlong entries, absolute paths, credential-like strings, and entries still marked `[superseded by …]` that are waiting for an approved purge. Use `--json` when another tool consumes the result.

## Handoff and sync

When the findings live on a feature branch, mention it and ask whether the rules, skill, and log commit should be propagated to other maintained branches. Do not cherry-pick or push on your own: the operator knows which branches are shared and which artifacts are version-specific.

## Adapters

Hosts keep project instructions in different files. See [references/adapters.md](references/adapters.md) for the rules file to update and the discovery-log location. Skill installation across hosts is out of scope for the workflow; see `docs/installation.md` in the repository when you need to place the skill itself.

## Reference files

- [references/adapters.md](references/adapters.md) — rules file and discovery-log placement.
- [references/discovery-log-format.md](references/discovery-log-format.md) — exact log format, ordering, refresh, conflict handling, pruning rubric.
- [references/examples.md](references/examples.md) — worked entries across domains with good and bad rewrites.
- [references/discovery_log.md](references/discovery_log.md) — starter log to copy into a project.
- `scripts/log_health.py` — validator and health report.

## Anti-patterns

- Diary log: a narrative of what happened with no actionable fact.
- Duplicate truth: the same rule in the log, the rules file, and two skills.
- Silent pruning.
- Secrets, tokens, customer names, or absolute paths in entries.
- Creating a skill for a single session's convenience.
- Recording what git already tells you (commit message, diff).
- Running the full ritual after a one-line change; the 30-second test decides.
