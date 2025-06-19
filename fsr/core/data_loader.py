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
    # Assuming structure like: {"attendance": {"attendance": [{"month": "YYYY-MM", "weAvg": X}, ...]}}
    # or simply {"attendance": [{"month": "YYYY-MM", "weAvg": X}, ...]} if the outer dict is the list itself.
    # The prompt was raw_data.get('attendance', {}), then monthly_records = attendance_data.get('attendance', [])
    # This implies the nested structure.

    attendance_top_level = raw_data.get('attendance', {})
    if isinstance(attendance_top_level, dict):
        monthly_records = attendance_top_level.get('attendance', [])
    elif isinstance(attendance_top_level, list): # Handles if 'attendance' key points directly to a list
        monthly_records = attendance_top_level
    else:
        monthly_records = []

    if not monthly_records and attendance_top_level: # Data exists at 'attendance' but not in expected list format or empty list
        print("Warning: 'attendance' data found but is not a list of records or is empty. Meeting attendance will not be available.")
    elif not attendance_top_level: # 'attendance' key itself is missing
        print("Warning: 'attendance' key not found in JSON. Meeting attendance will not be available.")

    for item in monthly_records:
        if not isinstance(item, dict):
            print(f"Warning: Skipping invalid attendance item (not a dictionary): {item}")
            continue

        month_str = item.get('month')
        we_avg_raw = item.get('weAvg')

        if not month_str or we_avg_raw is None: # Check if essential keys are missing
            print(f"Warning: Skipping attendance item with missing 'month' or 'weAvg': {item}")
            continue

        try:
            year = int(month_str.split('-')[0])
            month_num = int(month_str.split('-')[1])

            we_avg = 0
            try:
                we_avg = int(we_avg_raw) # Or float if decimal averages are possible
            except (ValueError, TypeError):
                print(f"Warning: Could not parse 'weAvg' value '{we_avg_raw}' for month {month_str}. Defaulting to 0.")
                # we_avg remains 0

            cong_data.monthly_attendance_weekend_avg[(year, month_num)] = we_avg
        except ValueError:
            print(f"Warning: Could not parse year/month from attendance item: {item}. Skipping.")
        except Exception as e: # Catch-all for other unexpected errors with an item
            print(f"Warning: An unexpected error occurred processing attendance item {item}: {e}. Skipping.")

    return cong_data
