import csv
import os
import unittest
from unittest.mock import MagicMock
from click.testing import CliRunner
import tempfile

from fsr.reports.exports import export_csv_command
from fsr.core.data_loader import CongregationData
from fsr.core.constants import ROLE_AUXILIARY_PIONEER, ROLE_REGULAR_PIONEER, ROLE_PUBLISHER


class TestExportCsvCommandUpdated(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_cong_data = MagicMock(spec=CongregationData)
        self.mock_cong_data.publishers_list = []
        self.mock_cong_data.reports_by_publisher_month_year = {}
        self.expected_headers = [
            'Date', 'FirstName', 'LastName', 'SharedInMinistry', 'BibleStudies',
            'AP', 'Hours', 'Credit', 'Remarks'
        ]

    def _run_command(self, temp_dir_path, extra_args=None):
        csv_filename = "output.csv"
        csv_filepath = os.path.join(temp_dir_path, csv_filename)

        args = ['--csv-file', csv_filepath]
        if extra_args:
            args.extend(extra_args)

        ctx_obj = {'cong_data': self.mock_cong_data}
        result = self.runner.invoke(export_csv_command, args, obj=ctx_obj, catch_exceptions=False)

        return result, csv_filepath

    def _read_csv_data(self, csv_filepath):
        if not os.path.exists(csv_filepath):
            return None, []
        with open(csv_filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            rows = [dict(row) for row in reader]
        return fieldnames, rows

    def test_csv_creation_and_headers(self):
        """Verify CSV creation and correct headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.mock_cong_data.publishers_list = []
            self.mock_cong_data.reports_by_publisher_month_year = {}
            result, csv_filepath = self._run_command(temp_dir)

            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertTrue(os.path.exists(csv_filepath))
            fieldnames, rows = self._read_csv_data(csv_filepath)
            self.assertListEqual(list(fieldnames) if fieldnames else [], self.expected_headers)
            self.assertEqual(len(rows), 0)

    def test_month_option_removed(self):
        """Verify that using the old --month option causes an error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_filepath = os.path.join(temp_dir, "output.csv")
            result = self.runner.invoke(
                export_csv_command,
                ['--csv-file', csv_filepath, '--month', '2023-10'],
                obj={'cong_data': self.mock_cong_data},
                catch_exceptions=True
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Error: No such option: --month", result.output)

    def test_publisher_with_no_reports_at_all(self):
        """Verify output for a publisher with no reports (using lowercase name keys)."""
        self.mock_cong_data.publishers_list = [
            {'id': '1', 'firstname': 'NoReport', 'lastname': 'User'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['Date'], 'N/A')
            self.assertEqual(row['FirstName'], 'NoReport')
            self.assertEqual(row['LastName'], 'User')
            self.assertEqual(row['Remarks'], 'No reports found for this publisher')

    def test_publisher_name_key_variations(self):
        """Verify handling of missing or alternatively cased firstname/lastname keys."""
        self.mock_cong_data.publishers_list = [
            {'id': 'std_lc', 'firstname': 'John', 'lastname': 'Doe'},      # Standard lowercase (correct)
            {'id': 'no_fn', 'lastname': 'Smith'},                           # Missing 'firstname'
            {'id': 'no_ln', 'firstname': 'Jane'},                           # Missing 'lastname'
            {'id': 'camel_keys', 'firstName': 'Alice', 'lastName': 'Wonder'} # CamelCase keys only
        ]
        # Provide minimal report data or none, as focus is on name output.
        # If no reports, they get "No reports found..." remark.
        self.mock_cong_data.reports_by_publisher_month_year = {
             ('std_lc', 2023, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1, 'remarks': 'Std LC User Report'},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 4)

            def find_row_by_id_surrogate(pub_id_prefix, all_rows):
                # Since ID is not in CSV, we use known unique names or lack thereof for test.
                # This is a bit fragile but necessary without IDs in output.
                if pub_id_prefix == 'std_lc': # John Doe
                    return next((r for r in all_rows if r['FirstName'] == 'John' and r['LastName'] == 'Doe'), None)
                if pub_id_prefix == 'no_fn': # Smith, no first name
                    return next((r for r in all_rows if r['LastName'] == 'Smith' and r['FirstName'] == ''), None)
                if pub_id_prefix == 'no_ln': # Jane, no last name
                    return next((r for r in all_rows if r['FirstName'] == 'Jane' and r['LastName'] == ''), None)
                if pub_id_prefix == 'camel_keys': # Alice Wonder (names will be blank)
                    # Find the row that has blank names and is not 'no_fn' or 'no_ln'
                    for r in all_rows:
                        if r['FirstName'] == '' and r['LastName'] == '' and \
                           not (r['LastName'] == 'Smith') and \
                           not (r['FirstName'] == 'Jane'):
                           return r
                    return None
                return None

            # Standard lowercase case (has a report)
            std_lc_row = find_row_by_id_surrogate('std_lc', rows)
            self.assertIsNotNone(std_lc_row, "Standard lowercase publisher 'John Doe' not found.")
            self.assertEqual(std_lc_row['FirstName'], 'John')
            self.assertEqual(std_lc_row['LastName'], 'Doe')
            self.assertEqual(std_lc_row['Remarks'], 'Std LC User Report')

            # Missing firstname ('Smith')
            no_fn_row = find_row_by_id_surrogate('no_fn', rows)
            self.assertIsNotNone(no_fn_row, "Publisher 'Smith' (no firstname) not found.")
            self.assertEqual(no_fn_row['FirstName'], '')
            self.assertEqual(no_fn_row['LastName'], 'Smith')
            self.assertEqual(no_fn_row['Remarks'], 'No reports found for this publisher')

            # Missing lastname ('Jane')
            no_ln_row = find_row_by_id_surrogate('no_ln', rows)
            self.assertIsNotNone(no_ln_row, "Publisher 'Jane' (no lastname) not found.")
            self.assertEqual(no_ln_row['FirstName'], 'Jane')
            self.assertEqual(no_ln_row['LastName'], '')
            self.assertEqual(no_ln_row['Remarks'], 'No reports found for this publisher')

            # CamelCase keys only ('Alice Wonder' -> names should be empty)
            camel_keys_row = find_row_by_id_surrogate('camel_keys', rows)
            self.assertIsNotNone(camel_keys_row, "Publisher with camelCase keys (Alice Wonder) not found.")
            self.assertEqual(camel_keys_row['FirstName'], '') # Now expects lowercase 'firstname'
            self.assertEqual(camel_keys_row['LastName'], '')  # Now expects lowercase 'lastname'
            self.assertEqual(camel_keys_row['Remarks'], 'No reports found for this publisher')


    def test_publisher_with_multi_month_reports(self):
        """Verify output for a publisher with reports in multiple months (using lowercase name keys)."""
        self.mock_cong_data.publishers_list = [
            {'id': 'p1', 'firstname': 'MultiMonth', 'lastname': 'Reporter'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('p1', 2023, 10): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 300, 'studies': 2, 'remarks': 'Oct Report'},
            ('p1', 2023, 11): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1, 'remarks': 'Nov Report'},
            ('p1', 2023, 12): {'has_reported_field_service': False, 'pioneer': ROLE_PUBLISHER, 'remarks': 'Dec - No Service'}
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0)
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 3)
            rows.sort(key=lambda r: r['Date'])

            self.assertEqual(rows[0]['FirstName'], 'MultiMonth')
            self.assertEqual(rows[0]['LastName'], 'Reporter')
            self.assertEqual(rows[0]['Date'], '2023-10-01')
            self.assertEqual(rows[0]['AP'], 'True')
            self.assertEqual(rows[0]['Hours'], str(300 // 60))

            self.assertEqual(rows[1]['FirstName'], 'MultiMonth')
            self.assertEqual(rows[1]['Date'], '2023-11-01')
            self.assertEqual(rows[1]['Hours'], '0')


    def test_mixed_scenario_multiple_publishers(self):
        """Test with multiple publishers, mixed reports, multi-month (using lowercase name keys)."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub1', 'firstname': 'Alice', 'lastname': 'Active'},
            {'id': 'pub2', 'firstname': 'Bob', 'lastname': 'NoReports'},
            {'id': 'pub3', 'firstname': 'Charlie', 'lastname': 'Pioneer'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('pub1', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1, 'remarks': 'Alice Jan'},
            ('pub1', 2024, 2): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 2, 'remarks': 'Alice Feb'},
            ('pub3', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 120, 'studies': 3, 'remarks': 'Charlie Jan AP'},
            ('pub3', 2024, 2): {'has_reported_field_service': True, 'pioneer': ROLE_REGULAR_PIONEER, 'minutes': 420, 'studies': 4, 'remarks': 'Charlie Feb RP'}
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0)
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 5)

            alice_rows = sorted([r for r in rows if r['FirstName'] == 'Alice'], key=lambda r: r['Date'])
            bob_rows = [r for r in rows if r['FirstName'] == 'Bob'] # Should only be one
            charlie_rows = sorted([r for r in rows if r['FirstName'] == 'Charlie'], key=lambda r: r['Date'])

            self.assertEqual(len(alice_rows), 2)
            self.assertEqual(alice_rows[0]['lastname'], 'Active') # Checking consistency
            self.assertEqual(alice_rows[0]['Remarks'], 'Alice Jan')

            self.assertEqual(len(bob_rows), 1)
            self.assertEqual(bob_rows[0]['lastname'], 'NoReports')
            self.assertEqual(bob_rows[0]['Remarks'], 'No reports found for this publisher')

            self.assertEqual(len(charlie_rows), 2)
            self.assertEqual(charlie_rows[0]['lastname'], 'Pioneer')
            self.assertEqual(charlie_rows[0]['AP'], 'True')
            self.assertEqual(charlie_rows[0]['Hours'], str(120 // 60))


    def test_existing_output_file_overwritten(self):
        """Verify existing output file is overwritten (using lowercase name keys)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            self.mock_cong_data.publishers_list = [
                {'id': 'p_initial', 'firstname': 'Initial', 'lastname': 'Run'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                ('p_initial', 2023, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1}
            }
            result1, csv_filepath1 = self._run_command(temp_dir)
            self.assertEqual(result1.exit_code, 0)
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(len(rows1), 1)
            self.assertEqual(rows1[0]['FirstName'], 'Initial') # Check name from lowercase source key

            self.mock_cong_data.publishers_list = [
                {'id': 'p_overwrite', 'firstname': 'Overwritten', 'lastname': 'Run'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                 ('p_overwrite', 2023, 2): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 60}
            }
            result2, csv_filepath2 = self._run_command(temp_dir)
            self.assertEqual(result2.exit_code, 0)
            self.assertEqual(csv_filepath1, csv_filepath2)
            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(len(rows2), 1)
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten') # Check name
            self.assertEqual(rows2[0]['AP'], 'True')

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
