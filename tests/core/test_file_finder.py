import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import List, Optional

# Modules to be tested
from fsr.core.file_finder import find_json_file
from fsr.core import constants as fsr_constants # To mock its attributes

class TestFindJsonFile(unittest.TestCase):

    def setUp(self):
        # Default mock for Path.home()
        self.mock_home_patch = patch('pathlib.Path.home')
        self.mock_home = self.mock_home_patch.start()
        self.mock_home.return_value = Path('/fake/home')

        # Mocking potential download directories
        self.mock_downloads_path = Path('/fake/home/Downloads')
        self.mock_current_dir_path = Path('.')

        # Keep track of all patches to stop them in tearDown
        self.patches = [self.mock_home_patch]

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.patches = []

    def _setup_path_mocks(self, path_instance_mock, existing_files_map=None):
        """
        Helper to configure a Path instance mock for glob, is_file, is_dir, etc.
        existing_files_map is a dict like:
        { "/path/to/dir": {"is_dir": True, "glob_results": {"pattern": [Path("file1"), Path("file2")]}} }
        """
        if existing_files_map is None:
            existing_files_map = {}

        def new_path_init(self_path, *args, **kwargs):
            # Store the path string for later use in side_effects
            self_path.path_str = str(args[0]) if args else '.'
            # Call original Path init if necessary, or just set essential attributes
            # For this mock, we mostly care about the path_str for side_effect mapping

        def is_dir_side_effect(*args, **kwargs):
            path_str = args[0].path_str if args and hasattr(args[0], 'path_str') else '.'
            return existing_files_map.get(path_str, {}).get("is_dir", False)

        def glob_side_effect(pattern):
            # self here is the Path instance
            path_str = self.path_str
            # Ensure path_str ends with a / for directory matching, or is "."
            # This part is tricky, as glob is called on a Path object representing a directory
            # Let's assume path_str is the directory glob is called upon.
            
            # Find the correct directory in existing_files_map
            # This logic might need to be more robust depending on how Path objects are created and used
            dir_glob_results = existing_files_map.get(path_str, {}).get("glob_results", {})
            
            return iter(dir_glob_results.get(pattern, []))


        def is_file_side_effect(*args, **kwargs):
            # self here is the Path instance, e.g. one of the results from glob
            path_str = self.path_str
            for dir_data in existing_files_map.values():
                for files in dir_data.get("glob_results", {}).values():
                    for file_path_obj in files:
                        if str(file_path_obj) == path_str:
                            # Check if there's specific is_file status, default True
                            return file_path_obj.custom_is_file if hasattr(file_path_obj, 'custom_is_file') else True
            return False

        path_instance_mock.is_dir.side_effect = is_dir_side_effect
        path_instance_mock.glob.side_effect = glob_side_effect
        path_instance_mock.is_file.side_effect = is_file_side_effect
        path_instance_mock.__init__.side_effect = new_path_init
        
        # Mock resolve and stat for file selection logic
        path_instance_mock.resolve.return_value = path_instance_mock # Return self for chaining
        # Each Path object returned by glob should have its own stat mock if modification times are tested.
        # This will be handled per file in existing_files_map.

    @patch('fsr.core.file_finder.Path') # Mock the Path class in file_finder module
    def test_find_json_specific_type_success(self, MockPathClass):
        
        mock_path_instance = MockPathClass.return_value # This is what Path() will return

        # Define files that exist
        file_in_downloads = Path("/fake/home/Downloads/test-export-1.json")
        file_in_downloads.stat = MagicMock(return_value=MagicMock(st_mtime=100))
        
        # Configure file system mock
        # This map represents the state of the filesystem for this test
        existing_files_map = {
            "/fake/home/Downloads": {
                "is_dir": True,
                "glob_results": {
                    "test-export-1 (*).json": [],
                    "test-export-1.json": [file_in_downloads]
                }
            },
            ".": {"is_dir": True, "glob_results": {}} # Current directory
        }
        # Apply this configuration to the mocked Path instance
        self._setup_path_mocks(MockPathClass, existing_files_map) # Pass the class to setup class-level behavior like __init__
                                                                # and instance-level via its return_value if needed.
                                                                # It's simpler if Path() always returns the same mock_path_instance for directory operations
                                                                # and glob returns new instances with specific attrs.

        # For this test, we'll simplify: Path(directory_str) returns a mock that then uses existing_files_map
        # And Path(file_str) (as returned by glob) also has its methods mocked.
        # The challenge is that Path() is called for dirs, and its glob returns Path objects for files.

        # Re-thinking _setup_path_mocks: it should mock the behavior of Path instances
        # The MockPathClass itself is what we call Path() on.
        # Path(some_dir_str) should return an object whose glob method works.
        # The results of glob should be Path objects whose is_file() and stat() methods work.

        # Simplified approach for this test:
        # Let Path() constructor return a specific mock for each directory being checked.
        # Glob results are pre-defined Path objects with their own stat.

        mock_downloads_dir_obj = MagicMock(spec=Path)
        mock_downloads_dir_obj.is_dir.return_value = True
        mock_downloads_dir_obj.glob.return_value = iter([file_in_downloads])
        mock_downloads_dir_obj.path_str = "/fake/home/Downloads" # for debugging

        mock_current_dir_obj = MagicMock(spec=Path)
        mock_current_dir_obj.is_dir.return_value = True
        mock_current_dir_obj.glob.return_value = iter([]) # No matching files in current dir
        mock_current_dir_obj.path_str = "." # for debugging

        def path_constructor_side_effect(path_arg):
            if str(path_arg) == '/fake/home/Downloads':
                return mock_downloads_dir_obj
            if str(path_arg) == '.':
                return mock_current_dir_obj
            if str(path_arg) == '/fake/home': # For Path.home()
                mock_home_dir_obj = MagicMock(spec=Path)
                mock_home_dir_obj.is_dir.return_value = True
                mock_home_dir_obj.glob.return_value = iter([])
                return mock_home_dir_obj
            # For file paths themselves, like file_in_downloads
            if str(path_arg) == str(file_in_downloads):
                 # This is tricky, Path(file_str) is not usually how we check is_file
                 # is_file is called on the Path object itself.
                 # file_in_downloads needs its own is_file, stat, resolve
                 file_in_downloads.is_file.return_value = True
                 file_in_downloads.resolve.return_value = file_in_downloads # or a version with absolute path string
                 return file_in_downloads
            
            # Default fallback
            m = MagicMock(spec=Path)
            m.is_dir.return_value = False
            m.glob.return_value = iter([])
            return m
        
        MockPathClass.side_effect = path_constructor_side_effect
        
        # Mock constants
        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, {"test_type_A": "test-export-1"}):
            result = find_json_file(json_type_key="test_type_A")

        self.assertEqual(str(result), str(file_in_downloads.resolve()))
        # Check that glob was called with the correct pattern
        mock_downloads_dir_obj.glob.assert_any_call("test-export-1 (*).json")
        mock_downloads_dir_obj.glob.assert_any_call("test-export-1.json")


    @patch('fsr.core.file_finder.Path')
    def test_find_json_default_type_hourglass(self, MockPathClass):
        mock_hourglass_file = Path("/fake/home/Downloads/hourglass-export.json")
        mock_hourglass_file.stat = MagicMock(return_value=MagicMock(st_mtime=200))
        mock_hourglass_file.is_file.return_value = True
        mock_hourglass_file.resolve.return_value = mock_hourglass_file

        mock_downloads_dir_obj = MagicMock(spec=Path)
        mock_downloads_dir_obj.is_dir.return_value = True
        # Simulate glob finding the hourglass file
        def glob_side_effect(pattern):
            if pattern == "hourglass-export.json":
                return iter([mock_hourglass_file])
            return iter([])
        mock_downloads_dir_obj.glob.side_effect = glob_side_effect
        
        mock_current_dir_obj = MagicMock(spec=Path)
        mock_current_dir_obj.is_dir.return_value = True
        mock_current_dir_obj.glob.return_value = iter([])

        def path_constructor_side_effect(path_arg):
            if str(path_arg) == '/fake/home/Downloads': return mock_downloads_dir_obj
            if str(path_arg) == '.': return mock_current_dir_obj
            if str(path_arg) == '/fake/home': 
                m = MagicMock(spec=Path); m.is_dir.return_value = True; m.glob.return_value = iter([])
                return m
            return MagicMock(spec=Path, is_dir=MagicMock(return_value=False))

        MockPathClass.side_effect = path_constructor_side_effect
        
        # DEFAULT_JSON_TYPE_KEY is "hourglass", CONFIGURABLE_JSON_TYPES has "hourglass": "hourglass-export"
        # No need to patch constants if we rely on their actual default values for this test case.
        # However, for strict unit testing, it's better to control them.
        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, {"hourglass": "hourglass-export"}, clear=True), \
             patch.object(fsr_constants, 'DEFAULT_JSON_TYPE_KEY', "hourglass"):
            result = find_json_file() # No key, should use default

        self.assertEqual(str(result), str(mock_hourglass_file.resolve()))
        mock_downloads_dir_obj.glob.assert_any_call("hourglass-export (*).json")
        mock_downloads_dir_obj.glob.assert_any_call("hourglass-export.json")


    @patch('fsr.core.file_finder.Path')
    def test_find_json_no_file_found(self, MockPathClass):
        mock_downloads_dir_obj = MagicMock(spec=Path)
        mock_downloads_dir_obj.is_dir.return_value = True
        mock_downloads_dir_obj.glob.return_value = iter([]) # No files found

        mock_current_dir_obj = MagicMock(spec=Path)
        mock_current_dir_obj.is_dir.return_value = True
        mock_current_dir_obj.glob.return_value = iter([])

        def path_constructor_side_effect(path_arg):
            if str(path_arg) == '/fake/home/Downloads': return mock_downloads_dir_obj
            if str(path_arg) == '.': return mock_current_dir_obj
            if str(path_arg) == '/fake/home':
                m = MagicMock(spec=Path); m.is_dir.return_value = True; m.glob.return_value = iter([])
                return m
            return MagicMock(spec=Path, is_dir=MagicMock(return_value=False))

        MockPathClass.side_effect = path_constructor_side_effect

        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, {"rare_type": "rare-file"}):
            result = find_json_file(json_type_key="rare_type")
        self.assertIsNone(result)

    def test_find_json_invalid_type_key(self):
        # This relies on CONFIGURABLE_JSON_TYPES not containing "invalid_key"
        original_types = fsr_constants.CONFIGURABLE_JSON_TYPES.copy()
        fsr_constants.CONFIGURABLE_JSON_TYPES = {"valid_key": "valid_pattern"}
        
        with self.assertRaisesRegex(ValueError, "Unknown JSON type key: 'invalid_key'"):
            find_json_file(json_type_key="invalid_key")
        
        # Restore original
        fsr_constants.CONFIGURABLE_JSON_TYPES = original_types


    @patch('fsr.core.file_finder.Path')
    def test_file_prioritization_logic(self, MockPathClass):
        # This tests the underlying find_data_file logic via find_json_file
        # Files: pattern (1).json (older), pattern.json (newer), pattern (2).json (newest)
        file_pattern_1_old = Path("/fake/home/Downloads/my-pattern (1).json")
        file_pattern_1_old.stat = MagicMock(return_value=MagicMock(st_mtime=100))
        file_pattern_1_old.is_file.return_value = True
        file_pattern_1_old.resolve.return_value = file_pattern_1_old

        file_pattern_no_num_new = Path("/fake/home/Downloads/my-pattern.json") # Newer than (1)
        file_pattern_no_num_new.stat = MagicMock(return_value=MagicMock(st_mtime=300))
        file_pattern_no_num_new.is_file.return_value = True
        file_pattern_no_num_new.resolve.return_value = file_pattern_no_num_new
        
        file_pattern_2_newest = Path("/fake/home/Downloads/my-pattern (2).json") # Newest, highest number
        file_pattern_2_newest.stat = MagicMock(return_value=MagicMock(st_mtime=200)) # Mod time doesn't matter if num is higher
        file_pattern_2_newest.is_file.return_value = True
        file_pattern_2_newest.resolve.return_value = file_pattern_2_newest

        mock_downloads_dir_obj = MagicMock(spec=Path)
        mock_downloads_dir_obj.is_dir.return_value = True
        # Glob for "my-pattern (*).json" should find (1) and (2)
        # Glob for "my-pattern.json" should find the no_num one
        def glob_side_effect(pattern_str):
            if pattern_str == "my-pattern (*).json":
                return iter([file_pattern_1_old, file_pattern_2_newest])
            elif pattern_str == "my-pattern.json":
                return iter([file_pattern_no_num_new])
            return iter([])
        mock_downloads_dir_obj.glob.side_effect = glob_side_effect
        
        mock_current_dir_obj = MagicMock(spec=Path); mock_current_dir_obj.is_dir.return_value = True; mock_current_dir_obj.glob.return_value = iter([])

        def path_constructor_side_effect(path_arg):
            if str(path_arg) == '/fake/home/Downloads': return mock_downloads_dir_obj
            if str(path_arg) == '.': return mock_current_dir_obj
            if str(path_arg) == '/fake/home': 
                m = MagicMock(spec=Path); m.is_dir.return_value = True; m.glob.return_value = iter([])
                return m
            # Allow individual file paths to be "constructed" to return themselves for resolve()
            # This part is a bit fragile with generic Path mocking.
            if str(path_arg) == str(file_pattern_1_old): return file_pattern_1_old
            if str(path_arg) == str(file_pattern_no_num_new): return file_pattern_no_num_new
            if str(path_arg) == str(file_pattern_2_newest): return file_pattern_2_newest
            
            return MagicMock(spec=Path, is_dir=MagicMock(return_value=False))

        MockPathClass.side_effect = path_constructor_side_effect

        with patch.dict(fsr_constants.CONFIGURABLE_JSON_TYPES, {"test_pattern": "my-pattern"}):
            result = find_json_file(json_type_key="test_pattern")
        
        self.assertEqual(str(result), str(file_pattern_2_newest.resolve()))

if __name__ == '__main__':
    unittest.main()
