import csv
import os
import unittest
from unittest.mock import MagicMock
from click.testing import CliRunner
import tempfile

from fsr.reports.exports import export_csv_command
from fsr.core.data_loader import CongregationData
# ROLE_AUXILIARY_PIONEER, ROLE_REGULAR_PIONEER, ROLE_PUBLISHER are not directly used by tests
# but are good for context when creating mock data for 'pioneer' field.
# Actual 'AP' column logic relies on 'pioneer' string value being 'Auxiliary'.

class TestExportCsvCommandFullyUpdated(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_cong_data = MagicMock(spec=CongregationData)
        self.mock_cong_data.publishers_list = []
        self.mock_cong_data.reports_by_publisher_month_year = {}
        self.expected_headers = [
            'Date', 'FirstName', 'LastName', 'SharedInMinistry', 'BibleStudies',
            'AP', 'Hours', 'Credit', 'Remarks'
        ]

    def _run_command(self, temp_dir_path):
        csv_filename = "output.csv"
        csv_filepath = os.path.join(temp_dir_path, csv_filename)
        args = ['--csv-file', csv_filepath]
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
            self.mock_cong_data.publishers_list = [] # No publishers
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertTrue(os.path.exists(csv_filepath))
            fieldnames, rows = self._read_csv_data(csv_filepath)
            self.assertListEqual(list(fieldnames) if fieldnames else [], self.expected_headers)
            self.assertEqual(len(rows), 0)

    def test_publisher_with_no_reports_at_all(self):
        """Publisher with no reports: Date 'N/A', specific fields empty or False."""
        self.mock_cong_data.publishers_list = [
            {'id': '1', 'firstname': 'NoReport', 'lastname': 'User'}
        ]
        # reports_by_publisher_month_year remains empty
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
            self.assertEqual(row['BibleStudies'], '')
            self.assertEqual(row['AP'], 'False')
            self.assertEqual(row['Hours'], '')
            self.assertEqual(row['Credit'], '')
            self.assertEqual(row['Remarks'], '') # Remarks also empty now

    def test_comprehensive_field_logic_multi_publisher_multi_month(self):
        """Comprehensive test for all field logic across multiple publishers and months."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub1', 'firstname': 'Alice', 'lastname': 'AuxPioneer'},
            {'id': 'pub2', 'firstname': 'Bob', 'lastname': 'Publisher'},
            {'id': 'pub3', 'firstname': 'Charlie', 'lastname': 'Irregular'},
            {'id': 'pub4', 'firstname': 'David', 'lastname': 'SpecialPio'},
            {'id': 'pub5', 'firstname': 'Eve', 'lastname': 'FloaterCredit'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            # Alice (Auxiliary Pioneer)
            ('pub1', 2023, 9): {'pioneer': 'Auxiliary', 'has_reported_field_service': True, 'minutes': 300, 'studies': 2, 'remarks': 'Full month AP'}, # 5 hours
            ('pub1', 2023, 10): {'pioneer': 'Auxiliary', 'has_reported_field_service': True, 'minutes': 50}, # <1 hour

            # Bob (Publisher)
            ('pub2', 2023, 9): {'pioneer': None, 'has_reported_field_service': True, 'minutes': 130, 'studies': 1, 'credithours': 0}, # 2 hours, credit 0 -> ''
            ('pub2', 2023, 10): {'pioneer': 'Publisher', 'has_reported_field_service': False, 'remarks': '  Sick leave  '}, # No service, but has remark

            # Charlie (Irregular - one month service, one month no report data for this pub, should get N/A line)
            # Note: Charlie won't have a specific N/A line if other reports exist for them.
            # This test structure means we define reports. If a month is missing, no line for that month.
            # The "N/A" line is for publishers with *NO* reports at all.
            ('pub3', 2023, 9): {'pioneer': None, 'has_reported_field_service': True, 'studies': 0, 'credithours': 'NonNumeric'}, # studies 0 -> '', credit non-numeric -> ''

            # David (Special Pioneer)
            ('pub4', 2023, 9): {'pioneer': 'Special', 'has_reported_field_service': True, 'minutes': 0, 'remarks': 'Special Pioneer Report'}, # minutes 0 -> ''

            # Eve (Credit checks)
            ('pub5', 2023, 9): {'pioneer': None, 'has_reported_field_service': True, 'credithours': 10.0, 'studies': 3}, # Credit 10.0 -> "10"
            ('pub5', 2023, 10): {'pioneer': None, 'has_reported_field_service': True, 'credithours': "7.5", 'studies': 2}, # Credit "7.5" -> "7.5"
            ('pub5', 2023, 11): {'pioneer': None, 'has_reported_field_service': True, 'credithours': None, 'studies': 1}, # Credit None -> ""
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)

            # Expected rows: pub1 (2), pub2 (2), pub3 (1), pub4 (1), pub5 (3) = 9 rows
            self.assertEqual(len(rows), 9)

            # Helper to find rows for a publisher and sort by date
            def get_pub_rows(firstname, all_rows):
                return sorted([r for r in all_rows if r['FirstName'] == firstname], key=lambda r: r['Date'])

            # Alice - Auxiliary Pioneer
            alice_rows = get_pub_rows('Alice', rows)
            self.assertEqual(len(alice_rows), 2)
            self.assertEqual(alice_rows[0]['Date'], '2023-09')
            self.assertEqual(alice_rows[0]['AP'], 'True')
            self.assertEqual(alice_rows[0]['Hours'], '5')
            self.assertEqual(alice_rows[0]['BibleStudies'], '2')
            self.assertEqual(alice_rows[0]['Remarks'], 'Full month AP')
            self.assertEqual(alice_rows[1]['Date'], '2023-10')
            self.assertEqual(alice_rows[1]['AP'], 'True')
            self.assertEqual(alice_rows[1]['Hours'], '') # 50 minutes

            # Bob - Publisher
            bob_rows = get_pub_rows('Bob', rows)
            self.assertEqual(len(bob_rows), 2)
            self.assertEqual(bob_rows[0]['Date'], '2023-09')
            self.assertEqual(bob_rows[0]['AP'], 'False')
            self.assertEqual(bob_rows[0]['Hours'], '2') # 130 minutes
            self.assertEqual(bob_rows[0]['BibleStudies'], '1')
            self.assertEqual(bob_rows[0]['Credit'], '') # Credit 0
            self.assertEqual(bob_rows[1]['Date'], '2023-10')
            self.assertEqual(bob_rows[1]['SharedInMinistry'], 'False')
            self.assertEqual(bob_rows[1]['AP'], 'False')
            self.assertEqual(bob_rows[1]['Hours'], '')
            self.assertEqual(bob_rows[1]['BibleStudies'], '')
            self.assertEqual(bob_rows[1]['Remarks'], 'Sick leave') # Trimmed

            # Charlie - Irregular
            charlie_rows = get_pub_rows('Charlie', rows)
            self.assertEqual(len(charlie_rows), 1)
            self.assertEqual(charlie_rows[0]['Date'], '2023-09')
            self.assertEqual(charlie_rows[0]['AP'], 'False')
            self.assertEqual(charlie_rows[0]['BibleStudies'], '') # studies 0
            self.assertEqual(charlie_rows[0]['Credit'], '')     # credit non-numeric

            # David - Special Pioneer
            david_rows = get_pub_rows('David', rows)
            self.assertEqual(len(david_rows), 1)
            self.assertEqual(david_rows[0]['Date'], '2023-09')
            self.assertEqual(david_rows[0]['AP'], 'False') # Not 'Auxiliary'
            self.assertEqual(david_rows[0]['Hours'], '') # minutes 0
            self.assertEqual(david_rows[0]['Remarks'], 'Special Pioneer Report')

            # Eve - Credit checks
            eve_rows = get_pub_rows('Eve', rows)
            self.assertEqual(len(eve_rows), 3)
            self.assertEqual(eve_rows[0]['Date'], '2023-09')
            self.assertEqual(eve_rows[0]['Credit'], '10') # 10.0 -> "10"
            self.assertEqual(eve_rows[0]['BibleStudies'], '3')
            self.assertEqual(eve_rows[1]['Date'], '2023-10')
            self.assertEqual(eve_rows[1]['Credit'], '7.5') # "7.5" -> "7.5"
            self.assertEqual(eve_rows[1]['BibleStudies'], '2')
            self.assertEqual(eve_rows[2]['Date'], '2023-11')
            self.assertEqual(eve_rows[2]['Credit'], '') # None -> ""
            self.assertEqual(eve_rows[2]['BibleStudies'], '1')

    # Simplified test_existing_output_file_overwritten as detailed checks are above
    def test_existing_output_file_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            self.mock_cong_data.publishers_list = [{'id': 'p1', 'firstname': 'Initial', 'lastname': 'Content'}]
            self.mock_cong_data.reports_by_publisher_month_year = {('p1', 2023, 1): {'has_reported_field_service': True, 'minutes': 70}}
            result1, csv_filepath1 = self._run_command(temp_dir)
            self.assertEqual(result1.exit_code, 0)
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(rows1[0]['FirstName'], 'Initial')
            self.assertEqual(rows1[0]['Hours'], '1')
            self.assertEqual(rows1[0]['Date'], '2023-01')

            self.mock_cong_data.publishers_list = [{'id': 'p2', 'firstname': 'Overwritten', 'lastname': 'Content'}]
            self.mock_cong_data.reports_by_publisher_month_year = {('p2', 2023, 2): {'has_reported_field_service': True, 'pioneer': 'Auxiliary', 'minutes': 120}}
            result2, csv_filepath2 = self._run_command(temp_dir) # same filename output.csv
            self.assertEqual(result2.exit_code, 0)
            self.assertEqual(csv_filepath1, csv_filepath2)
            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[0]['AP'], 'True')
            self.assertEqual(rows2[0]['Hours'], '2')
            self.assertEqual(rows2[0]['Date'], '2023-02')

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
