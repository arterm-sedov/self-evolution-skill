# Discovery log format

The log is a compact journal of session knowledge that has not yet earned a permanent home. It is read by agents under context pressure, so structure matters more than prose. It is also a staging area: without periodic refresh it turns into a graveyard of stale facts.

## File skeleton

```markdown
# Discovery log

Durable session knowledge for <project>. Newest first: agents read from the top and may stop early.

## 2026-06-22

- **Short topic.** Symptom → cause → fix. Exact command, flag, or ID.
- **Another topic.** One or two lines.

## 2026-06-20

- **Topic.** Entry text.
```

Rules:

- One `## YYYY-MM-DD` heading per calendar day. Add new bullets under today's heading; never create a second heading for the same date.
- Newest date block directly below the intro. A new day prepends above the previous one.
- One bullet per finding. A bullet may carry a bold topic label, but the actionable text comes first.
- 1–2 lines per entry. Split a long incident into separate findings rather than writing a paragraph.

## What belongs in an entry

| Element | Required | Example |
| --- | --- | --- |
| Symptom | Yes | build fails with `UnicodeEncodeError` |
| Cause | When non-obvious | colorama encodes Material progress output |
| Fix | Yes | set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` |
| Exact strings | When applicable | flag, command, error text, category ID |
| Pointer to proof | Optional | link to the file, script, or doc that confirms it |

The fresh-session test is the bar: a reader with no memory of the task can apply the entry without asking a question.

## Ordering and merging

- Compare dates, not block position, when in doubt. Newest date first.
- If a stale block sits above a newer one, move it rather than duplicating it.
- When merging two branches, keep both sides' bullets inside the matching date block and re-sort the headings.
- Do not rewrite history inside old blocks silently. Add a correction entry with the current date and a reference to the old one.

## Pruning rubric

| Status | Meaning | Action |
| --- | --- | --- |
| Migrate | Valuable, wrong home | Add the fact to a skill, rule, or doc; then remove from the log |
| Prune | Fully absorbed or redundant | Delete after the durable home exists |
| Keep | Operational detail or best agent entry point | Leave in the log |
| Supersede | New fact overrides an old one | Add the new entry, mark the old one, then remove the old one after approval |
| Fix | Stale or incorrect | Propose corrected wording; do not delete silently |

Before proposing a change, verify the fact's current truth against the code, configuration, or scripts. The repository may have changed since the entry was written.

## Periodic summarization, refresh, and purge

The log decays in three ways: it grows, facts go stale, and newer facts contradict older ones. A refresh pass addresses all three.

### Cadence

Run a refresh:

- monthly, by default;
- when the log exceeds the size budget below;
- before a release or a large refactor;
- when the same fact appears in three or more entries;
- when a session starts by reading a fact that is no longer true.

The operator may choose a different cadence. Record the choice in the rules file wiring block; do not assume the default.

### Operations

| Operation | What changes | Approval |
| --- | --- | --- |
| Summarize | Merge related bullets into one durable entry or skill rule, preserving exact strings and the newest date | Required before deleting the originals |
| Refresh | Verify each fact against the current code; mark wrong facts Fix, not Keep | Required before rewriting |
| Supersede | Replace an overridden fact with a new one and mark the old one | Required before removing the old entry |
| Purge | Remove absorbed, superseded, or redundant entries | Required always |
| Migrate | Move a fact to a skill, rule, or doc and remove it from the log | Required before removal |

Summarization is not permission to blur. Keep the exact command, flag, error text, or ID that makes the entry actionable. If two entries conflict and the current truth is unknown, keep both, label the conflict `[conflict — verify]`, and ask the operator which fact is current. Never guess.

### Supersession format

When a new fact overrides an old one, the new entry names the old date and gist:

```markdown
- **Publish timeout raised.** Full import now takes 12–15 minutes after the corpus grew; use a 900000 ms timeout. Supersedes 2026-06-18: full import takes 5–10 minutes.
```

After approval, mark the old entry so a reader cannot act on it:

```markdown
- **Full import takes 5–10 minutes.** [superseded by 2026-07-02]
```

Then remove the old entry in the same approved pass or in the next purge. Two unmarked contradictory facts are worse than either one alone.

### Confirmation protocol

Present the proposal before changing the file:

| Entry (date + gist) | Status | Proposed action | Destination / evidence |
| --- | --- | --- | --- |
| 2026-06-18 · import timeout 5–10 min | Supersede | Replace with 12–15 min; mark old; remove after approval | `scripts/import.py` timeout constant |
| 2026-06-09 · category `909` | Migrate | Move to cloning skill; remove from log | `scripts/clone.py` default `--target-category-id 909` |
| 2026-06-20 · commit `#6`/`#5` convention | Keep | No change | Convention still in use |

Then ask explicitly: “Apply these summarization, supersession, and purge changes?” Wait for a yes or no. Apply only the approved rows. If approval is partial, leave the rest untouched.

Why approval is mandatory: the operator owns the conventions, knows which branches are shared, and may deliberately keep a reminder even when a durable doc also covers it. Silent deletion destroys trust in the log faster than a stale entry does.

### Archive before destructive purge

If the repository does not track the log in Git, copy it to `references/discovery_log_archive_YYYY-MM.md` before removing entries. If Git tracks it, the history is the archive; say so in the proposal instead of creating a second file.

## Size budget

A healthy log is small. Treat these as signals to schedule a refresh:

- more than ~150 bullets (the checker's default `--max-entries`);
- blocks older than six months with no migration;
- three or more bullets about the same workflow;
- repeated commands that could live in one skill or script;
- entries marked `[superseded by …]` that were never removed.

The checker reports these signals but never edits the log.

## Conflict handling

```markdown
<<<<<<< HEAD
## 2026-06-22
- **A.** ...
=======
## 2026-06-22
- **B.** ...
>>>>>>> feature-branch
```

Resolution: one `## 2026-06-22` heading, both bullets under it, order by importance rather than alphabet. Losing the other branch's discovery is a correctness bug, not a formatting choice.

## Checker reference

`python scripts/log_health.py <log-path>` reports:

- invalid or duplicate date headings;
- newest-first violations;
- entries older than `--max-age-days` (default 180);
- entry count above `--max-entries` (default 150);
- near-duplicate bullets above `--duplicate-threshold` (default 0.65 Jaccard similarity);
- bullets longer than 500 characters;
- absolute paths (`C:\`, `/home/`, `/Users/`, `~`, UNC shares);
- credential-like `key = value` patterns;
- entries still carrying a `[superseded by …]` marker, which are purge candidates.

Exit code `1` means at least one structural error; warnings alone exit `0`. `--json` emits the same report for tooling.
