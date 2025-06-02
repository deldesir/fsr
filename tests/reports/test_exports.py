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
        # This test remains the same
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
        """Publisher with no reports: Date 'N/A', other fields empty or False."""
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
            self.assertEqual(row['SharedInMinistry'], 'False')
            self.assertEqual(row['BibleStudies'], '') # Expect empty string
            self.assertEqual(row['AP'], 'False')
            self.assertEqual(row['Hours'], '')        # Expect empty string
            self.assertEqual(row['Credit'], '')       # Expect empty string
            self.assertEqual(row['Remarks'], '')      # Expect empty string (was 'No reports found...')

    def test_publisher_name_key_variations(self):
        """Verify name handling: missing keys, camelCase vs lowercase."""
        self.mock_cong_data.publishers_list = [
            {'id': 'std_lc', 'firstname': 'John', 'lastname': 'Doe'},
            {'id': 'no_fn', 'lastname': 'Smith'},
            {'id': 'no_ln', 'firstname': 'Jane'},
            {'id': 'camel_keys', 'firstName': 'Alice', 'lastName': 'Wonder'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
             ('std_lc', 2023, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 1, 'remarks': 'Std LC Report', 'minutes': 0}, # Date: 2023-01
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 4)

            def find_row_by_names(first, last, all_rows): # Simplified finder for this test
                return next((r for r in all_rows if r['FirstName'] == first and r['LastName'] == last), None)

            std_lc_row = find_row_by_names('John', 'Doe', rows)
            self.assertIsNotNone(std_lc_row)
            self.assertEqual(std_lc_row['Date'], '2023-01') # Check YYYY-MM
            self.assertEqual(std_lc_row['Remarks'], 'Std LC Report')
            self.assertEqual(std_lc_row['BibleStudies'], '1') # Has studies
            self.assertEqual(std_lc_row['Hours'], '') # 0 minutes -> empty string hours

            no_fn_row = find_row_by_names('', 'Smith', rows)
            self.assertIsNotNone(no_fn_row)
            self.assertEqual(no_fn_row['Date'], 'N/A')
            self.assertEqual(no_fn_row['Remarks'], '') # Empty remarks

            no_ln_row = find_row_by_names('Jane', '', rows)
            self.assertIsNotNone(no_ln_row)
            self.assertEqual(no_ln_row['Date'], 'N/A')
            self.assertEqual(no_ln_row['Remarks'], '')

            camel_keys_row = find_row_by_names('', '', rows) # Expect empty names
            self.assertIsNotNone(camel_keys_row)
            self.assertEqual(camel_keys_row['Date'], 'N/A')
            self.assertEqual(camel_keys_row['Remarks'], '')


    def test_publisher_with_multi_month_reports_and_field_formatting(self):
        """Test multi-month, date format, empty strings for zero/null values, and remarks."""
        self.mock_cong_data.publishers_list = [
            {'id': 'p1', 'firstname': 'MultiMonth', 'lastname': 'Tester'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            # Month 1: AP, with hours, studies, remarks, credit
            ('p1', 2023, 9): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 300, 'studies': 2, 'credithours': '5', 'remarks': 'Good month!'},
            # Month 2: Publisher, service, but 0 studies, 0 minutes, no credit, no remarks
            ('p1', 2023, 10): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'minutes': 0, 'studies': None, 'credithours': None, 'remarks': None},
            # Month 3: No field service, but has a remark
            ('p1', 2023, 11): {'has_reported_field_service': False, 'pioneer': ROLE_PUBLISHER, 'remarks': 'Took a break'},
            # Month 4: Service, <1hr minutes, some studies
            ('p1', 2023, 12): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'minutes': 50, 'studies': 1}
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 4)
            rows.sort(key=lambda r: r['Date']) # Sort by YYYY-MM date

            # Month 1 (2023-09)
            self.assertEqual(rows[0]['Date'], '2023-09')
            self.assertEqual(rows[0]['FirstName'], 'MultiMonth')
            self.assertEqual(rows[0]['SharedInMinistry'], 'True')
            self.assertEqual(rows[0]['AP'], 'True')
            self.assertEqual(rows[0]['Hours'], '5') # 300 // 60
            self.assertEqual(rows[0]['BibleStudies'], '2')
            self.assertEqual(rows[0]['Credit'], '5')
            self.assertEqual(rows[0]['Remarks'], 'Good month!')

            # Month 2 (2023-10)
            self.assertEqual(rows[1]['Date'], '2023-10')
            self.assertEqual(rows[1]['SharedInMinistry'], 'True')
            self.assertEqual(rows[1]['AP'], 'False') # Publisher
            self.assertEqual(rows[1]['Hours'], '') # 0 minutes
            self.assertEqual(rows[1]['BibleStudies'], '') # studies: None
            self.assertEqual(rows[1]['Credit'], '')   # credithours: None
            self.assertEqual(rows[1]['Remarks'], '')  # remarks: None

            # Month 3 (2023-11)
            self.assertEqual(rows[2]['Date'], '2023-11')
            self.assertEqual(rows[2]['SharedInMinistry'], 'False')
            self.assertEqual(rows[2]['AP'], 'False')
            self.assertEqual(rows[2]['Hours'], '')
            self.assertEqual(rows[2]['BibleStudies'], '')
            self.assertEqual(rows[2]['Credit'], '')
            self.assertEqual(rows[2]['Remarks'], 'Took a break') # Actual remark preserved

            # Month 4 (2023-12)
            self.assertEqual(rows[3]['Date'], '2023-12')
            self.assertEqual(rows[3]['SharedInMinistry'], 'True')
            self.assertEqual(rows[3]['AP'], 'False')
            self.assertEqual(rows[3]['Hours'], '') # 50 minutes < 1 hour
            self.assertEqual(rows[3]['BibleStudies'], '1')
            self.assertEqual(rows[3]['Credit'], '')
            self.assertEqual(rows[3]['Remarks'], '')


    def test_hours_calculation_various_scenarios(self):
        """Test revised Hours calculation for pioneers and non-pioneers."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub_A', 'firstname': 'PubA', 'lastname': 'NonPioPlentyHours'},
            {'id': 'pub_B', 'firstname': 'PubB', 'lastname': 'PioFewMinutes'},
            {'id': 'pub_C', 'firstname': 'PubC', 'lastname': 'NonPioNoService'},
            {'id': 'pub_D', 'firstname': 'PubD', 'lastname': 'PioNoMinutes'},
            {'id': 'pub_E', 'firstname': 'PubE', 'lastname': 'NonPioZeroMinutes'},
            {'id': 'pub_F', 'firstname': 'PubF', 'lastname': 'PioExactlyOneHour'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {
            ('pub_A', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'minutes': 130}, # Expect "2"
            ('pub_B', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 50}, # Expect ""
            ('pub_C', 2024, 1): {'has_reported_field_service': False, 'pioneer': ROLE_PUBLISHER, 'minutes': 120}, # Expect "" (no service)
            ('pub_D', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_REGULAR_PIONEER, 'minutes': None}, # Expect ""
            ('pub_E', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'minutes': 0}, # Expect ""
            ('pub_F', 2024, 1): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 60} # Expect "1"
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            _, rows = self._read_csv_data(csv_filepath)
            self.assertEqual(len(rows), 6)

            rows_by_name = {r['FirstName']: r for r in rows}

            self.assertEqual(rows_by_name['PubA']['Hours'], '2')
            self.assertFalse(rows_by_name['PubA']['AP'] == 'True') # AP is boolean False

            self.assertEqual(rows_by_name['PubB']['Hours'], '')
            self.assertTrue(rows_by_name['PubB']['AP'] == 'True') # AP is boolean True

            self.assertEqual(rows_by_name['PubC']['Hours'], '')
            self.assertEqual(rows_by_name['PubC']['SharedInMinistry'], 'False')

            self.assertEqual(rows_by_name['PubD']['Hours'], '')

            self.assertEqual(rows_by_name['PubE']['Hours'], '')

            self.assertEqual(rows_by_name['PubF']['Hours'], '1')
            self.assertTrue(rows_by_name['PubF']['AP'] == 'True')


    def test_existing_output_file_overwritten(self):
        # This test is more about file system interaction, less about format details here
        # but will use the new formatting.
        with tempfile.TemporaryDirectory() as temp_dir:
            self.mock_cong_data.publishers_list = [
                {'id': 'p_initial', 'firstname': 'Initial', 'lastname': 'Run'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                ('p_initial', 2023, 1): {'has_reported_field_service': True, 'pioneer': ROLE_PUBLISHER, 'studies': 0} # studies 0 -> ''
            }
            result1, csv_filepath1 = self._run_command(temp_dir)
            self.assertEqual(result1.exit_code, 0)
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(len(rows1), 1)
            self.assertEqual(rows1[0]['FirstName'], 'Initial')
            self.assertEqual(rows1[0]['BibleStudies'], '') # studies 0 -> ''
            self.assertEqual(rows1[0]['Date'], '2023-01') # YYYY-MM

            self.mock_cong_data.publishers_list = [
                {'id': 'p_overwrite', 'firstname': 'Overwritten', 'lastname': 'Run'}
            ]
            self.mock_cong_data.reports_by_publisher_month_year = {
                 ('p_overwrite', 2023, 2): {'has_reported_field_service': True, 'pioneer': ROLE_AUXILIARY_PIONEER, 'minutes': 60} # 1 hour
            }
            result2, csv_filepath2 = self._run_command(temp_dir)
            self.assertEqual(result2.exit_code, 0)
            self.assertEqual(csv_filepath1, csv_filepath2)
            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(len(rows2), 1)
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[0]['Hours'], '1') # 60 minutes -> 1 hour
            self.assertEqual(rows2[0]['Date'], '2023-02') # YYYY-MM

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
