import unittest
import json
import tempfile
import os
import datetime
from unittest.mock import patch
from click.testing import CliRunner
from collections import defaultdict

USER_PROVIDED_JSON_MAY_2025_STR = """
{
  "congregation": {"id": 28341, "name": "East Karenberg Area Congregation (#744)", "locales_id": 37, "timezones_id": 95, "countries_id": 58, "jworg_langcode": "FR", "locale": {"id": 37, "code": "fr", "name": "French", "symbol": "FR"}},
  "publishers": [{"id": 1000001, "reportstobranch": false, "firstname": "Michael", "lastname": "Edwards"}, {"id": 1000002, "reportstobranch": false, "firstname": "Brenda", "lastname": "Moore"}, {"id": 1000003, "reportstobranch": false, "firstname": "Anna", "lastname": "Bishop"}, {"id": 1000004, "reportstobranch": false, "firstname": "Gail", "lastname": "Jones"}, {"id": 1000005, "reportstobranch": false, "firstname": "Dawn", "lastname": "Berry"}, {"id": 1000008, "reportstobranch": false, "firstname": "Kaitlin", "lastname": "Todd"}, {"id": 1000009, "reportstobranch": true, "firstname": "Troy", "lastname": "Bush"}, {"id": 1000010, "reportstobranch": true, "firstname": "Kiara", "lastname": "Cross"}, {"id": 1000006, "firstname": "Alicia", "lastname": "Fitzgerald", "reportstobranch": false}, {"id": 1000007, "firstname": "Sierra", "lastname": "Johnson", "reportstobranch": false}],
  "reports": [
    {"user": {"id": 1000001}, "month": 5, "year": 2025, "minutes": 2340, "pioneer": "Regular", "studies": 6, "has_reported_field_service": true},
    {"user": {"id": 1000002}, "month": 5, "year": 2025, "minutes": 3300, "pioneer": "Regular", "studies": 6, "has_reported_field_service": true},
    {"user": {"id": 1000003}, "month": 5, "year": 2025, "minutes": 3840, "pioneer": "Regular", "studies": 4, "has_reported_field_service": true},
    {"user": {"id": 1000004}, "month": 5, "year": 2025, "minutes": 3960, "pioneer": "Regular", "studies": 5, "has_reported_field_service": true},
    {"user": {"id": 1000005}, "month": 5, "year": 2025, "minutes": 3600, "pioneer": "Regular", "studies": 8, "has_reported_field_service": true},
    {"user": {"id": 1000008}, "month": 5, "year": 2025, "minutes": 3000, "pioneer": "Regular", "studies": 3, "has_reported_field_service": true},
    {"user": {"id": 1000009}, "month": 5, "year": 2025, "minutes": 1, "pioneer": null, "studies": 15, "has_reported_field_service": true},
    {"user": {"id": 1000010}, "month": 5, "year": 2025, "minutes": 1, "pioneer": null, "studies": 14, "has_reported_field_service": true},
    {"user": {"id": 1000009}, "year": 2024, "month": 12, "minutes": 1, "studies": 0, "has_reported_field_service": true, "pioneer": "Special"},
    {"user": {"id": 1000010}, "year": 2025, "month": 1, "minutes": 1, "studies": 0, "has_reported_field_service": true, "pioneer": "Special"},
    {"user": {"id": 1000001}, "year": 2025, "month": 2, "minutes": 1, "studies": 0, "has_reported_field_service": true, "pioneer": "Regular"},
    {"user": {"id": 1000002}, "year": 2025, "month": 3, "minutes": 1, "studies": 0, "has_reported_field_service": true, "pioneer": "Regular"},
    {"user": {"id": 1000006}, "year": 2025, "month": 4, "minutes": 1, "studies": 0, "has_reported_field_service": true, "pioneer": null},
    {"user": {"id": 1000007}, "year": 2024, "month": 12, "minutes": 1, "studies": 0, "has_reported_field_service": true, "pioneer": null}
  ],
  "attendance": {"attendance": [{"month": "2025-05", "weAvg": 163}]}
}
"""

