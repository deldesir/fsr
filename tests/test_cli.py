import unittest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from fsr import cli as fsr_cli
from fsr.core import constants as fsr_constants

class TestCli(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch('fsr.cli.load_and_prepare_data')
    @patch('fsr.cli.find_json_file')
    def test_json_type_option_used(self, mock_find_json_file, mock_load_data):
        mock_find_json_file.return_value = "/fake/path/to/some_file.json"
        mock_load_data.return_value = MagicMock() # Dummy CongregationData object

        # Define a custom type for testing that is different from default
        custom_type_key = "custom_json"
        
        # Ensure this custom type is temporarily part of the configurable types
        # if the CLI's @click.option Choice validation is active during the test run.
        # For this test, we're mostly checking if find_json_file is *called* with the right param.
        # Click's Choice validation happens before our mock is called if not handled.
        # We can patch CONFIGURABLE_JSON_TYPES used by the @click.option decorator.
        
        test_configurable_types = {"hourglass": "hourglass-export", custom_type_key: "custom-pattern"}

        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, test_configurable_types, clear=True):
            # We need to reload the CLI module or specific functions if Click options
            # are bound at import time. Click's decorators evaluate when the module is loaded.
            # A simpler way for testing is to ensure the test choice is valid.
            # For this specific test, we directly invoke fsr_cli.cli
            
            # To make Click re-evaluate its choices, we might need to re-import or use a context manager
            # that temporarily alters the constants *before* the CLI command object is constructed/invoked.
            # Patching the module where the constant is defined is usually the way.
            # fsr.core.constants.CONFIGURABLE_JSON_TYPES is what needs patching.
            
            # Invoking a minimal command, assuming 'export field-service' exists
            # Need to ensure the command doesn't fail due to other reasons.
            # The main CLI group itself loads data, so that's what we test.
            result = self.runner.invoke(fsr_cli.cli, ['--json-type', custom_type_key, 'export', 'field-service', '--csv-file', 'dummy.csv'])

        mock_find_json_file.assert_called_once_with(json_type_key=custom_type_key)
        mock_load_data.assert_called_once_with("/fake/path/to/some_file.json")
        self.assertEqual(result.exit_code, 0, f"CLI command failed: {result.output}")


    @patch('fsr.cli.load_and_prepare_data')
    @patch('fsr.cli.find_json_file')
    def test_json_type_default_used(self, mock_find_json_file, mock_load_data):
        mock_find_json_file.return_value = "/fake/path/to/default_file.json"
        mock_load_data.return_value = MagicMock()

        # Test with default --json-type
        # The default is 'hourglass'. We need to ensure this is in CONFIGURABLE_JSON_TYPES for the Choice validation.
        test_configurable_types = {"hourglass": "hourglass-export", "other": "other-pattern"}
        
        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, test_configurable_types, clear=True), \
             patch.object(fsr_constants, 'DEFAULT_JSON_TYPE_KEY', 'hourglass'):
            
            result = self.runner.invoke(fsr_cli.cli, ['export', 'field-service', '--csv-file', 'dummy.csv']) # No --json-type

        mock_find_json_file.assert_called_once_with(json_type_key=fsr_constants.DEFAULT_JSON_TYPE_KEY)
        mock_load_data.assert_called_once_with("/fake/path/to/default_file.json")
        self.assertEqual(result.exit_code, 0, f"CLI command failed: {result.output}")

    @patch('fsr.cli.find_json_file')
    def test_json_file_not_found_error(self, mock_find_json_file):
        mock_find_json_file.return_value = None # Simulate file not found

        test_configurable_types = {"hourglass": "hourglass-export"}
        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, test_configurable_types, clear=True), \
             patch.object(fsr_constants, 'DEFAULT_JSON_TYPE_KEY', 'hourglass'):
            result = self.runner.invoke(fsr_cli.cli, ['export', 'field-service', '--csv-file', 'dummy.csv'])

        # A missing JSON is no longer fatal at the group level (docx-driven
        # program exports need no JSON); commands that DO need data emit
        # their own error instead.
        self.assertNotEqual(result.exit_code, 0, "field-service should still error without data.")
        self.assertIn("continuing without congregation data", result.output)
        self.assertIn("Congregation data not loaded", result.output)


    @patch('fsr.cli.load_and_prepare_data') # Mock load_and_prepare_data
    @patch('fsr.cli.find_json_file') # Mock find_json_file
    def test_json_file_provided_bypasses_detection(self, mock_find_json_file, mock_load_data):
        mock_load_data.return_value = MagicMock()
        
        # Create a dummy file for the --json-file option
        with self.runner.isolated_filesystem():
            with open("my_specific_file.json", "w") as f:
                f.write("{}") # Minimal valid JSON

            result = self.runner.invoke(fsr_cli.cli, ['--json-file', 'my_specific_file.json', 'export', 'field-service', '--csv-file', 'dummy.csv'])

        mock_find_json_file.assert_not_called() # find_json_file should not be called
        mock_load_data.assert_called_once_with('my_specific_file.json')
        self.assertEqual(result.exit_code, 0, f"CLI command failed: {result.output}")

    @patch('fsr.cli.load_and_prepare_data')
    @patch('fsr.cli.find_json_file')
    def test_json_type_invalid_choice_by_click(self, mock_find_json_file, mock_load_data):
        # This test verifies Click's Choice validation.
        # Our find_json_file mock won't even be called if Click rejects the choice.
        
        test_configurable_types = {"valid": "valid-pattern"}
        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, test_configurable_types, clear=True), \
             patch.object(fsr_constants, 'DEFAULT_JSON_TYPE_KEY', 'valid'):
            
            result = self.runner.invoke(fsr_cli.cli, ['--json-type', 'invalidtype', 'export', 'field-service', '--csv-file', 'dummy.csv'])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Invalid value for '--json-type'", result.output) # Click's error message
        mock_find_json_file.assert_not_called()
        mock_load_data.assert_not_called()

if __name__ == '__main__':
    unittest.main()
