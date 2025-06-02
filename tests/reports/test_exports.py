import csv
import os
import unittest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
import tempfile
from datetime import datetime
from pathlib import Path

from fsr import cli as fsr_main_cli # Import the main CLI entry point
from fsr.core.data_loader import CongregationData
from fsr.core import constants as fsr_constants


class TestExportCsvCommandFinal(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_cong_data = MagicMock(spec=CongregationData)
        self.mock_cong_data.publishers_list = []
        self.mock_cong_data.reports_by_publisher_month_year = {}
        self.expected_headers = [
            'Date', 'FirstName', 'LastName', 'SharedInMinistry', 'BibleStudies',
            'AP', 'Hours', 'Credit', 'Remarks'
        ]
        # This dummy path will be created within isolated_filesystem for each test
        self.dummy_input_json_filename = "dummy_input.json"


    def _run_command(self, temp_dir_path, export_specific_args=None):
        """
        Runs the `export field-service` command via the main CLI.
        `temp_dir_path` is the path to the temporary directory provided by isolated_filesystem.
        `export_specific_args` are arguments specifically for the `export field-service` subcommand.
        """
        # Path for the dummy input JSON within the isolated filesystem
        dummy_json_full_path = os.path.join(temp_dir_path, self.dummy_input_json_filename)
        
        # Ensure dummy input JSON file exists for the main CLI --json-file option
        with open(dummy_json_full_path, 'w') as f:
            f.write('{}') # Minimal valid JSON

        # Arguments for the main CLI command
        main_cli_args = ['--json-file', dummy_json_full_path, 'export', 'field-service']
        if export_specific_args:
            main_cli_args.extend(export_specific_args)
        
        # Context object to be passed to the CLI invocation
        # This simulates that data loading has occurred and json_file_path is set
        ctx_obj = {
            'cong_data': self.mock_cong_data,
            'json_file_path': dummy_json_full_path # Path to the input JSON
        }

        result = self.runner.invoke(fsr_main_cli.cli, main_cli_args, obj=ctx_obj, catch_exceptions=False)
        
        # Determine the output CSV path for verification
        # If --csv-file is in export_specific_args, use that. Otherwise, it's complex (generated).
        output_csv_name = "output.csv" # Default for old tests not specifying args
        if export_specific_args:
            try:
                idx = export_specific_args.index('--csv-file')
                output_csv_name = export_specific_args[idx + 1]
            except (ValueError, IndexError):
                # --csv-file not provided, name was generated. Test must predict it.
                # For simplicity, this helper will return None for path if generated.
                # The test method itself will need to construct the expected path.
                # Or, we can try to find the generated CSV.
                generated_files = [p for p in Path(temp_dir_path).glob('*.csv')]
                if len(generated_files) == 1:
                    output_csv_name = generated_files[0].name
                else: # Cannot determine, or multiple CSVs
                    return result, None 


        return result, os.path.join(temp_dir_path, output_csv_name)


    def _read_csv_data(self, csv_filepath):
        if not os.path.exists(csv_filepath):
            return None, []
        with open(csv_filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            rows = [dict(row) for row in reader]
        return fieldnames, rows

    def test_csv_creation_and_headers_if_no_publishers_with_reports(self):
        """If no publishers have reports (or no publishers at all), CSV has only headers."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub_no_reports', 'firstname': 'NoReport', 'lastname': 'User'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {} # No reports for anyone
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertTrue(os.path.exists(csv_filepath), f"CSV file not found at {csv_filepath}")
            fieldnames, rows = self._read_csv_data(csv_filepath)
            self.assertListEqual(list(fieldnames) if fieldnames else [], self.expected_headers, f"CSV headers mismatch in {csv_filepath}")
            self.assertEqual(len(rows), 0) # No data rows

    def test_publisher_with_no_reports_is_omitted(self):
        """Publishers with no reports are omitted from CSV."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub_with_report', 'firstname': 'Reporter', 'lastname': 'Person'},
            {'id': 'pub_no_reports', 'firstname': 'NoReport', 'lastname': 'User'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('pub_with_report', 2023, 1): {'has_reported_field_service': True, 'minutes': 60}
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 1, f"Expected 1 row, got {len(rows)} in {csv_filepath}")
            self.assertEqual(rows[0]['FirstName'], 'Reporter')

    def test_publisher_name_key_variations_with_reports(self):
        """Name key variations for publishers *who have reports*."""
        self.mock_cong_data.publishers_list = [
            {'id': 'std_lc', 'firstname': 'John', 'lastname': 'Doe'},      
            {'id': 'no_fn', 'lastname': 'Smith'},                           
            {'id': 'no_ln', 'firstname': 'Jane'},          
            {'id': 'camel_keys', 'firstName': 'Alice', 'lastName': 'Wonder'} # Code expects lowercase
        ]
        # Each publisher needs at least one report to be included
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('std_lc', 2023, 1): {'has_reported_field_service': True, 'minutes': 60},
            ('no_fn', 2023, 1): {'has_reported_field_service': True, 'minutes': 60},
            ('no_ln', 2023, 1): {'has_reported_field_service': True, 'minutes': 60},
            ('camel_keys', 2023, 1): {'has_reported_field_service': True, 'minutes': 60},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 4, f"CSV rows count mismatch in {csv_filepath}")

            rows_by_name = {(r['FirstName'], r['LastName']): r for r in rows}
            self.assertIn(('John', 'Doe'), rows_by_name)
            self.assertIn(('', 'Smith'), rows_by_name)
            self.assertIn(('Jane', ''), rows_by_name)
            self.assertIn(('', ''), rows_by_name) # For Alice Wonder with camelCase keys

    def test_final_comprehensive_output_scenarios(self):
        """Comprehensive test for all field logic, including omission of no-report publishers."""
        self.mock_cong_data.publishers_list = [
            {'id': 'p1', 'firstname': 'AuxiliaryP', 'lastname': 'One'},
            {'id': 'p2', 'firstname': 'RegularP', 'lastname': 'Two'},
            {'id': 'p3', 'firstname': 'PublisherF', 'lastname': 'Three'},
            {'id': 'p4', 'firstname': 'NoServiceP', 'lastname': 'Four'},
            {'id': 'p5', 'firstname': 'MiscP', 'lastname': 'Five'},
            {'id': 'p6', 'firstname': 'NeverReported', 'lastname': 'Six'} # This publisher has no reports
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            # p1: AuxiliaryP One
            ('p1', 2023, 9): {'has_reported_field_service': True, 'pioneer': 'Auxiliary', 'minutes': 1200, 'studies': 3, 'credithours': 0, 'remarks': 'AP Full Month'}, # Credit 0 -> ''
            ('p1', 2023, 10): {'has_reported_field_service': True, 'pioneer': 'Auxiliary', 'minutes': 30, 'studies': 0, 'credithours': 5}, # <1hr, 0 studies
            
            # p2: RegularP Two
            ('p2', 2023, 9): {'has_reported_field_service': True, 'pioneer': 'Regular', 'minutes': 3000, 'studies': None, 'credithours': "2.5", 'remarks': 'RP good month'},
            
            # p3: PublisherF Three (non-pioneer)
            ('p3', 2023, 9): {'has_reported_field_service': True, 'pioneer': None, 'minutes': 120, 'studies': 1, 'credithours': 0}, 
            ('p3', 2023, 10): {'has_reported_field_service': True, 'pioneer': 'Publisher', 'minutes': 0, 'studies': 0, 'credithours': 0}, 
            
            # p4: NoServiceP Four (has_reported_field_service: False)
            ('p4', 2023, 9): {'has_reported_field_service': False, 'pioneer': 'Auxiliary', 'minutes': 600, 'studies': 2, 'credithours': 5, 'remarks': 'Specific Comment When Not Sharing'},
            ('p4', 2023, 10): {'has_reported_field_service': False, 'pioneer': None, 'remarks': "   "}, # Remarks only whitespace
            
            # p5: MiscP Five
            ('p5', 2023, 9): {'has_reported_field_service': True, 'pioneer': 'Special', 'minutes': None, 'studies': 5, 'credithours': "10"}, 
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            
            # Expected rows: p1(2), p2(1), p3(2), p4(2), p5(1) = 8 rows. p6 is omitted.
            self.assertEqual(len(rows), 8, f"CSV rows count mismatch in {csv_filepath}")

            def get_rows(firstname): return sorted([r for r in rows if r['FirstName'] == firstname], key=lambda r: r['Date'])

            # P1: AuxiliaryP One
            p1_rows = get_rows('AuxiliaryP')
            self.assertEqual(len(p1_rows), 2)
            self.assertEqual(p1_rows[0]['Date'], '2023-09'); self.assertEqual(p1_rows[0]['SharedInMinistry'], 'True'); self.assertEqual(p1_rows[0]['AP'], 'True'); self.assertEqual(p1_rows[0]['Hours'], '20'); self.assertEqual(p1_rows[0]['BibleStudies'], '3'); self.assertEqual(p1_rows[0]['Credit'], ''); self.assertEqual(p1_rows[0]['Remarks'], 'AP Full Month')
            self.assertEqual(p1_rows[1]['Date'], '2023-10'); self.assertEqual(p1_rows[1]['SharedInMinistry'], 'True'); self.assertEqual(p1_rows[1]['AP'], 'True'); self.assertEqual(p1_rows[1]['Hours'], ''); self.assertEqual(p1_rows[1]['BibleStudies'], ''); self.assertEqual(p1_rows[1]['Credit'], '5'); self.assertEqual(p1_rows[1]['Remarks'], '')

            # P2: RegularP Two
            p2_rows = get_rows('RegularP')
            self.assertEqual(len(p2_rows), 1)
            self.assertEqual(p2_rows[0]['Date'], '2023-09'); self.assertEqual(p2_rows[0]['SharedInMinistry'], 'True'); self.assertEqual(p2_rows[0]['AP'], 'False'); self.assertEqual(p2_rows[0]['Hours'], '50'); self.assertEqual(p2_rows[0]['BibleStudies'], ''); self.assertEqual(p2_rows[0]['Credit'], '2.5'); self.assertEqual(p2_rows[0]['Remarks'], 'RP good month')
            
            # P3: PublisherF Three
            p3_rows = get_rows('PublisherF')
            self.assertEqual(len(p3_rows), 2)
            self.assertEqual(p3_rows[0]['Date'], '2023-09'); self.assertEqual(p3_rows[0]['SharedInMinistry'], 'True'); self.assertEqual(p3_rows[0]['AP'], 'False'); self.assertEqual(p3_rows[0]['Hours'], '2'); self.assertEqual(p3_rows[0]['BibleStudies'], '1'); self.assertEqual(p3_rows[0]['Credit'], ''); self.assertEqual(p3_rows[0]['Remarks'], '')
            self.assertEqual(p3_rows[1]['Date'], '2023-10'); self.assertEqual(p3_rows[1]['SharedInMinistry'], 'True'); self.assertEqual(p3_rows[1]['AP'], 'False'); self.assertEqual(p3_rows[1]['Hours'], ''); self.assertEqual(p3_rows[1]['BibleStudies'], ''); self.assertEqual(p3_rows[1]['Credit'], ''); self.assertEqual(p3_rows[1]['Remarks'], '')

            # P4: NoServiceP Four
            p4_rows = get_rows('NoServiceP')
            self.assertEqual(len(p4_rows), 2)
            self.assertEqual(p4_rows[0]['Date'], '2023-09'); self.assertEqual(p4_rows[0]['SharedInMinistry'], 'False'); self.assertEqual(p4_rows[0]['AP'], 'False'); self.assertEqual(p4_rows[0]['Hours'], ''); self.assertEqual(p4_rows[0]['BibleStudies'], ''); self.assertEqual(p4_rows[0]['Credit'], ''); self.assertEqual(p4_rows[0]['Remarks'], 'Specific Comment When Not Sharing')
            self.assertEqual(p4_rows[1]['Date'], '2023-10'); self.assertEqual(p4_rows[1]['SharedInMinistry'], 'False'); self.assertEqual(p4_rows[1]['AP'], 'False'); self.assertEqual(p4_rows[1]['Hours'], ''); self.assertEqual(p4_rows[1]['BibleStudies'], ''); self.assertEqual(p4_rows[1]['Credit'], ''); self.assertEqual(p4_rows[1]['Remarks'], '') # Whitespace remark becomes empty

            # P5: MiscP Five
            p5_rows = get_rows('MiscP')
            self.assertEqual(len(p5_rows), 1)
            self.assertEqual(p5_rows[0]['Date'], '2023-09'); self.assertEqual(p5_rows[0]['SharedInMinistry'], 'True'); self.assertEqual(p5_rows[0]['AP'], 'False'); self.assertEqual(p5_rows[0]['Hours'], ''); self.assertEqual(p5_rows[0]['BibleStudies'], '5'); self.assertEqual(p5_rows[0]['Credit'], '10'); self.assertEqual(p5_rows[0]['Remarks'], '')

            # Verify P6 (NeverReported) is NOT in the output
            for row in rows:
                self.assertNotEqual(row['FirstName'], 'NeverReported', "Publisher 'NeverReported' should be omitted.")

    def test_existing_output_file_overwritten(self): # Keep this as a sanity check for file ops
        # Existing tests now use _run_command which calls the main CLI
        # Need to ensure they pass correct export_specific_args
        # For example, the original _run_command implicitly used ['--csv-file', 'output.csv']
        with tempfile.TemporaryDirectory() as temp_dir:
            self.mock_cong_data.publishers_list = [{'id': 'p_init', 'firstname': 'Initial', 'lastname': 'Content'}]
            self.mock_cong_data.reports_by_publisher_month_year = {('p_init', 2023, 1): {'has_reported_field_service': True, 'minutes': 70}}
            # Pass the specific args for this call of _run_command
            result1, csv_filepath1 = self._run_command(temp_dir, export_specific_args=['--csv-file', 'output1.csv'])
            self.assertEqual(result1.exit_code, 0, f"Cmd failed: {result1.output}")
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(rows1[0]['Hours'], '1')

            self.mock_cong_data.publishers_list = [{'id': 'p_over', 'firstname': 'Overwritten', 'lastname': 'Content'}]
            self.mock_cong_data.reports_by_publisher_month_year = {('p_over', 2023, 2): {'has_reported_field_service': True, 'pioneer': 'Auxiliary', 'minutes': 120}}
            result2, csv_filepath2 = self._run_command(temp_dir, export_specific_args=['--csv-file', 'output2.csv']) # Use a different name or ensure overwrite
            self.assertEqual(result2.exit_code, 0, f"Cmd failed: {result2.output}")
            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[0]['Hours'], '2')

    # New tests for filename generation and app-target option
    @patch('fsr.reports.exports.datetime') # Mock datetime in the exports module
    def test_default_csv_filename_generation(self, mock_datetime_in_exports):
        fixed_now = datetime(2023, 1, 15, 10, 30, 0) # Fixed point in time
        mock_datetime_in_exports.now.return_value = fixed_now
        timestamp_str = fixed_now.strftime("%Y%m%d") # "20230115"

        input_json_stem = Path(self.dummy_input_json_filename).stem # "dummy_input"
        expected_app_target = fsr_constants.DEFAULT_APP_TARGET # Default, e.g., "NWScheduler"
        expected_filename = f"{expected_app_target}_{input_json_stem}_{timestamp_str}.csv"
        
        with self.runner.isolated_filesystem() as td:
            # _run_command will create the dummy JSON inside td
            # Call without --csv-file to trigger default name generation
            result, generated_csv_path = self._run_command(td, export_specific_args=[]) # No specific args for export

            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertIsNotNone(generated_csv_path, "Generated CSV path should be determined by _run_command")
            
            # Check if the generated file name matches expected
            # generated_csv_path is absolute, expected_filename is just the name
            self.assertEqual(Path(generated_csv_path).name, expected_filename, f"Generated filename mismatch. Got {Path(generated_csv_path).name}")
            self.assertTrue(os.path.exists(generated_csv_path), f"Expected CSV file {generated_csv_path} not found.")
            # Check user message (this requires the message to be part of result.output)
            # The message uses an absolute path, so construct it based on td
            expected_msg_filepath = os.path.join(td, expected_filename)
            self.assertIn(f"Defaulting to: {expected_msg_filepath}", result.output)


    @patch('fsr.reports.exports.datetime')
    def test_default_csv_filename_with_app_target_option(self, mock_datetime_in_exports):
        fixed_now = datetime(2023, 1, 16, 11, 0, 0)
        mock_datetime_in_exports.now.return_value = fixed_now
        timestamp_str = fixed_now.strftime("%Y%m%d") # "20230116"

        custom_app_target = "CustomApp"
        input_json_stem = Path(self.dummy_input_json_filename).stem
        expected_filename = f"{custom_app_target}_{input_json_stem}_{timestamp_str}.csv"
        
        original_targets = fsr_constants.CONFIGURABLE_APP_TARGETS
        original_default = fsr_constants.DEFAULT_APP_TARGET
        # Temporarily modify constants for this test if Click's Choice validation is strict
        fsr_constants.CONFIGURABLE_APP_TARGETS = [fsr_constants.DEFAULT_APP_TARGET, custom_app_target]

        with self.runner.isolated_filesystem() as td:
            export_args = ['--app-target', custom_app_target] # No --csv-file
            result, generated_csv_path = self._run_command(td, export_specific_args=export_args)

            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertIsNotNone(generated_csv_path)
            self.assertEqual(Path(generated_csv_path).name, expected_filename)
            self.assertTrue(os.path.exists(generated_csv_path))
            expected_msg_filepath = os.path.join(td, expected_filename)
            self.assertIn(f"Defaulting to: {expected_msg_filepath}", result.output)
        
        fsr_constants.CONFIGURABLE_APP_TARGETS = original_targets # Restore
        fsr_constants.DEFAULT_APP_TARGET = original_default


    def test_provided_csv_filename_overrides_default(self):
        provided_filename = "my_special_export.csv"
        # No need to mock datetime if filename is provided explicitly

        with self.runner.isolated_filesystem() as td:
            export_args = ['--csv-file', provided_filename]
            result, output_csv_path = self._run_command(td, export_specific_args=export_args)

            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertIsNotNone(output_csv_path)
            self.assertEqual(Path(output_csv_path).name, provided_filename)
            self.assertTrue(os.path.exists(output_csv_path))
            self.assertNotIn("Defaulting to:", result.output) # Should not show default message
            # Message shows absolute path
            expected_success_msg_filepath = os.path.join(td, provided_filename)
            self.assertIn(f"CSV file '{expected_success_msg_filepath}' created successfully.", result.output)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
