import unittest
import json
import tempfile
import os
import datetime # Added
from unittest.mock import patch # Added
from click.testing import CliRunner
from collections import defaultdict

# Assuming 'fsr.cli:cli' is the entry point for the main CLI application.
# We will continue to test via CLI runner for end-to-end command testing.

class TestMonthlyActivityReport(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.maxDiff = None # Show full diffs

        # Mock data for summaries, updated for new features
        self.mock_data_for_summaries = {
            "congregation": {},
            "publishers": [
                {"id": "1000001", "firstname": "Michael", "lastname": "Edwards"}, # Inactive
                {"id": "1000002", "firstname": "Stephanie", "lastname": "Roman"}, # Aux Pioneer
                {"id": "1000003", "firstname": "Carol", "lastname": "Mitchell"},    # Publisher
                {"id": "1000004", "firstname": "Carl", "lastname": "Smith"},       # Publisher
                {"id": "1000005", "firstname": "Jason", "lastname": "Nguyen"},     # Reg Pioneer
                {"id": "1000006", "firstname": "Gabriel", "lastname": "Williams"}, # Special Pioneer (activity excluded from summary)
                {"id": "1000007", "firstname": "Joel", "lastname": "Jenkins"},     # Aux Pioneer
                {"id": "1000008", "firstname": "Jacqueline", "lastname": "Moore"}  # Publisher (reports, 0 activity)
            ],
            "reports": [
                # Month 1: 2026-08 (Active Month)
                {"year": 2026, "month": 8, "user": {"id": "1000001"}, "pioneer": None, "has_reported_field_service": False, "minutes": None, "studies": None},
                {"year": 2026, "month": 8, "user": {"id": "1000002"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 3000, "studies": 5}, # AP1: 50hr, 5st
                {"year": 2026, "month": 8, "user": {"id": "1000003"}, "pioneer": None, "has_reported_field_service": True, "minutes": 60, "studies": 1},          # Pub1: 1st
                {"year": 2026, "month": 8, "user": {"id": "1000004"}, "pioneer": "Publisher", "has_reported_field_service": True, "minutes": 120, "studies": 2},    # Pub2: 2st
                {"year": 2026, "month": 8, "user": {"id": "1000005"}, "pioneer": "Regular", "has_reported_field_service": True, "minutes": 600, "studies": None},   # RP1: 10hr, 0st
                {"year": 2026, "month": 8, "user": {"id": "1000006"}, "pioneer": "Special", "has_reported_field_service": True, "minutes": 0, "studies": 3},     # SP1: 0hr, 3st (EXCLUDED from this report)
                {"year": 2026, "month": 8, "user": {"id": "1000007"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 30, "studies": 0},      # AP2: 0hr (30min), 0st
                {"year": 2026, "month": 8, "user": {"id": "1000008"}, "pioneer": None, "has_reported_field_service": True, "minutes": 0, "studies": 0},          # Pub3: Reports, 0 activity

                # Month 2: 2026-09 (No Activity Month)
                {"year": 2026, "month": 9, "user": {"id": "1000001"}, "pioneer": None, "has_reported_field_service": False},
                {"year": 2026, "month": 9, "user": {"id": "1000002"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 0, "studies": 0},
                {"year": 2026, "month": 9, "user": {"id": "1000003"}, "pioneer": None, "has_reported_field_service": False},
                {"year": 2026, "month": 9, "user": {"id": "1000006"}, "pioneer": "Special", "has_reported_field_service": False}, # SP inactive this month
            ],
            "attendance": [ # Added
                {"month": "2026-08", "mwAvg": 0, "mwCount": 0, "mwTotal": 0, "weAvg": 150, "weCount": 4, "weTotal": 600},
                {"month": "2026-09", "mwAvg": 0, "mwCount": 0, "mwTotal": 0, "weAvg": 0, "weCount": 0, "weTotal": 0}
            ]
        }

    def _run_summary_command(self, month_str: str = None): # Modified signature
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp_json_file:
            json.dump(self.mock_data_for_summaries, tmp_json_file)
            tmp_json_file_path = tmp_json_file.name
        
        cli_path = "~/.local/bin/fsr" 
        if not os.path.exists(os.path.expanduser(cli_path)):
             cli_path = "fsr"

        cmd = [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity']
        if month_str:
            cmd.extend(['--month', month_str])

        result = self.runner.invoke(
            None,
            cmd, # Use the constructed cmd list
            catch_exceptions=False,
            prog_name="fsr"
        )
        os.remove(tmp_json_file_path)
        return result

    def test_monthly_activity_with_data(self):
        """Test summary for a month with various activities, new format."""
        result = self._run_summary_command("2026-08")
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n") # Normalize line endings

        # Expected values for 2026-08 (Special Pioneer 1000006 excluded)
        # Total Active Publishers (non-special):
        #   1000002 (AP), 1000003 (Pub), 1000004 (Pub), 1000005 (RP), 1000007 (AP), 1000008 (Pub) = 6
        self.assertIn("Tous les proclamateurs actifs", output)
        self.assertIn("6", output) # This needs to be specific. A simple "In" might catch other 6s.
                                     # We'll check its position relative to the label later if needed.

        # Weekend Avg Attendance: 150
        self.assertIn("Assistance moyenne à la réunion de week-end", output)
        self.assertIn("150", output) # Similar specificity concern as above.

        # Proclamateurs (Publishers):
        #   1000003: 1st
        #   1000004: 2st
        #   1000008: 0st (reports, counts for S-4)
        #   Count S-4: 3. Studies: 1 + 2 = 3. Hours: Not shown.
        # Expected output snippet for Proclamateurs:
        # Proclamateurs
        # Nombre de fiches d’activité (S-4)
        # 3
        # Cours bibliques
        # 3
        proclamateurs_header = "Proclamateurs"
        self.assertIn(f"{proclamateurs_header}\nNombre de fiches d’activité (S-4)\n3", output)
        self.assertIn(f"Cours bibliques\n3", output) # This will be within the Proclamateurs section
        self.assertNotIn("Heures", output.split(proclamateurs_header)[1].split("Pionniers auxiliaires")[0])


        # Pionniers auxiliaires:
        #   1000002: 50hr (from 3000min), 5st
        #   1000007: 0hr (from 30min), 0st
        #   Count S-4: 2. Hours: 50. Studies: 5.
        # Expected output snippet:
        # Pionniers auxiliaires
        # Nombre de fiches d’activité (S-4)
        # 2
        # Heures
        # 50
        # Cours bibliques
        # 5
        aux_pionniers_header = "Pionniers auxiliaires"
        perm_pionniers_header = "Pionniers permanents" # Delimiter for section end
        
        # Extracting section more robustly
        try:
            aux_section = output.split(aux_pionniers_header)[1].split(perm_pionniers_header)[0]
        except IndexError:
            self.fail(f"'{aux_pionniers_header}' or '{perm_pionniers_header}' not found in output or in wrong order.")

        self.assertIn("Nombre de fiches d’activité (S-4)\n2", aux_section)
        self.assertIn("Heures\n50", aux_section)
        self.assertIn("Cours bibliques\n5", aux_section)

        # Pionniers permanents:
        #   1000005: 10hr, 0st
        #   Count S-4: 1. Hours: 10. Studies: 0.
        # Expected output snippet:
        # Pionniers permanents
        # Nombre de fiches d’activité (S-4)
        # 1
        # Heures
        # 10
        # Cours bibliques
        # 0
        try:
            perm_section = output.split(perm_pionniers_header)[1].split("\n-----------------------------")[0]
        except IndexError:
            self.fail(f"'{perm_pionniers_header}' not found or structure changed.")

        self.assertIn("Nombre de fiches d’activité (S-4)\n1", perm_section)
        self.assertIn("Heures\n10", perm_section)
        self.assertIn("Cours bibliques\n0", perm_section)

        self.assertNotIn("Pyonye espesyal", output) # Special pioneers section should not exist
        self.assertNotIn("Total Etid Kongregasyon an", output) # This line is removed

        # Check overall counts more directly if possible (e.g. after "Tous les proclamateurs actifs")
        # This is tricky with simple assertIn. The section-based approach is better.
        # A more direct way to check "Tous les proclamateurs actifs\n6"
        self.assertIn("Tous les proclamateurs actifs\n6", output)
        self.assertIn("Assistance moyenne à la réunion de week-end\n150", output)


    def test_monthly_activity_no_activity(self):
        """Test summary for a month with no qualifying activity, new format."""
        result = self._run_summary_command("2026-09")
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")

        self.assertIn("Tous les proclamateurs actifs\n0", output)
        self.assertIn("Assistance moyenne à la réunion de week-end\nN/A", output) # 0 attendance -> N/A

        self.assertIn("Proclamateurs\nNombre de fiches d’activité (S-4)\n0", output)
        self.assertIn("Cours bibliques\n0", output.split("Proclamateurs")[1].split("Pionniers auxiliaires")[0]) # Check studies for Proclamateurs is 0

        aux_section = output.split("Pionniers auxiliaires")[1].split("Pionniers permanents")[0]
        self.assertIn("Nombre de fiches d’activité (S-4)\n0", aux_section)
        self.assertIn("Heures\n0", aux_section)
        self.assertIn("Cours bibliques\n0", aux_section)

        perm_section = output.split("Pionniers permanents")[1].split("\n-----------------------------")[0]
        self.assertIn("Nombre de fiches d’activité (S-4)\n0", perm_section)
        self.assertIn("Heures\n0", perm_section)
        self.assertIn("Cours bibliques\n0", perm_section)
        
        self.assertNotIn("Pyonye espesyal", output)
        self.assertIn("Note: Pa gen rapò ki disponib pou mwa 2026-09.", output)

    @patch('fsr.reports.summaries.datetime.datetime') # Path to datetime used in summaries.py
    def test_monthly_activity_default_month(self, mock_datetime):
        # Configure mock_datetime.now() to return a date that makes "2026-08" the current month
        mock_now = datetime.datetime(2026, 8, 15) # Example: 15th August 2026
        mock_datetime.now.return_value = mock_now

        expected_month_str = "2026-08"

        result = self._run_summary_command() # No month_str argument
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output.replace("\r\n", "\n")

        self.assertIn(f"Info: --month not provided, defaulting to current month ({expected_month_str})", output)

        # Assertions for 2026-08 data (adapted from test_monthly_activity_with_data)
        self.assertIn("Tous les proclamateurs actifs\n6", output)
        self.assertIn("Assistance moyenne à la réunion de week-end\n150", output)

        # Proclamateurs
        proclamateurs_header = "Proclamateurs"
        # Check for the full block for Proclamateurs to ensure numbers are in the right place
        expected_proclamateurs_block = f"{proclamateurs_header}\nNombre de fiches d’activité (S-4)\n3\nCours bibliques\n3"
        self.assertIn(expected_proclamateurs_block, output)
        self.assertNotIn("Heures", output.split(proclamateurs_header)[1].split("Pionniers auxiliaires")[0])

        # Pionniers auxiliaires
        aux_pionniers_header = "Pionniers auxiliaires"
        perm_pionniers_header = "Pionniers permanents"
        try:
            aux_section = output.split(aux_pionniers_header)[1].split(perm_pionniers_header)[0]
        except IndexError:
            self.fail(f"'{aux_pionniers_header}' or '{perm_pionniers_header}' not found in output for default month test.")

        self.assertIn("Nombre de fiches d’activité (S-4)\n2", aux_section)
        self.assertIn("Heures\n50", aux_section)
        self.assertIn("Cours bibliques\n5", aux_section)

        # Pionniers permanents
        try:
            perm_section = output.split(perm_pionniers_header)[1].split("\n-----------------------------")[0]
        except IndexError:
            self.fail(f"'{perm_pionniers_header}' not found or structure changed for default month test.")

        self.assertIn("Nombre de fiches d’activité (S-4)\n1", perm_section)
        self.assertIn("Heures\n10", perm_section)
        self.assertIn("Cours bibliques\n0", perm_section)

        self.assertNotIn("Pyonye espesyal", output)
# Removed: if __name__ == '__main__': unittest.main(...)