MAY_2026_MOCK_DATA_STR = """
{
  "congregation": {"id": 28342, "name": "Default Test Cong", "locale": {"id": 37, "code": "fr", "name": "French"}},
  "publishers": [
    {"id": "rp1", "reportstobranch": false, "firstname": "RP", "lastname": "One"}, {"id": "rp2", "reportstobranch": false, "firstname": "RP", "lastname": "Two"},
    {"id": "ap1", "reportstobranch": false, "firstname": "AP", "lastname": "One"},
    {"id": "pub1", "reportstobranch": false, "firstname": "Pub", "lastname": "One"}, {"id": "pub2", "reportstobranch": false, "firstname": "Pub", "lastname": "Two"}, {"id": "pub3", "reportstobranch": false, "firstname": "Pub", "lastname": "Three"},
    {"id": "sp1", "reportstobranch": true, "firstname": "SP", "lastname": "One"},
    {"id": "inactive1", "firstname": "Inactive", "lastname": "One"}
  ],
  "reports": [
    {"user": {"id": "rp1"}, "year": 2026, "month": 5, "minutes": 3000, "studies": 5, "pioneer": "Regular", "has_reported_field_service": true},
    {"user": {"id": "rp2"}, "year": 2026, "month": 5, "minutes": 3600, "studies": 4, "pioneer": "Regular", "has_reported_field_service": true},
    {"user": {"id": "ap1"}, "year": 2026, "month": 5, "minutes": 1800, "studies": 3, "pioneer": "Auxiliary", "has_reported_field_service": true},
    {"user": {"id": "pub1"}, "year": 2026, "month": 5, "minutes": 600, "studies": 2, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "pub2"}, "year": 2026, "month": 5, "minutes": 0, "studies": 1, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "pub3"}, "year": 2026, "month": 5, "minutes": 300, "studies": 0, "pioneer": null, "has_reported_field_service": true},
    {"user": {"id": "sp1"}, "year": 2026, "month": 5, "minutes": 6000, "studies": 10, "pioneer": "Special", "has_reported_field_service": true}
  ],
  "attendance": {"attendance": [{"month": "2026-05", "weAvg": 100}]}
}
"""

NO_ACTIVITY_JUL_2024_JSON_STR = """
{
  "congregation": {"id": 28344, "name": "No Activity July Cong", "locale": {"id": 37, "code": "fr", "name": "French"}},
  "publishers": [], "reports": [],
  "attendance": {"attendance": [{"month": "2024-07", "weAvg": 0}]}
}
"""

