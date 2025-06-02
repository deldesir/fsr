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
        # Initialize with empty data; tests will populate as needed
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
            # Convert to list of dicts for easier comparison
            rows = [dict(row) for row in reader]
        return fieldnames, rows

    def test_csv_creation_and_headers(self):
        """Verify CSV creation and correct headers (new order)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # No publishers, no reports = empty CSV with headers
            self.mock_cong_data.publishers_list = []
            self.mock_cong_data.reports_by_publisher_month_year = {}
            result, csv_filepath = self._run_command(temp_dir)

            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertTrue(os.path.exists(csv_filepath))

            fieldnames, rows = self._read_csv_data(csv_filepath)
            self.assertListEqual(list(fieldnames) if fieldnames else [], self.expected_headers)
            self.assertEqual(len(rows), 0) # No data rows if no publishers

    def test_month_option_removed(self):
        """Verify that using the old --month option causes an error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_filepath = os.path.join(temp_dir, "output.csv")
            # Use catch_exceptions=True because we expect a Click exception (NoSuchOption)
            result = self.runner.invoke(
                export_csv_command,
                ['--csv-file', csv_filepath, '--month', '2023-10'],
                obj={'cong_data': self.mock_cong_data},
                catch_exceptions=True # Important for testing Click argument errors
            )
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("Error: No such option: --month", result.output)


    def test_publisher_with_no_reports_at_all(self):
        """Verify output for a publisher with no reports in any month."""
        self.mock_cong_data.publishers_list = [
            {'id': '1', 'firstName': 'NoReport', 'lastName': 'User'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {} # Empty reports

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row['Date'], 'N/A')
            self.assertEqual(row['FirstName'], 'NoReport')
            self.assertEqual(row['LastName'], 'User')
            self.assertEqual(row['SharedInMinistry'], 'False')
            self.assertEqual(row['BibleStudies'], '0')
            self.assertEqual(row['AP'], 'False')
            self.assertEqual(row['Hours'], '0')
            self.assertEqual(row['Credit'], '')
            self.assertEqual(row['Remarks'], 'No reports found for this publisher')

    def test_publisher_with_multi_month_reports(self):
        """Verify output for a publisher with reports in multiple months."""
        self.mock_cong_data.publishers_list = [
            {'id': 'p1', 'firstName': 'MultiMonth', 'lastName': 'Reporter'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('p1', 2023, 10): {
                'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER,
                'minutes': 300, 'studies': 2, 'remarks': 'Oct Report'
            },
            ('p1', 2023, 11): {
                'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER,
                'studies': 1, 'remarks': 'Nov Report'
            },
            ('p1', 2023, 12): { # No field service this month
                'has_reported_field_service': False, 'pioneer': ROLE_PUBLISHER,
                'remarks': 'Dec - No Service'
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 3) # One row per report

            # Sort rows by date for consistent checking
            rows.sort(key=lambda r: r['Date'])

            # Oct Report (AP)
            self.assertEqual(rows[0]['Date'], '2023-10-01')
            self.assertEqual(rows[0]['FirstName'], 'MultiMonth')
            self.assertEqual(rows[0]['SharedInMinistry'], 'True')
            self.assertEqual(rows[0]['AP'], 'True')
            self.assertEqual(rows[0]['Hours'], str(300 // 60)) # 5 hours
            self.assertEqual(rows[0]['BibleStudies'], '2')
            self.assertEqual(rows[0]['Remarks'], 'Oct Report')

            # Nov Report (Publisher)
            self.assertEqual(rows[1]['Date'], '2023-11-01')
            self.assertEqual(rows[1]['SharedInMinistry'], 'True')
            self.assertEqual(rows[1]['AP'], 'False')
            self.assertEqual(rows[1]['Hours'], '0') # Publisher, so hours are 0
            self.assertEqual(rows[1]['BibleStudies'], '1')
            self.assertEqual(rows[1]['Remarks'], 'Nov Report')

            # Dec Report (No field service)
            self.assertEqual(rows[2]['Date'], '2023-12-01')
            self.assertEqual(rows[2]['SharedInMinistry'], 'False')
            self.assertEqual(rows[2]['AP'], 'False')
            self.assertEqual(rows[2]['Hours'], '0')
            self.assertEqual(rows[2]['BibleStudies'], '0')
            self.assertEqual(rows[2]['Remarks'], 'Did not report field service')


    def test_mixed_scenario_multiple_publishers(self):
        """Test with multiple publishers, mixed report statuses, and multi-month data."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub1', 'firstName': 'Alice', 'lastName': 'Active'},
            {'id': 'pub2', 'firstName': 'Bob', 'lastName': 'NoReports'},
            {'id': 'pub3', 'firstName': 'Charlie', 'lastName': 'Pioneer'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            # Alice: two months of reports
            ('pub1', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1, 'remarks': 'Alice Jan'},
            ('pub1', 2024, 2): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 2, 'remarks': 'Alice Feb'},
            # Bob: no reports (will be handled by the 'No reports found' logic)
            # Charlie: one month as AP, one as RP
            ('pub3', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 120, 'studies': 3, 'remarks': 'Charlie Jan AP'},
            ('pub3', 2024, 2): {'has_reported_field_service': True, 'pioneer': ROLE_REGULAR_PIONEER, 'minutes': 420, 'studies': 4, 'remarks': 'Charlie Feb RP'}
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")

            _, rows = self._read_csv_data(csv_filepath)
            # Expected rows: Alice (2) + Bob (1) + Charlie (2) = 5 rows
            self.assertEqual(len(rows), 5)

            # For easier checking, filter rows by publisher and sort by date if needed
            alice_rows = sorted([r for r in rows if r['FirstName'] == 'Alice'], key=lambda r: r['Date'])
            bob_rows = [r for r in rows if r['FirstName'] == 'Bob']
            charlie_rows = sorted([r for r in rows if r['FirstName'] == 'Charlie'], key=lambda r: r['Date'])

            self.assertEqual(len(alice_rows), 2)
            self.assertEqual(alice_rows[0]['Date'], '2024-01-01')
            self.assertEqual(alice_rows[0]['Remarks'], 'Alice Jan')
            self.assertEqual(alice_rows[1]['Date'], '2024-02-01')
            self.assertEqual(alice_rows[1]['Remarks'], 'Alice Feb')

            self.assertEqual(len(bob_rows), 1)
            self.assertEqual(bob_rows[0]['Date'], 'N/A')
            self.assertEqual(bob_rows[0]['Remarks'], 'No reports found for this publisher')
            self.assertEqual(bob_rows[0]['SharedInMinistry'], 'False')

            self.assertEqual(len(charlie_rows), 2)
            self.assertEqual(charlie_rows[0]['Date'], '2024-01-01')
            self.assertEqual(charlie_rows[0]['AP'], 'True')
            self.assertEqual(charlie_rows[0]['Hours'], str(120 // 60))
            self.assertEqual(charlie_rows[0]['Remarks'], 'Charlie Jan AP')
            self.assertEqual(charlie_rows[1]['Date'], '2024-02-01')
            self.assertEqual(charlie_rows[1]['AP'], 'False') # Regular Pioneer
            self.assertEqual(charlie_rows[1]['Hours'], str(420 // 60))
            self.assertEqual(charlie_rows[1]['Remarks'], 'Charlie Feb RP')

    def test_existing_output_file_overwritten(self):
        """Verify that an existing output CSV file is overwritten (multi-month context)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First run: create the file with some data
            self.mock_cong_data.publishers_list = [
                {'id': 'p_initial', 'firstName': 'Initial', 'lastName': 'Run'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                ('p_initial', 2023, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1}
            }
            result1, csv_filepath1 = self._run_command(temp_dir)
            self.assertEqual(result1.exit_code, 0, f"Initial run failed: {result1.output}")
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(len(rows1), 1)
            self.assertEqual(rows1[0]['FirstName'], 'Initial')

            # Second run: overwrite with new data
            self.mock_cong_data.publishers_list = [
                {'id': 'p_overwrite', 'firstName': 'Overwritten', 'lastName': 'Run'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                 ('p_overwrite', 2023, 2): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 60},
                 ('p_overwrite', 2023, 3): {'has_reported_field_service': False, 'pioneer': ROLE_PUBLISHER}
            }
            result2, csv_filepath2 = self._run_command(temp_dir) # Uses the same "output.csv"
            self.assertEqual(result2.exit_code, 0, f"Overwrite run failed: {result2.output}")
            self.assertEqual(csv_filepath1, csv_filepath2)

            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(len(rows2), 2) # Two rows for p_overwrite's reports

            # Sort by date to check specific rows if necessary
            rows2.sort(key=lambda r: r['Date'])
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[0]['Date'], '2023-02-01')
            self.assertEqual(rows2[0]['AP'], 'True')
            self.assertEqual(rows2[0]['Hours'], '1')

            self.assertEqual(rows2[1]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[1]['Date'], '2023-03-01')
            self.assertEqual(rows2[1]['SharedInMinistry'], 'False')


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
