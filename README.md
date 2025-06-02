# CSV Updater from JSON

## Description

This Python script updates a target CSV file with data retrieved from a source JSON file. The updates are applied specifically to rows in the CSV that match a given month and year, based on detailed mapping rules and publisher activity information contained in the JSON.

The script is designed to process publisher activity reports, reflecting them accurately in a CSV format according to predefined business logic.

## Requirements

- Python 3.x
- Standard Python libraries: `argparse`, `csv`, `json` (no external packages need to be installed).

## Usage

The script is run from the command line:

```bash
python update_csv.py --csv-file <path_to_csv> --json-file <path_to_json> --month <YYYY-MM>
```

### Arguments:

-   `--csv-file <path_to_csv>`: (Required) The full path to the target CSV file that will be read and updated.
-   `--json-file <path_to_json>`: (Required) The full path to the source JSON file containing the publisher and report data.
-   `--month <YYYY-MM>`: (Required) The target month and year for which CSV rows should be updated. Format must be "YYYY-MM" (e.g., "2023-10").

## Input File Formats

### JSON File (`--json-file`)

The JSON file is expected to have a specific structure:

-   A `publishers` key containing a list of publisher objects. Each publisher object should have at least:
    -   `id`: A unique identifier for the publisher.
    -   `firstname`: The publisher's first name.
    -   `lastname`: The publisher's last name.
-   A `reports` key containing a list of monthly report objects. Each report object should link to a user/publisher and contain activity details. Relevant fields include:
    -   `user`: An object containing the publisher's `id` (e.g., `{"id": 12345}`).
    -   `year`: Integer representing the year of the report.
    -   `month`: Integer representing the month of the report (1-12).
    -   `pioneer`: A string indicating pioneer status (e.g., "Auxiliary", "Regular", "Special", or `null`).
    -   `studies`: Integer, number of Bible studies.
    -   `minutes`: Integer, ministry time in minutes.
    -   `credithours`: Integer, credit hours (assumed to be denominated in hours).
    -   `remarks`: String, any remarks for the month.

### CSV File (`--csv-file`)

The CSV file should contain columns including (but not necessarily limited to):

-   `Date`: The month and year of the record (e.g., "YYYY-MM").
-   `FirstName`: Publisher's first name.
-   `LastName`: Publisher's last name.
-   `SharedInMinistry`: Boolean-like string ("True"/"False") indicating if they shared in ministry.
-   `BibleStudies`: Integer string, number of Bible studies.
-   `AP`: Boolean-like string ("True"/"False") indicating if they were an Auxiliary Pioneer that month.
-   `Hours`: Integer string, hours of ministry.
-   `Credit`: Integer string, credit hours.
-   `Remarks`: String, remarks.

The script matches CSV rows to JSON publishers based on `FirstName`, `LastName`, and the `Date` (matching the provided `--month` argument).

## Logic Overview

-   **Data Loading**: Parses the entire JSON file to create quick lookup dictionaries for publishers (by name) and their reports (by user ID, year, and month).
-   **CSV Processing**: Reads the CSV file row by row.
-   **Target Month Matching**: For rows where the `Date` column matches the input `--month`, the script attempts to find a corresponding publisher and their report in the JSON data.
-   **Data Mapping Rules**:
    -   `SharedInMinistry`: Set to `True` if a JSON report exists for the publisher for the target month, `False` otherwise.
    -   `BibleStudies`, `Credit`, `Remarks`: Populated from the JSON report.
    -   `AP` (Auxiliary Pioneer flag): Set to `True` only if the `report.pioneer` status indicates "Auxiliary Pioneer".
    -   `Hours`:
        -   For Non-Pioneer publishers, `Hours` are set to `0` (or empty), regardless of any `minutes` recorded in their JSON report.
        -   For Auxiliary, Regular, or Special Pioneers, `Hours` are calculated as `report.minutes // 60`.
-   **No Report Found**: If a JSON report isn't found for a publisher in the target month, their CSV row for that month is updated with default "inactive" values (`SharedInMinistry=False`, numeric fields to "0", etc.).
-   **Untouched Rows**: CSV rows for months other than the target `--month` are not modified.

## Error Handling

The script includes basic error handling for:
- File not found (for both CSV and JSON inputs).
- Invalid JSON format.
- Issues during CSV reading or writing.
Error messages will be printed to the console if such issues occur.

## Output

The script modifies the input CSV file **in-place**. It is recommended to back up the CSV file before running the script if you need to preserve the original state.