class TestMonthlyActivityReport(unittest.TestCase):
    USER_PROVIDED_JSON_MAY_2025_STR = USER_PROVIDED_JSON_MAY_2025_STR
    MAY_2026_MOCK_DATA_STR = MAY_2026_MOCK_DATA_STR
    NO_ACTIVITY_JUL_2024_JSON_STR = NO_ACTIVITY_JUL_2024_JSON_STR

    def setUp(self):
        self.runner = CliRunner()
        self.maxDiff = None

    def _run_cli_with_data(self, json_data_str, month_arg=None):
        from fsr.cli import cli as fsr_cli

        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding='utf-8') as tmp_json_file:
            tmp_json_file.write(json_data_str)
            tmp_json_file_path = tmp_json_file.name

        args = ['--json-file', tmp_json_file_path, 'summary', 'monthly-activity']
        if month_arg:
            args.extend(['--month', month_arg])

        try:
            result = self.runner.invoke(
                fsr_cli, args, catch_exceptions=False, prog_name="fsr")
        finally:
            os.remove(tmp_json_file_path)
        return result

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_may_2025(self, mock_datetime_summaries):
        """Tests the May 2025 summary with the new French-labeled format and SP logic."""
        mock_datetime_summaries.timedelta = datetime.timedelta
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2025, 6, 15, 10, 0, 0)
        result = self._run_cli_with_data(self.USER_PROVIDED_JSON_MAY_2025_STR, "2025-05")
        
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")

        expected_french_output = """Tous les proclamateurs actifs
10
Assistance moyenne à la réunion de week-end
163

PROCLAMATEURS
Nombre de fiches d’activité (S-4)
0
Cours bibliques
0

PIONNIERS AUXILIAIRES
Nombre de fiches d’activité (S-4)
0
Heures
0.00
Cours bibliques
0

PIONNIERS PERMANENTS
Nombre de fiches d’activité (S-4)
6
Heures
334.00
Cours bibliques
32""".strip()

        actual_report_lines = []
        report_content_started = False
        for line in output.split('\n'):
            if line.strip() == "Tous les proclamateurs actifs": report_content_started = True
            if not report_content_started: continue
            if not (line.startswith("Info:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or \
                    line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                # Keep "Rapò kreye:" for now, or decide to strip it too
                actual_report_lines.append(line)

        # Strip "Rapò kreye:" if present before final comparison
        final_actual_lines = [line for line in actual_report_lines if not line.startswith("Rapò kreye:")]
        actual_report_processed = "\n".join(final_actual_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                         f"Output does not match expected French summary for May 2025.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_default_month(self, mock_datetime_summaries):
        """Tests the default month summary (May 2026) with the new French-labeled format."""
        mock_datetime_summaries.timedelta = datetime.timedelta
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2026, 6, 15, 10, 0, 0)
        expected_month_str = "2026-05"
        result = self._run_cli_with_data(self.MAY_2026_MOCK_DATA_STR)

        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")
        self.assertIn(f"Info: --month not provided, defaulting to previous month ({expected_month_str}).", output)

        expected_french_output = """Tous les proclamateurs actifs
7
Assistance moyenne à la réunion de week-end
100

PROCLAMATEURS
Nombre de fiches d’activité (S-4)
3
Cours bibliques
3

PIONNIERS AUXILIAIRES
Nombre de fiches d’activité (S-4)
1
Heures
30.00
Cours bibliques
3

PIONNIERS PERMANENTS
Nombre de fiches d’activité (S-4)
2
Heures
110.00
Cours bibliques
9""".strip()

        actual_report_lines = []
        report_content_started = False
        for line in output.split('\n'):
            if line.strip() == "Tous les proclamateurs actifs": report_content_started = True
            if not report_content_started: continue # Skip lines before this marker
            if not (line.startswith("Info:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or \
                    line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                actual_report_lines.append(line)

        final_actual_lines = [line for line in actual_report_lines if not line.startswith("Rapò kreye:")]
        actual_report_processed = "\n".join(final_actual_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                            f"Output does not match expected French summary for default month May 2026.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_no_activity_default_month(self, mock_datetime_summaries):
        """Tests the default month with no activity, expecting French-labeled output."""
        mock_datetime_summaries.timedelta = datetime.timedelta
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2024, 8, 15, 10, 0, 0)
        expected_month_str = "2024-07"
        result = self._run_cli_with_data(self.NO_ACTIVITY_JUL_2024_JSON_STR)

        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")
        self.assertIn(f"Info: --month not provided, defaulting to previous month ({expected_month_str}).", output)

        expected_french_output = """Tous les proclamateurs actifs
0
Assistance moyenne à la réunion de week-end
N/A

PROCLAMATEURS
Nombre de fiches d’activité (S-4)
0
Cours bibliques
0

PIONNIERS AUXILIAIRES
Nombre de fiches d’activité (S-4)
0
Heures
0.00
Cours bibliques
0

PIONNIERS PERMANENTS
Nombre de fiches d’activité (S-4)
0
Heures
0.00
Cours bibliques
0

Note: Aucune donnée d'activité disponible pour le mois 2024-07.""".strip()

        actual_report_lines = []
        report_content_started = False
        for line in output.split('\n'):
            if line.strip() == "Tous les proclamateurs actifs": report_content_started = True
            if not report_content_started: continue
            if not (line.startswith("Info:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or \
                    line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                actual_report_lines.append(line)

        final_actual_lines = [line for line in actual_report_lines if not line.startswith("Rapò kreye:")]
        actual_report_processed = "\n".join(final_actual_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                             f"Output does not match expected French no-activity summary for {expected_month_str}.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")

# Removed if __name__ == '__main__': block
# Removed old test_monthly_activity_no_activity as it's replaced by test_summary_new_format_no_activity_default_month
# Removed old _run_summary_command as it's replaced by _run_cli_with_data
# Removed self.mock_data_for_summaries as it's no longer used by these tests.
