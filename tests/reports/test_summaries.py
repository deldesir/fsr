import unittest
import json
import tempfile
import os
from click.testing import CliRunner
from collections import defaultdict

# Assuming 'fsr.cli:cli' is the entry point for the main CLI application
# and that 'fsr.core.data_loader.CongregationData' is the data structure used.
# We need to be able to invoke the 'summary monthly-activity' command.
# This might require access to the main 'cli' object from 'fsr.cli'.
# For simplicity, if direct invocation of monthly_activity_report is possible and preferred for unit testing,
# that would be an alternative, but testing via CLI runner is more end-to-end for commands.

# To test CLI:
# from fsr.cli import cli # Or however your main CLI group is defined

# For this test, we'll prepare a mock JSON file that can be loaded by CongregationData via the CLI's --json-file option.

class TestMonthlyActivityReport(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.maxDiff = None # Show full diffs

        # Mock data for summaries - based on user's anonymized data and scenarios
        self.mock_data_for_summaries = {
            "congregation": {},
            "publishers": [
                {"id": "1000001", "firstname": "Michael", "lastname": "Edwards"},
                {"id": "1000002", "firstname": "Stephanie", "lastname": "Roman"},
                {"id": "1000003", "firstname": "Carol", "lastname": "Mitchell"},
                {"id": "1000004", "firstname": "Carl", "lastname": "Smith"},
                {"id": "1000005", "firstname": "Jason", "lastname": "Nguyen"},
                {"id": "1000006", "firstname": "Gabriel", "lastname": "Williams"},
                {"id": "1000007", "firstname": "Joel", "lastname": "Jenkins"},
                {"id": "1000008", "firstname": "Jacqueline", "lastname": "Moore"},
                {"id": "1000009", "firstname": "Crystal", "lastname": "Anderson"},
                {"id": "1000010", "firstname": "Matthew", "lastname": "Jones"}
            ],
            "reports": [
                # Month 1: 2026-08 (Active Month)
                {"year": 2026, "month": 8, "user": {"id": "1000001"}, "pioneer": None, "has_reported_field_service": False, "minutes": None, "studies": None, "remarks": "Vacation"}, # Not counted in summary
                {"year": 2026, "month": 8, "user": {"id": "1000002"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 3000, "studies": 5, "remarks": ""}, # AP: 50hr, 5st
                {"year": 2026, "month": 8, "user": {"id": "1000003"}, "pioneer": None, "has_reported_field_service": True, "minutes": 60, "studies": 1, "remarks": ""},       # Pub: 1hr (not summed), 1st
                {"year": 2026, "month": 8, "user": {"id": "1000004"}, "pioneer": "Publisher", "has_reported_field_service": True, "minutes": 120, "studies": 2, "remarks": "Good job"}, # Pub: 2hr (not summed), 2st
                {"year": 2026, "month": 8, "user": {"id": "1000005"}, "pioneer": "Regular", "has_reported_field_service": True, "minutes": 600, "studies": None, "remarks": ""}, # RP: 10hr, 0st
                {"year": 2026, "month": 8, "user": {"id": "1000006"}, "pioneer": "Special", "has_reported_field_service": True, "minutes": 0, "studies": 3}, # SP: 0hr, 3st. Active by studies.
                {"year": 2026, "month": 8, "user": {"id": "1000007"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 30, "studies": 0}, # AP: active by minutes, but <1hr, 0 studies
                {"year": 2026, "month": 8, "user": {"id": "1000008"}, "pioneer": None, "has_reported_field_service": True, "minutes": 0, "studies": 0, "remarks": "Reported, no activity"}, # Active by explicit True, but 0 activity.


                # Month 2: 2026-09 (No Activity Month for summary check)
                # All reports have has_reported_field_service: False or no positive minutes/studies
                {"year": 2026, "month": 9, "user": {"id": "1000001"}, "pioneer": None, "has_reported_field_service": False, "remarks": "Still out"},
                {"year": 2026, "month": 9, "user": {"id": "1000002"}, "pioneer": "Auxiliary", "has_reported_field_service": True, "minutes": 0, "studies": 0},
                {"year": 2026, "month": 9, "user": {"id": "1000003"}, "pioneer": None, "has_reported_field_service": False},
            ]
        }

    def _run_summary_command(self, month_str):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp_json_file:
            json.dump(self.mock_data_for_summaries, tmp_json_file)
            tmp_json_file_path = tmp_json_file.name
        
        # Assumes 'fsr' is callable via CLI after 'pip install -e .'
        # The path might need to be ~/.local/bin/fsr if not in main PATH
        cli_path = "~/.local/bin/fsr" 
        if not os.path.exists(os.path.expanduser(cli_path)): # Fallback for environments where it might be in main path
             cli_path = "fsr"

        result = self.runner.invoke(
            None, # We need to invoke the top-level CLI group if it's defined in fsr.cli.cli
            [cli_path, '--json-file', tmp_json_file_path, 'summary', 'monthly-activity', '--month', month_str],
            catch_exceptions=False, # Let exceptions propagate for debugging
            prog_name="fsr" # Helps Click identify the command if fsr.cli.cli is a group
        )
        os.remove(tmp_json_file_path)
        return result

    def test_monthly_activity_with_data(self):
        """Test summary for a month with various activities."""
        result = self._run_summary_command("2026-08")
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output

        # Expected values for 2026-08 based on current summary logic
        # Pwoklamatè ki pa pyonye (Non-Pioneers):
        #   1000003: 1st (60 min, not counted for hours)
        #   1000004: 2st (120 min, not counted for hours)
        #   1000008: 0st, 0min (active by explicit True in CSV exports, but summary logic infers from min/studies)
        #     -> Summary logic: Pub 1000003 (studies>0), Pub 1000004 (studies>0). Pub 1000008 has 0 min/studies, so NOT counted.
        #   Count = 2, Total Studies = 1 + 2 = 3
        self.assertIn("*Rapò pou Pwoklamatè Ki Pa Pyonye (08-2026)*", output)
        self.assertIn("Total Etid: 3", output) # 1 (Carol) + 2 (Carl) = 3
        self.assertIn("_Te gen 2 pwoklamatè ki pa pyonye ki te bay rapò pou mwa sa._", output)

        # Pyonye Oksilyè (Auxiliary Pioneers):
        #   1000002: 50hr, 5st
        #   1000007: 0hr (30min), 0st (active by positive minutes)
        #   Count = 2, Total Hours = 50 + 0 = 50, Total Studies = 5 + 0 = 5
        self.assertIn("*Rapò pou Pyonye Oksilyè (08-2026)*", output)
        self.assertIn("Total Lè: 50", output)
        self.assertIn("Total Etid: 5", output)
        self.assertIn("_Te gen 2 pyonye oksilyè ki te bay rapò pou mwa sa._", output)
        
        # Pyonye Pèmanan (Regular Pioneers):
        #   1000005: 10hr, 0st (studies is null)
        #   Count = 1, Total Hours = 10, Total Studies = 0
        self.assertIn("*Rapò pou Pyonye Pèmanan (08-2026)*", output)
        self.assertIn("Total Lè: 10", output)
        self.assertIn("Total Etid: 0", output)
        self.assertIn("_Te gen 1 pyonye pèmanan ki te bay rapò pou mwa sa._", output)

        # Pyonye Espesyal (Special Pioneers):
        #   1000006: 0hr (0 min), 3st (active by studies)
        #   Count = 1, Total Hours = 0, Total Studies = 3
        self.assertIn("*Rapò pou Pyonye Espesyal (08-2026)*", output)
        self.assertIn("Total Lè: 0", output)
        self.assertIn("Total Etid: 3", output)
        self.assertIn("_Te gen 1 pyonye espesyal ki te bay rapò pou mwa sa._", output)

        # Total Congregation Studies: 3 (Pub) + 5 (AP) + 0 (RP) + 3 (SP) = 11
        self.assertIn("Total Etid Kongregasyon an: 11", output)
        
        # Check that 1000001 (Vacation, has_reported_field_service: False) is not counted anywhere
        # Check that 1000008 (0 min, 0 studies) is not counted as pwoklamatè
        # (This is implicitly checked by the counts above)

    def test_monthly_activity_no_activity(self):
        """Test summary for a month with no qualifying activity."""
        result = self._run_summary_command("2026-09")
        self.assertEqual(result.exit_code, 0, f"CLI Error: {result.output}")
        output = result.output
        
        # For 2026-09:
        # 1000001: has_reported_field_service: False -> ignored
        # 1000002: AP, 0 min, 0 studies -> not counted as active by summary logic (needs >0 min or >0 studies)
        # 1000003: has_reported_field_service: False -> ignored
        # So, all counts should be 0.

        self.assertIn("*Rapò pou Pwoklamatè Ki Pa Pyonye (09-2026)*", output)
        self.assertIn("Total Etid: 0", output)
        self.assertIn("_Te gen 0 pwoklamatè ki pa pyonye ki te bay rapò pou mwa sa._", output)

        self.assertIn("*Rapò pou Pyonye Oksilyè (09-2026)*", output)
        self.assertIn("Total Lè: 0", output)
        self.assertIn("Total Etid: 0", output)
        self.assertIn("_Te gen 0 pyonye oksilyè ki te bay rapò pou mwa sa._", output)
        
        self.assertIn("*Rapò pou Pyonye Pèmanan (09-2026)*", output)
        self.assertIn("Total Lè: 0", output)
        self.assertIn("Total Etid: 0", output)
        self.assertIn("_Te gen 0 pyonye pèmanan ki te bay rapò pou mwa sa._", output)

        self.assertIn("*Rapò pou Pyonye Espesyal (09-2026)*", output)
        self.assertIn("Total Lè: 0", output)
        self.assertIn("Total Etid: 0", output)
        self.assertIn("_Te gen 0 pyonye espesyal ki te bay rapò pou mwa sa._", output)
        
        self.assertIn("Total Etid Kongregasyon an: 0", output)
        self.assertIn("Note: Pa gen rapò ki disponib pou mwa 2026-09.", output)

if __name__ == '__main__':
    # This allows running the tests directly if the fsr module is in PYTHONPATH
    # For the agent, direct execution isn't the primary concern, but good for local testing.
    # Need to ensure fsr.cli can be imported or use a different way to get 'cli' group.
    # The CliRunner().invoke(None, ...) with full path to fsr script is more robust in this env.
    
    # To make fsr.cli.cli available for CliRunner().invoke(cli, ...)
    # we would need to ensure the path is set up, or the package is installed.
    # The current _run_summary_command tries to handle this.
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
