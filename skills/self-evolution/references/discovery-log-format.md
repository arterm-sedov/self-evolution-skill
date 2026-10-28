# Discovery log format

The log is a compact journal of session knowledge that has not yet earned a permanent home. It is read by agents under context pressure, so structure matters more than prose.

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
- Do not rewrite history inside old blocks; add a correction bullet with the current date and a reference to the old one.

## Pruning rubric

| Status | Meaning | Action |
| --- | --- | --- |
| Migrate | Valuable, wrong home | Add the fact to a skill, rule, or doc; then remove from the log |
| Prune | Fully absorbed or redundant | Delete after the durable home exists |
| Keep | Operational detail or best agent entry point | Leave in the log |
| Fix | Stale or incorrect | Propose corrected wording; do not delete silently |

Before proposing a change, verify the fact's current truth against the code, configuration, or scripts — the repository may have changed since the entry was written.

## Size budget

A healthy log is small. Treat these as signals to schedule a cleanup:

- more than ~150 bullets;
- blocks older than six months with no migration;
- three or more bullets about the same workflow;
- repeated commands that could live in one skill or script.

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
- near-duplicate bullets above `--duplicate-threshold` (default 0.65 Jaccard similarity);
- bullets longer than 500 characters;
- absolute paths (`C:\`, `/home/`, `/Users/`, `~`, UNC shares);
- credential-like `key = value` patterns.

Exit code `1` means at least one structural error; warnings alone exit `0`. `--json` emits the same report for tooling.
