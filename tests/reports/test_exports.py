import csv
import os
import unittest
from unittest.mock import MagicMock
from click.testing import CliRunner
import tempfile

from fsr.reports.exports import export_csv_command
from fsr.core.data_loader import CongregationData

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

    def test_csv_creation_and_headers_if_no_publishers_with_reports(self):
        """If no publishers have reports (or no publishers at all), CSV has only headers."""
        self.mock_cong_data.publishers_list = [
            {'id': 'pub_no_reports', 'firstname': 'NoReport', 'lastname': 'User'}
        ]
        self.mock_cong_data.reports_by_publisher_month_year = {} # No reports for anyone

        with tempfile.TemporaryDirectory() as temp_dir:
            result, csv_filepath = self._run_command(temp_dir)
            self.assertEqual(result.exit_code, 0, f"Command failed: {result.output}")
            self.assertTrue(os.path.exists(csv_filepath))
            fieldnames, rows = self._read_csv_data(csv_filepath)
            self.assertListEqual(list(fieldnames) if fieldnames else [], self.expected_headers)
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
            self.assertEqual(len(rows), 1) # Only one publisher should be in the output
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
            self.assertEqual(len(rows), 4)

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
            self.assertEqual(len(rows), 8)

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
        with tempfile.TemporaryDirectory() as temp_dir:
            self.mock_cong_data.publishers_list = [{'id': 'p_init', 'firstname': 'Initial', 'lastname': 'Content'}]
            self.mock_cong_data.reports_by_publisher_month_year = {('p_init', 2023, 1): {'has_reported_field_service': True, 'minutes': 70}}
            result1, csv_filepath1 = self._run_command(temp_dir)
            self.assertEqual(result1.exit_code, 0)
            _, rows1 = self._read_csv_data(csv_filepath1)
            self.assertEqual(rows1[0]['Hours'], '1')

            self.mock_cong_data.publishers_list = [{'id': 'p_over', 'firstname': 'Overwritten', 'lastname': 'Content'}]
            self.mock_cong_data.reports_by_publisher_month_year = {('p_over', 2023, 2): {'has_reported_field_service': True, 'pioneer': 'Auxiliary', 'minutes': 120}}
            result2, csv_filepath2 = self._run_command(temp_dir)
            self.assertEqual(result2.exit_code, 0)
            _, rows2 = self._read_csv_data(csv_filepath2)
            self.assertEqual(rows2[0]['FirstName'], 'Overwritten')
            self.assertEqual(rows2[0]['Hours'], '2')


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
