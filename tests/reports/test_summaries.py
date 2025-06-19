import unittest
import json
import tempfile
import os
import datetime
from unittest.mock import patch
from click.testing import CliRunner
from collections import defaultdict

# JSON data constants defined at class level for clarity and reuse
USER_PROVIDED_JSON_MAY_2025_STR = """
{
  "congregation": {"id": 28341, "name": "East Karenberg Area Congregation (#744)", "locales_id": 37, "timezones_id": 95, "countries_id": 58, "jworg_langcode": "FR", "locale": {"id": 37, "code": "fr", "name": "French", "symbol": "FR"}},
  "publishers": [{"id": 1000001, "reportstobranch": false}, {"id": 1000002, "reportstobranch": false}, {"id": 1000003, "reportstobranch": false}, {"id": 1000004, "reportstobranch": false}, {"id": 1000005, "reportstobranch": false}, {"id": 1000008, "reportstobranch": false}, {"id": 1000009, "reportstobranch": true}, {"id": 1000010, "reportstobranch": true}],
  "reports": [
    {"user": {"id": 1000001}, "month": 5, "year": 2025, "minutes": 2340, "pioneer": "Regular", "studies": 6, "has_reported_field_service": true},
    {"user": {"id": 1000002}, "month": 5, "year": 2025, "minutes": 3300, "pioneer": "Regular", "studies": 6, "has_reported_field_service": true},
    {"user": {"id": 1000003}, "month": 5, "year": 2025, "minutes": 3840, "pioneer": "Regular", "studies": 4, "has_reported_field_service": true},
    {"user": {"id": 1000004}, "month": 5, "year": 2025, "minutes": 3960, "pioneer": "Regular", "studies": 5, "has_reported_field_service": true},
    {"user": {"id": 1000005}, "month": 5, "year": 2025, "minutes": 3600, "pioneer": "Regular", "studies": 8, "has_reported_field_service": true},
    {"user": {"id": 1000008}, "month": 5, "year": 2025, "minutes": 3000, "pioneer": "Regular", "studies": 3, "has_reported_field_service": true},
    {"user": {"id": 1000009}, "month": 5, "year": 2025, "minutes": 1, "pioneer": null, "studies": 15, "has_reported_field_service": true},
    {"user": {"id": 1000010}, "month": 5, "year": 2025, "minutes": 1, "pioneer": null, "studies": 14, "has_reported_field_service": true}
  ],
  "attendance": {"attendance": [{"month": "2025-05", "weAvg": 163}]}
}
"""

MAY_2026_MOCK_DATA_STR = """
{
  "congregation": {"id": 28342, "name": "Default Test Cong", "locale": {"id": 37, "code": "fr", "name": "French"}},
  "publishers": [
    {"id": "rp1", "reportstobranch": false}, {"id": "rp2", "reportstobranch": false},
    {"id": "ap1", "reportstobranch": false},
    {"id": "pub1", "reportstobranch": false}, {"id": "pub2", "reportstobranch": false}, {"id": "pub3", "reportstobranch": false},
    {"id": "sp1", "reportstobranch": true},
    {"id": "inactive1"}
  ],
  "reports": [
    {"user": {"id": "rp1"}, "year": 2026, "month": 5, "minutes": 3000, "studies": 5, "pioneer": "Regular"},
    {"user": {"id": "rp2"}, "year": 2026, "month": 5, "minutes": 3600, "studies": 4, "pioneer": "Regular"},
    {"user": {"id": "ap1"}, "year": 2026, "month": 5, "minutes": 1800, "studies": 3, "pioneer": "Auxiliary"},
    {"user": {"id": "pub1"}, "year": 2026, "month": 5, "minutes": 600, "studies": 2, "pioneer": null},
    {"user": {"id": "pub2"}, "year": 2026, "month": 5, "minutes": 0, "studies": 1, "pioneer": null},
    {"user": {"id": "pub3"}, "year": 2026, "month": 5, "minutes": 300, "studies": 0, "pioneer": null},
    {"user": {"id": "sp1"}, "year": 2026, "month": 5, "minutes": 6000, "studies": 10, "pioneer": "Special"}
  ],
  "attendance": {"attendance": [{"month": "2026-05", "weAvg": 100}]}
}
"""

