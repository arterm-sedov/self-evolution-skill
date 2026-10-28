"""Tests for the discovery-log health checker."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "self-evolution" / "scripts"))

from log_health import build_report, main, parse_log  # noqa: E402


def codes(issues):
    return [issue.code for issue in issues]


class ParseTests(unittest.TestCase):
    def test_reads_entries_and_dates(self):
        text = "# Log\n\n## 2026-06-20\n\n- first\n- second\n\n## 2026-06-18\n\n- third\n"
        entries, dates, issues = parse_log(text)
        self.assertEqual(dates, ["2026-06-20", "2026-06-18"])
        self.assertEqual(len(entries), 3)
        self.assertEqual(entries[0].date, "2026-06-20")
        self.assertEqual(codes(issues), [])

    def test_bullets_outside_date_blocks_are_ignored(self):
        text = "# Log\n\n- intro bullet\n\n## 2026-06-20\n\n- real\n"
        entries, _, _ = parse_log(text)
        self.assertEqual([entry.text for entry in entries], ["real"])

    def test_order_violation_is_an_error(self):
        text = "## 2026-06-18\n\n- old\n\n## 2026-06-20\n\n- new\n"
        _, _, issues = parse_log(text)
        self.assertIn("order", codes(issues))

    def test_duplicate_date_is_an_error(self):
        text = "## 2026-06-20\n\n- a\n\n## 2026-06-20\n\n- b\n"
        _, _, issues = parse_log(text)
        self.assertIn("duplicate-date", codes(issues))

    def test_invalid_date_is_an_error(self):
        text = "## 2026-13-40\n\n- a\n"
        _, _, issues = parse_log(text)
        self.assertIn("invalid-date", codes(issues))


class ContentTests(unittest.TestCase):
    def test_flags_absolute_paths_and_secrets(self):
        text = (
            "## 2026-06-20\n\n"
            "- Build runs from C:\\Users\\dev\\repo.\n"
            "- Set api_key = sk_live_123456789 before deploy.\n"
        )
        entries, _, _ = parse_log(text)
        report_issues = []
        from log_health import check_content

        report_issues.extend(check_content(entries))
        found = codes(report_issues)
        self.assertIn("absolute-path", found)
        self.assertIn("secret", found)

    def test_flags_long_entries(self):
        text = "## 2026-06-20\n\n- " + ("word " * 200) + "\n"
        entries, _, _ = parse_log(text)
        from log_health import check_content

        self.assertIn("long-entry", codes(check_content(entries)))

    def test_ignores_clean_entries(self):
        text = "## 2026-06-20\n\n- Set PYTHONUTF8=1 to fix the build.\n"
        entries, _, _ = parse_log(text)
        from log_health import check_content

        self.assertEqual(check_content(entries), [])

    def test_flags_superseded_entries(self):
        text = "## 2026-06-20\n\n- Old fact. [superseded by 2026-07-02]\n"
        entries, _, _ = parse_log(text)
        from log_health import check_content

        self.assertIn("superseded-entry", codes(check_content(entries)))


class SizeTests(unittest.TestCase):
    def test_size_budget_uses_entry_count(self):
        text = "## 2026-06-20\n\n- one\n- two\n- three\n"
        entries, _, _ = parse_log(text)
        from log_health import check_size

        self.assertEqual(len(check_size(entries, 3)), 0)
        self.assertIn("size-budget", codes(check_size(entries, 2)))


class DuplicateTests(unittest.TestCase):
    def test_near_duplicates_are_reported(self):
        text = (
            "## 2026-06-20\n\n"
            "- Build crashes with colorama UnicodeEncodeError on Windows; set PYTHONUTF8 and PYTHONIOENCODING.\n"
            "- Build crashes with colorama UnicodeEncodeError on Windows; set PYTHONUTF8 and PYTHONIOENCODING now.\n"
        )
        entries, _, _ = parse_log(text)
        from log_health import check_duplicates

        self.assertIn("near-duplicate", codes(check_duplicates(entries, 0.65)))

    def test_distinct_entries_pass(self):
        text = "## 2026-06-20\n\n- First finding about database pools.\n- Second finding about browser caching.\n"
        entries, _, _ = parse_log(text)
        from log_health import check_duplicates

        self.assertEqual(check_duplicates(entries, 0.65), [])


class StalenessTests(unittest.TestCase):
    def test_old_blocks_are_flagged(self):
        text = "## 2025-01-01\n\n- ancient\n"
        entries, _, _ = parse_log(text)
        from log_health import check_staleness

        issues = check_staleness(entries, 180, today=date(2026, 6, 20))
        self.assertIn("stale-block", codes(issues))

    def test_recent_blocks_pass(self):
        text = "## 2026-06-18\n\n- recent\n"
        entries, _, _ = parse_log(text)
        from log_health import check_staleness

        self.assertEqual(check_staleness(entries, 180, today=date(2026, 6, 20)), [])


class ReportTests(unittest.TestCase):
    def test_build_report_summarizes_span(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.md"
            path.write_text("# Log\n\n## 2026-06-20\n\n- a\n\n## 2026-06-18\n\n- b\n", encoding="utf-8")
            report = build_report(path, today=date(2026, 6, 20))
            self.assertEqual(report.entries, 2)
            self.assertEqual(report.dates, 2)
            self.assertEqual(report.newest, "2026-06-20")
            self.assertEqual(report.oldest, "2026-06-18")

    def test_json_cli_exit_codes(self):
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp) / "clean.md"
            clean.write_text("## 2026-06-20\n\n- a\n", encoding="utf-8")
            broken = Path(tmp) / "broken.md"
            broken.write_text("## 2026-06-18\n\n- a\n\n## 2026-06-20\n\n- b\n", encoding="utf-8")

            buffer = io.StringIO()
            with redirect_stdout(buffer):
                self.assertEqual(main([str(clean), "--json"]), 0)
                self.assertEqual(main([str(broken), "--json"]), 1)

    def test_json_payload_shape(self):
        import io
        from contextlib import redirect_stdout

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "log.md"
            path.write_text("## 2026-06-20\n\n- a\n", encoding="utf-8")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                self.assertEqual(main([str(path), "--json"]), 0)
            payload = json.loads(buffer.getvalue())
            self.assertIn("issues", payload)
            self.assertEqual(payload["entries"], 1)
            self.assertEqual(payload["errors"], 0)
            self.assertEqual(payload["warnings"], 0)

    def test_size_warning_renders_without_line_number(self):
        from log_health import Issue, Report, render_text

        report = Report(path="log.md", dates=1, entries=200)
        report.issues.append(Issue("warning", "size-budget", "too many entries"))
        rendered = render_text(report)
        self.assertIn("too many entries", rendered)
        self.assertNotIn("line None", rendered)


if __name__ == "__main__":
    unittest.main()
