"""
Handles loading and preparation of congregation data from a JSON file.
"""
import json

class CongregationData:
    """
    A container for loaded and processed congregation data.

    Attributes:
        congregation_info (dict): Information about the congregation.
        publishers_list (list): A list of publisher data objects (dictionaries).
        reports_list (list): A list of report data objects (dictionaries).
        publishers_by_id (dict): Publisher objects keyed by their 'id'.
        publishers_by_name (dict): Publisher objects keyed by (firstname.lower(), lastname.lower()).
        reports_by_publisher_month_year (dict): Report objects keyed by (publisher_id, year, month).
    """
    def __init__(self):
        self.congregation_info: dict = {}
        self.publishers_list: list = []
        self.reports_list: list = []
        self.publishers_by_id: dict = {}
        self.publishers_by_name: dict = {}
        self.reports_by_publisher_month_year: dict = {}
        self.monthly_attendance_weekend_avg: dict = {}


def load_and_prepare_data(json_file_path: str) -> CongregationData | None:
    """
    Loads congregation data from a JSON file, processes it, and populates lookup structures.

    Args:
        json_file_path: The path to the JSON data file.

    Returns:
        A CongregationData instance populated with data from the JSON file,
        or None if file reading or JSON parsing fails.

    Raises:
        FileNotFoundError: If the specified json_file_path does not exist.
        json.JSONDecodeError: If the JSON file content is invalid.
        KeyError: If the expected keys ('congregation', 'publishers', 'reports')
                  are not found in the JSON data.
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at '{json_file_path}'.")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from '{json_file_path}'. Details: {e}")
        raise

    cong_data = CongregationData()

    try:
        cong_data.congregation_info = raw_data['congregation']
        # Store original lists as well
        cong_data.publishers_list = raw_data['publishers']
        cong_data.reports_list = raw_data['reports']
    except KeyError as e:
        print(f"Error: Missing expected key '{e}' in JSON data structure from '{json_file_path}'.")
        raise

    # Build lookup for publishers
    for publisher in cong_data.publishers_list:
        try:
            pub_id = publisher['id']
            cong_data.publishers_by_id[pub_id] = publisher

            # Ensure firstname and lastname exist before lowercasing
            firstname = publisher.get('firstname', '')
            lastname = publisher.get('lastname', '')
            cong_data.publishers_by_name[(firstname.lower(), lastname.lower())] = publisher
        except KeyError as e:
            print(f"Warning: Publisher entry missing key '{e}': {publisher}. Skipping this entry for lookups.")
            continue # Skip problematic publisher for lookups

    # Build lookup for reports
    for report in cong_data.reports_list:
        try:
            # Assuming 'user' is a dictionary within report and contains 'id'
            publisher_id = report['user']['id']
            year = report['year']
            month = report['month']
            cong_data.reports_by_publisher_month_year[(publisher_id, year, month)] = report
        except KeyError as e:
            # More specific error messages for common issues
            if 'user' not in report:
                 print(f"Warning: Report entry missing 'user' field: {report}. Skipping this report for lookup.")
            elif 'id' not in report.get('user', {}):
                 print(f"Warning: Report entry's 'user' field missing 'id': {report}. Skipping this report for lookup.")
            elif 'year' not in report or 'month' not in report:
                print(f"Warning: Report entry missing 'year' or 'month': {report}. Skipping this report for lookup.")
            else:
                print(f"Warning: Report entry missing other key '{e}': {report}. Skipping this report for lookup.")
            continue # Skip problematic report for lookup
        except TypeError: # Handles cases where report['user'] might not be a dict
            print(f"Warning: Report entry has unexpected structure for 'user': {report}. Skipping this report for lookup.")
            continue

    # Process meeting attendance data
    attendance_data = raw_data.get('attendance')
    if isinstance(attendance_data, list):
        for att_entry in attendance_data:
            if not isinstance(att_entry, dict) or 'month' not in att_entry or 'weAvg' not in att_entry:
                print(f"Warning: Skipping invalid attendance entry: {att_entry}")
                continue
            try:
                year_str, month_str = att_entry['month'].split('-')
                year = int(year_str)
                month_num = int(month_str)
                # Ensure weAvg is a number, default to 0 if not convertible
                we_avg = att_entry['weAvg']
                if not isinstance(we_avg, (int, float)):
                    try:
                        we_avg = float(we_avg) # Try to convert if it's a string representation of a number
                    except (ValueError, TypeError):
                        print(f"Warning: Invalid 'weAvg' value in attendance entry {att_entry}, defaulting to 0.")
                        we_avg = 0

                cong_data.monthly_attendance_weekend_avg[(year, month_num)] = we_avg
            except ValueError:
                print(f"Warning: Could not parse year/month from attendance entry: {att_entry}. Skipping.")
            except Exception as e: # Catch any other unexpected errors during processing an entry
                print(f"Warning: An unexpected error occurred while processing attendance entry {att_entry}: {e}. Skipping.")
    elif attendance_data is not None: # It exists but is not a list
        print("Warning: 'attendance' data found but is not in the expected list format. Meeting attendance will not be available.")
    else: # attendance_data is None (key not found)
        print("Warning: 'attendance' data not found in JSON. Meeting attendance will not be available.")

    return cong_data