WITH_DATA_OCT_2023_JSON_STR = """
{
  "congregation": {"id": 28343, "name": "With Data Oct Cong", "locale": {"id": 37, "code": "fr", "name": "French"}},
  "publishers": [
    {"id": "rp_wd1", "reportstobranch": false}, {"id": "ap_wd1", "reportstobranch": false},
    {"id": "pub_wd1", "reportstobranch": false}, {"id": "pub_wd2", "reportstobranch": false},
    {"id": "sp_wd1", "reportstobranch": true}, {"id": "inactive_wd1"}
  ],
  "reports": [
    {"user": {"id": "rp_wd1"}, "year": 2023, "month": 10, "minutes": 3300, "studies": 3, "pioneer": "Regular"},
    {"user": {"id": "ap_wd1"}, "year": 2023, "month": 10, "minutes": 2100, "studies": 2, "pioneer": "Auxiliary"},
    {"user": {"id": "pub_wd1"}, "year": 2023, "month": 10, "minutes": 720, "studies": 1, "pioneer": null},
    {"user": {"id": "pub_wd2"}, "year": 2023, "month": 10, "minutes": 480, "studies": 0, "pioneer": null},
    {"user": {"id": "sp_wd1"}, "year": 2023, "month": 10, "minutes": 5400, "studies": 7, "pioneer": "Special"}
  ],
  "attendance": {"attendance": [{"month": "2023-10", "weAvg": 150}]}
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
    WITH_DATA_OCT_2023_JSON_STR = WITH_DATA_OCT_2023_JSON_STR
    NO_ACTIVITY_JUL_2024_JSON_STR = NO_ACTIVITY_JUL_2024_JSON_STR

    def setUp(self):
        self.runner = CliRunner()
        self.maxDiff = None

    def _run_cli_with_data(self, json_data_str, month_arg=None):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json", encoding='utf-8') as tmp_json_file:
            tmp_json_file.write(json_data_str)
            tmp_json_file_path = tmp_json_file.name
        
        cli_path = "~/.local/bin/fsr" 
        if not os.path.exists(os.path.expanduser(cli_path)):
            cli_path = "fsr"

        cmd = [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity']
        if month_arg:
            cmd.extend(['--month', month_arg])

        result = self.runner.invoke(None, cmd, catch_exceptions=False, prog_name="fsr")
        os.remove(tmp_json_file_path)
        return result

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_may_2025(self, mock_datetime_summaries):
        """Tests the May 2025 summary with the new French-labeled format and SP logic."""
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2025, 6, 15, 10, 0, 0)
        result = self._run_cli_with_data(self.USER_PROVIDED_JSON_MAY_2025_STR, "2025-05")
        
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")

        expected_french_output = """Tous les proclamateurs actifs
8
Assistance moyenne à la réunion de week-end
163

PROCLAMATEURS
Nombre de fiches d’activité (S-4)
0
Cours bibliques
0
Heures
0.00

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
            if not (line.startswith("Info:") or line.startswith("Rapò kreye:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                actual_report_lines.append(line)
        actual_report_processed = "\n".join(actual_report_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                         f"Output does not match expected French summary for May 2025.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_default_month(self, mock_datetime_summaries):
        """Tests the default month summary (May 2026) with the new French-labeled format."""
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2026, 6, 15, 10, 0, 0)
        expected_month_str = "2026-05"
        result = self._run_cli_with_data(self.MAY_2026_MOCK_DATA_STR) # No month arg

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
Heures
15.00

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
            if not report_content_started: continue
            if not (line.startswith("Info:") or line.startswith("Rapò kreye:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                actual_report_lines.append(line)
        actual_report_processed = "\n".join(actual_report_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                            f"Output does not match expected French summary for default month May 2026.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_oct_2023(self, mock_datetime_summaries):
        """Tests a specific month (Oct 2023) with the new French-labeled format."""
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2023, 11, 15, 10, 0, 0)
        month_to_test = "2023-10"
        result = self._run_cli_with_data(self.WITH_DATA_OCT_2023_JSON_STR, month_to_test)

        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")

        expected_french_output = """Tous les proclamateurs actifs
5
Assistance moyenne à la réunion de week-end
150

PROCLAMATEURS
Nombre de fiches d’activité (S-4)
2
Cours bibliques
1
Heures
20.00

PIONNIERS AUXILIAIRES
Nombre de fiches d’activité (S-4)
1
Heures
35.00
Cours bibliques
2

PIONNIERS PERMANENTS
Nombre de fiches d’activité (S-4)
1
Heures
55.00
Cours bibliques
3""".strip()

        actual_report_lines = []
        report_content_started = False
        for line in output.split('\n'):
            if line.strip() == "Tous les proclamateurs actifs": report_content_started = True
            if not report_content_started: continue
            if not (line.startswith("Info:") or line.startswith("Rapò kreye:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                actual_report_lines.append(line)
        actual_report_processed = "\n".join(actual_report_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                             f"Output does not match expected French summary for Oct 2023.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")

    @patch('fsr.reports.summaries.datetime')
    def test_summary_new_format_no_activity_default_month(self, mock_datetime_summaries):
        """Tests the default month with no activity, expecting French-labeled output."""
        mock_datetime_summaries.datetime.now.return_value = datetime.datetime(2024, 8, 15, 10, 0, 0)
        expected_month_str = "2024-07"
        result = self._run_cli_with_data(self.NO_ACTIVITY_JUL_2024_JSON_STR) # No month arg

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
Heures
0.00

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
0""".strip()

        actual_report_lines = []
        report_content_started = False
        for line in output.split('\n'):
            if line.strip() == "Tous les proclamateurs actifs": report_content_started = True
            if not report_content_started: continue
            if not (line.startswith("Info:") or line.startswith("Rapò kreye:") or \
                    line.startswith("Rezime Rapò Aktivite Mansyèl") or line.startswith("Pou Mwa:") or \
                    line.strip() == "-----------------------------"):
                actual_report_lines.append(line)
        actual_report_processed = "\n".join(actual_report_lines).strip()

        self.assertEqual(actual_report_processed, expected_french_output,
                             f"Output does not match expected French no-activity summary for {expected_month_str}.\nExpected:\n{expected_french_output}\n\nActual:\n{actual_report_processed}")
