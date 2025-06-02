import csv
import os
import unittest
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
import tempfile

from fsr.reports.exports import export_csv_command
from fsr.core.data_loader import CongregationData
from fsr.core.constants import ROLE_AUXILIARY_PIONEER, ROLE_REGULAR_PIONEER, ROLE_PUBLISHER


class TestExportCsvCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_cong_data = MagicMock(spec=CongregationData)
        self.mock_cong_data.publishers_list = []
        self.mock_cong_data.reports_by_publisher_month_year = {}

    def _run_command(self, temp_dir_path, month_str="2023-10", extra_args=None):
        csv_filename = "output.csv"
        csv_filepath = os.path.join(temp_dir_path, csv_filename)

        args = [
            '--csv-file', csv_filepath,
            '--month', month_str,
        ]
        if extra_args:
            args.extend(extra_args)

        # Mock the context object that Click passes
        ctx_obj = {'cong_data': self.mock_cong_data}

        # The command is part of a group, but we can test it directly if we don't rely on group context
        # However, the command itself uses ctx.obj, so we need to ensure that's available.
        # CliRunner's invoke can pass obj to the command context.
        result = self.runner.invoke(export_csv_command, args, obj=ctx_obj, catch_exceptions=False)

        return result, csv_filepath

    def _read_csv_data(self, csv_filepath):
        if not os.path.exists(csv_filepath):
            return None, []
        with open(csv_filepath, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            rows = list(reader)
        return fieldnames, rows

    def test_csv_creation_and_headers(self):
        """Verify CSV creation and correct headers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertTrue(os.path.exists(csv_filepath))

            fieldnames, _ = self._read_csv_data(csv_filepath)
            expected_headers = ['FirstName', 'LastName', 'Date', 'SharedInMinistry', 'AP', 'Hours', 'BibleStudies', 'Credit', 'Remarks']
            self.assertListEqual(fieldnames, expected_headers)

    def test_data_population_publisher_with_report(self):
        """Verify data for a publisher with a full report."""
        self.mock_cong_data.publishers_list = [
            {'id': '1', 'firstName': 'John', 'lastName': 'Doe'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('1', 2023, 10): {
                'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER,
                'minutes': 300, 'studies': 2, 'credithours': '5', 'remarks': 'Good month'
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['FirstName'], 'John')
            self.assertEqual(row['LastName'], 'Doe')
            self.assertEqual(row['Date'], '2023-10-01')
            self.assertEqual(row['SharedInMinistry'], 'True') # CSV reads bools as strings
            self.assertEqual(row['AP'], 'True')
            self.assertEqual(row['Hours'], str(300 // 60)) # 5 hours
            self.assertEqual(row['BibleStudies'], '2')
            self.assertEqual(row['Credit'], '5')
            self.assertEqual(row['Remarks'], 'Good month')

    def test_data_population_publisher_without_report(self):
        """Verify data for a publisher with no report."""
        self.mock_cong_data.publishers_list = [
            {'id': '2', 'firstName': 'Jane', 'lastName': 'Smith'}
        ]
        # No entry in reports_by_publisher_month_year for publisher '2'
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['FirstName'], 'Jane')
            self.assertEqual(row['LastName'], 'Smith')
            self.assertEqual(row['Date'], '2023-10-01')
            self.assertEqual(row['SharedInMinistry'], 'False')
            self.assertEqual(row['AP'], 'False')
            self.assertEqual(row['Hours'], '0')
            self.assertEqual(row['BibleStudies'], '0')
            self.assertEqual(row['Credit'], '')
            self.assertEqual(row['Remarks'], 'No report found for this month')

    def test_data_population_no_field_service(self):
        """Verify data for a publisher with a report but no field service."""
        self.mock_cong_data.publishers_list = [
            {'id': '3', 'firstName': 'Jim', 'lastName': 'Brown'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('3', 2023, 10): {'has_reported_field_service': False, 'pioneer': ROLE_PUBLISHER, 'remarks': 'Inactive'}
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['SharedInMinistry'], 'False')
            self.assertEqual(row['AP'], 'False')
            self.assertEqual(row['Hours'], '0')
            self.assertEqual(row['BibleStudies'], '0')
            self.assertEqual(row['Credit'], '')
            self.assertEqual(row['Remarks'], 'Did not report field service') # Specific remark from command

    def test_pioneer_hours_calculation_auxiliary(self):
        """Verify hours for an Auxiliary Pioneer."""
        self.mock_cong_data.publishers_list = [
            {'id': '4', 'firstName': 'Sarah', 'lastName': 'Connor', 'role': ROLE_AUXILIARY_PIONEER}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('4', 2023, 10): {
                'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER,
                'minutes': 120, 'studies': 1
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(rows[0]['Hours'], str(120 // 60)) # 2 hours
            self.assertEqual(rows[0]['AP'], 'True')

    def test_pioneer_hours_calculation_regular(self):
        """Verify hours for a Regular Pioneer."""
        self.mock_cong_data.publishers_list = [
            {'id': '5', 'firstName': 'Kyle', 'lastName': 'Reese', 'role': ROLE_REGULAR_PIONEER}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('5', 2023, 10): {
                'has_reported_field_service': True, 'pioneer': ROLE_REGULAR_PIONEER,
                'minutes': 420, 'studies': 3
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(rows[0]['Hours'], str(420 // 60)) # 7 hours
            self.assertEqual(rows[0]['AP'], 'False') # Regular pioneer is not AP

    def test_non_pioneer_hours(self):
        """Verify hours for a non-pioneer (Publisher) is 0 even if minutes reported."""
        self.mock_cong_data.publishers_list = [
            {'id': '6', 'firstName': 'Miles', 'lastName': 'Dyson', 'role': ROLE_PUBLISHER}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('6', 2023, 10): {
                'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, # Explicitly publisher
                'minutes': 60, 'studies': 1 # Reported minutes, but not a pioneer
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(rows[0]['Hours'], '0')
            self.assertEqual(rows[0]['AP'], 'False')

    def test_multiple_publishers(self):
        """Test with multiple publishers."""
        self.mock_cong_data.publishers_list = [
            {'id': '10', 'firstName': 'Pub', 'lastName': 'One'},
            {'id': '11', 'firstName': 'Pub', 'lastName': 'Two (No Report)'},
            {'id': '12', 'firstName': 'Pio', 'lastName': 'Three (AP)'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('10', 2023, 11): {
                'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER,
                'minutes': 0, 'studies': 1, 'remarks': 'Active'
            },
            ('12', 2023, 11): {
                'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER,
                'minutes': 180, 'studies': 2
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir, month_str="2023-11")
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 3)

            # Pub One
            self.assertEqual(rows[0]['FirstName'], 'Pub')
            self.assertEqual(rows[0]['LastName'], 'One')
            self.assertEqual(rows[0]['SharedInMinistry'], 'True')
            self.assertEqual(rows[0]['Hours'], '0') # Publisher hours are 0
            self.assertEqual(rows[0]['Remarks'], 'Active')

            # Pub Two
            self.assertEqual(rows[1]['FirstName'], 'Pub')
            self.assertEqual(rows[1]['LastName'], 'Two (No Report)')
            self.assertEqual(rows[1]['SharedInMinistry'], 'False')
            self.assertEqual(rows[1]['Remarks'], 'No report found for this month')

            # Pio Three
            self.assertEqual(rows[2]['FirstName'], 'Pio')
            self.assertEqual(rows[2]['LastName'], 'Three (AP)')
            self.assertEqual(rows[2]['SharedInMinistry'], 'True')
            self.assertEqual(rows[2]['AP'], 'True')
            self.assertEqual(rows[2]['Hours'], str(180 // 60)) # 3 hours

    def test_existing_output_file_overwritten(self):
        """Verify that an existing output CSV file is overwritten."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First run: create the file
            self.mock_cong_data.publishers_list = [
                {'id': '20', 'firstName': 'Initial', 'lastName': 'Content'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                ('20', 2023, 10): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1}
            }
            result1, csv_filepath1 = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result1.exit_code, 0)
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(len(rows1), 1)
            self.assertEqual(rows1[0]['FirstName'], 'Initial')

            # Second run: overwrite with new data
            self.mock_cong_data.publishers_list = [
                {'id': '21', 'firstName': 'Overwritten', 'lastName': 'Content'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                 ('21', 2023, 10): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 60}
            }
            # Ensure we use the same csv_filepath for the second call by not generating a new name
            # The _run_command helper uses a fixed name "output.csv" within the temp_dir
            result2, csv_filepath2 = self._run_command(temp_dir, month_str="2023-10")
            self.assertEqual(result2.exit_code, 0, f"Command failed: {result2.output}")
            self.assertEqual(csv_filepath1, csv_filepath2) # Ensure it's the same file path

            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(len(rows2), 1)
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[0]['AP'], 'True')
            self.assertEqual(rows2[0]['Hours'], '1')

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

# To ensure tests can be discovered and run, we might need __init__.py in tests/reports
# and potentially adjust sys.path if fsr module is not found.
# For now, assuming standard project structure where 'fsr' is discoverable.
# The CliRunner will invoke the command in a way that it should find its own modules.

# A note on ROLE_PUBLISHER in mock_cong_data.publishers_list:
# The actual `publisher` dict from `cong_data.publishers_list` might not have a 'role' key.
# The `get_publisher_role` function in `exports.py` derives role from the `pioneer` field
# in the *report* data. My mock setup for `reports_by_publisher_month_year` includes `pioneer`
# which is what `get_publisher_role` uses. So, adding 'role' to publisher_list items
# in the mock is for test clarity/documentation but isn't strictly used by the command for role determination.
# The key is `report.get('pioneer')`.
