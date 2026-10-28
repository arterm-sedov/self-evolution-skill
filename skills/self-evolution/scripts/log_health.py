#!/usr/bin/env python3
"""Health check for a newest-first discovery log.

Validates structure, reports stale or duplicated entries, and flags content
that should not be committed. Standard library only, so it runs wherever the
skill is installed with Python 3.10 or newer.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

DATE_HEADING = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2})\s*$")
BULLET = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")

# Machine-specific locations that should never reach a shared log.
ABSOLUTE_PATH = re.compile(
    r"(?:^|[\s(\"'])("
    r"[A-Za-z]:\\"
    r"|/home/"
    r"|/Users/"
    r"|~/"
    r"|\\\\[A-Za-z0-9_.-]+\\"
    r")"
)

# Credential-like assignments: key = value or key: value with a non-trivial value.
SECRET = re.compile(
    r"(?i)\b(api[_-]?key|secret|token|password|passwd|pwd|access[_-]?key)\b"
    r"\s*[:=]\s*[\"']?[A-Za-z0-9_\-./+]{6,}"
)

MAX_ENTRY_CHARS = 500
WORD = re.compile(r"[a-z0-9]{4,}")


@dataclass
class Issue:
    """One finding from the health check."""

    severity: str  # error | warning | info
    code: str
    message: str
    line: int | None = None


@dataclass
class Entry:
    """A single bullet in the log."""

    date: str
    line: int
    text: str


@dataclass
class Report:
    """Full health report for one log file."""

    path: str
    dates: int = 0
    entries: int = 0
    newest: str | None = None
    oldest: str | None = None
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]


def _tokens(text: str) -> set[str]:
    """Normalize a bullet into a set of meaningful tokens."""
    return set(WORD.findall(text.lower()))


def _similarity(left: set[str], right: set[str]) -> float:
    """Jaccard similarity; zero when either side is empty."""
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def parse_log(text: str) -> tuple[list[Entry], list[str], list[Issue]]:
    """Extract entries, date sequence, and structural issues from log text."""
    entries: list[Entry] = []
    dates: list[str] = []
    issues: list[Issue] = []
    seen: dict[str, int] = {}
    current_date: str | None = None

    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        match = DATE_HEADING.match(line)
        if match:
            value = match.group(1)
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                issues.append(
                    Issue("error", "invalid-date", f"invalid date heading: {value}", number)
                )
                current_date = None
                continue

            if value in seen:
                issues.append(
                    Issue(
                        "error",
                        "duplicate-date",
                        f"duplicate date heading {value}; first seen on line {seen[value]}",
                        number,
                    )
                )
            else:
                seen[value] = number
                dates.append(value)
            current_date = value
            continue

        if line.startswith("## "):
            issues.append(
                Issue(
                    "warning",
                    "non-date-heading",
                    f"heading is not a date: {line.strip('# ').strip()}",
                    number,
                )
            )
            current_date = None
            continue

        bullet = BULLET.match(line)
        if bullet and current_date:
            entries.append(Entry(current_date, number, bullet.group(1)))

    for index in range(1, len(dates)):
        if dates[index] > dates[index - 1]:
            issues.append(
                Issue(
                    "error",
                    "order",
                    f"date block {dates[index - 1]} appears above newer block {dates[index]}",
                    seen[dates[index - 1]],
                )
            )

    return entries, dates, issues


def check_content(entries: list[Entry]) -> list[Issue]:
    """Flag entries that are too long, machine-specific, or credential-like."""
    issues: list[Issue] = []
    for entry in entries:
        if len(entry.text) > MAX_ENTRY_CHARS:
            issues.append(
                Issue(
                    "warning",
                    "long-entry",
                    f"entry is {len(entry.text)} characters; split or tighten it",
                    entry.line,
                )
            )
        if ABSOLUTE_PATH.search(entry.text):
            issues.append(
                Issue(
                    "warning",
                    "absolute-path",
                    "entry contains an absolute path; make it repository-relative",
                    entry.line,
                )
            )
        if SECRET.search(entry.text):
            issues.append(
                Issue(
                    "error",
                    "secret",
                    "entry looks like it contains a credential; remove and rotate it",
                    entry.line,
                )
            )
    return issues


def check_staleness(entries: list[Entry], max_age_days: int, today: date | None = None) -> list[Issue]:
    """Warn about old blocks that may deserve migration or pruning."""
    today = today or date.today()
    flagged: set[str] = set()
    issues: list[Issue] = []
    for entry in entries:
        if entry.date in flagged:
            continue
        try:
            block_date = datetime.strptime(entry.date, "%Y-%m-%d").date()
        except ValueError:
            continue
        age = (today - block_date).days
        if age > max_age_days:
            flagged.add(entry.date)
            issues.append(
                Issue(
                    "warning",
                    "stale-block",
                    f"date block {entry.date} is {age} days old; review for migration or pruning",
                    entry.line,
                )
            )
    return issues


def check_duplicates(entries: list[Entry], threshold: float) -> list[Issue]:
    """Find near-duplicate bullets so the log does not repeat itself."""
    issues: list[Issue] = []
    token_sets = [_tokens(entry.text) for entry in entries]
    for index, entry in enumerate(entries):
        for earlier in range(index):
            score = _similarity(token_sets[index], token_sets[earlier])
            if score >= threshold:
                issues.append(
                    Issue(
                        "warning",
                        "near-duplicate",
                        f"similar to line {entries[earlier].line} ({score:.2f})",
                        entry.line,
                    )
                )
                break
    return issues


def build_report(
    path: Path,
    *,
    max_age_days: int = 180,
    duplicate_threshold: float = 0.65,
    today: date | None = None,
) -> Report:
    """Read a log file and produce a full report."""
    text = path.read_text(encoding="utf-8", errors="replace")
    entries, dates, issues = parse_log(text)
    issues.extend(check_content(entries))
    issues.extend(check_staleness(entries, max_age_days, today))
    issues.extend(check_duplicates(entries, duplicate_threshold))
    issues.sort(key=lambda issue: (issue.line or 0, issue.severity))

    return Report(
        path=str(path),
        dates=len(dates),
        entries=len(entries),
        newest=max(dates) if dates else None,
        oldest=min(dates) if dates else None,
        issues=issues,
    )


def render_text(report: Report) -> str:
    """Render a report for humans."""
    lines = [f"Discovery log health: {report.path}"]
    span = ""
    if report.newest and report.oldest:
        span = f", {report.oldest} to {report.newest}"
    lines.append(f"  {report.entries} entries in {report.dates} day blocks{span}")

    errors = report.errors
    warnings = report.warnings
    if errors:
        lines.append("")
        lines.append("Errors:")
        lines.extend(f"  line {issue.line}: {issue.message}" for issue in errors)
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"  line {issue.line}: {issue.message}" for issue in warnings)
    if not errors and not warnings:
        lines.append("")
        lines.append("No issues found.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Check a newest-first discovery log.")
    parser.add_argument("log", type=Path, help="path to discovery_log.md")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=180,
        help="warn about date blocks older than this (default: 180)",
    )
    parser.add_argument(
        "--duplicate-threshold",
        type=float,
        default=0.65,
        help="Jaccard similarity that counts as a duplicate (default: 0.65)",
    )
    args = parser.parse_args(argv)

    if not args.log.is_file():
        print(f"error: log not found: {args.log}", file=sys.stderr)
        return 2

    report = build_report(
        args.log,
        max_age_days=args.max_age_days,
        duplicate_threshold=args.duplicate_threshold,
    )

    if args.json:
        payload = asdict(report)
        payload["errors"] = len(report.errors)
        payload["warnings"] = len(report.warnings)
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
