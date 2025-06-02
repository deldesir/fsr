import os
import re
from pathlib import Path
from typing import List, Optional, Union

def find_data_file(default_name_parts: List[str], extensions: List[str], default_dirs: List[str]) -> Optional[str]:
    """
    Searches for a data file in specified directories based on name parts and extensions.

    The function searches for files matching the pattern "name_part (x).ext" or "name_part.ext".
    If multiple files are found, it prioritizes files with the highest number in (x).
    Among those with the highest number, the most recently modified file is chosen.
    If no numbered files exist, the most recently modified non-numbered file is selected.

    Args:
        default_name_parts: A list of core parts of the filename.
        extensions: A list of extensions to search for.
        default_dirs: A list of directories to search in.

    Returns:
        The absolute path to the selected file as a string, or None if no suitable file is found.
    """
    candidate_files = []

    for current_dir in default_dirs:
        p_dir = Path(current_dir)
        if not p_dir.is_dir():
            continue

        for name_part in default_name_parts:
            for ext in extensions:
                # Search for files with pattern "name_part (x).ext"
                for f_path in p_dir.glob(f"{name_part} (*).{ext}"):
                    if f_path.is_file():
                        candidate_files.append(f_path)

                # Search for files with pattern "name_part.ext"
                for f_path in p_dir.glob(f"{name_part}.{ext}"):
                    if f_path.is_file():
                        candidate_files.append(f_path)

    if not candidate_files:
        return None

    latest_file = None
    max_num = -1
    latest_mod_time = 0

    # Regex to extract number from "name_part (x).ext"
    # It should handle cases like "file (1).json", "file (12).json", etc.
    # It also needs to handle cases where there is no number, like "file.json"
    regex = re.compile(r"\((\d+)\)\.")

    numbered_files = []
    non_numbered_files = []

    for f_path in candidate_files:
        match = regex.search(f_path.name)
        if match:
            num = int(match.group(1))
            numbered_files.append((f_path, num))
        else:
            non_numbered_files.append(f_path)

    if numbered_files:
        # Sort by number (descending) then by modification time (descending)
        numbered_files.sort(key=lambda x: (x[1], x[0].stat().st_mtime), reverse=True)

        # The file with the highest number and most recent modification time
        # will be the first element after sorting.
        # We need to find all files with the max_num and then pick the most recent one.

        highest_num = numbered_files[0][1]

        # Filter for files with the highest number
        top_numbered_files = [f for f in numbered_files if f[1] == highest_num]

        # Sort these by modification time (descending)
        top_numbered_files.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)

        latest_file = top_numbered_files[0][0]

    if non_numbered_files:
        # Sort by modification time (descending)
        non_numbered_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # If no numbered file was found, or if the most recent non-numbered is newer
        # than the chosen numbered one (this case should not happen if logic is correct,
        # but as a fallback)
        if latest_file is None:
            latest_file = non_numbered_files[0]
        else:
            # If a numbered file was selected, compare its modification time with the most recent non-numbered file
            # This handles the case where "file.json" might be newer than "file (0).json"
            # However, the problem asks to prioritize highest number first.
            # So, if a numbered file exists (e.g. file (1).json), it should be preferred over file.json,
            # unless file.json is more recent AND there are no numbered files with a higher number.
            # The current logic for numbered files already picks the highest number and then most recent.
            # So, we only consider non-numbered if no numbered files were found at all.
            pass


    return str(latest_file.resolve()) if latest_file else None


def find_json_file() -> Optional[str]:
    """
    Finds a JSON file, typically an Hourglass export.

    Searches for "hourglass-export.json" or "hourglass-export (x).json"
    in the current directory and the user's Downloads folder.

    Returns:
        The absolute path to the selected JSON file, or None if not found.
    """
    home_dir = Path.home()
    # Common directory names for Downloads, case-insensitive
    download_dirs_names = ["Downloads", "downloads", "Téléchargements", "téléchargements"]

    potential_dirs = [".", str(home_dir)]
    for name in download_dirs_names:
        potential_dirs.append(str(home_dir / name))

    # Filter out directories that don't exist
    default_dirs = [d for d in potential_dirs if Path(d).is_dir()]

    # If no specific download directory was found, ensure at least home and current dir are there
    if not any(Path.home() / name in [Path(d) for d in default_dirs] for name in download_dirs_names):
         # This check is a bit redundant given the construction, but ensures Downloads is prioritized if found
        pass # The list `default_dirs` will contain existing directories from `potential_dirs`

    if not default_dirs: # Fallback if somehow even "." and home are not dirs (highly unlikely)
        default_dirs = ["."]


    return find_data_file(
        default_name_parts=["hourglass-export"],
        extensions=["json"],
        default_dirs=default_dirs
    )


def find_csv_file() -> Optional[str]:
    """
    Finds a CSV file, typically a "Descahos Rapò Sèvis" or "FSGExtract" export.

    Searches for "Descahos Rapò Sèvis.csv", "Descahos Rapò Sèvis (x).csv",
    "FSGExtract.csv", or "FSGExtract (x).csv" in the current directory
    and the user's Downloads folder.

    Returns:
        The absolute path to the selected CSV file, or None if not found.
    """
    home_dir = Path.home()
    download_dirs_names = ["Downloads", "downloads", "Téléchargements", "téléchargements"]

    potential_dirs = [".", str(home_dir)]
    for name in download_dirs_names:
        potential_dirs.append(str(home_dir / name))

    default_dirs = [d for d in potential_dirs if Path(d).is_dir()]

    if not default_dirs:
        default_dirs = ["."]

    return find_data_file(
        default_name_parts=["Descahos Rapò Sèvis", "FSGExtract"],
        extensions=["csv"],
        default_dirs=default_dirs
    )
