# Field Service Reporter (fsr)

**fsr** is a command-line interface (CLI) tool designed to process congregation field service data from a JSON file. It can generate various summary reports and assist with data export tasks, like updating CSV files.

## Features

*   Load and parse service data from a structured JSON file.
*   Auto-detects the main JSON data file if not specified.
*   Generate monthly activity summary reports, detailing pioneer and publisher activity.
*   Export service data to a new CSV file, providing a comprehensive view of activity across all months and publishers in the dataset.
*   Modular design, allowing for future expansion with new report types or export formats.

## Installation

It is recommended to install `fsr` within a Python virtual environment.

1.  **Create and activate a virtual environment (optional but recommended):**
    ```bash
    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    
    # For Windows
    # python -m venv .venv
    # .venv\Scripts\activate
    ```

2.  **Install `fsr`:**
    *   **For regular use:**
        ```bash
        pip install .
        ```
        This command installs the package from the current directory. `pip` will use the `pyproject.toml` file to build and install the package.
    *   **For development (editable install):**
        ```bash
        pip install -e .
        ```
        This allows you to make changes to the source code and have them immediately reflected when you run the `fsr` command.

## Usage

The general command structure for `fsr` is:

```bash
fsr [OPTIONS] COMMAND [ARGS]...
```

### Main Option: JSON Data File

The `--json-file <path_to_data.json>` option specifies the path to your JSON data file. This option is **optional**.

*   **If you provide the path** using `--json-file`, `fsr` will use that specific file.
*   **If you do not provide the path**, `fsr` will attempt to auto-detect the JSON file. It searches for files named `hourglass-export.json` (or variants like `hourglass-export (1).json`, `hourglass-export (2).json`, etc.) in the following locations:
    1.  The current directory.
    2.  Your user's "Downloads" folder (and common international equivalents like "Téléchargements").
*   When multiple matching files are found during auto-detection, `fsr` selects the one that appears to be the latest (e.g., `hourglass-export (2).json` over `hourglass-export (1).json`, or the most recently modified file if numbers are tied or absent).

You would typically use the explicit `--json-file` option if your file is named differently or stored in a non-standard location.

### Commands and Examples:

Below are examples of common commands.

**1. Generate a Monthly Activity Summary:**

The `fsr summary monthly-activity --month YYYY-MM` command generates a console-based summary report of congregation activity for the specified month.

*   **Output Details:** The summary is presented in Haitian Creole and includes the following categories:
    *   'Pwoklamatè ki pa Pyonye' (Non-Pioneer Publishers)
    *   'Pyonye Oksilyè' (Auxiliary Pioneers)
    *   'Pyonye Pèmanan' (Regular Pioneers)
    *   'Pyonye Espesyal' (Special Pioneers)

    For each category, the following information is provided:
    *   **"Total Lè"** (Total Hours): Sum of hours (`minutes // 60`) from reports in that category. This is shown for 'Pyonye Oksilyè', 'Pyonye Pèmanan', and 'Pyonye Espesyal' only.
    *   **"Total Etid"** (Total Studies): Sum of Bible studies reported.
    *   **Count of reporting publishers:** A line indicating how many unique individuals reported in that category for the month (e.g., "_Te gen X pwoklamatè ki pa pyonye ki te bay rapò pou mwa sa._").

    The report also includes a "Total Etid Kongregasyon an" (Total Congregation Bible Studies).

*   **Data Interpretation for Summary:**
    *   **Active Participation:** A publisher is considered to have participated in ministry for summary aggregation if their report for the month shows positive `minutes` OR positive `studies`.
    *   **`has_reported_field_service` Flag:** If a report explicitly contains `has_reported_field_service: false`, that report's `minutes` and `studies` are **not** included in the summary totals, even if they are positive. If the flag is `true` or absent/`null`, activity is based on positive minutes/studies.
    *   **Pioneer Categorization:** Determined by the `pioneer` field in each monthly report:
        *   `'Auxiliary'` -> 'Pyonye Oksilyè'
        *   `'Regular'` -> 'Pyonye Pèmanan'
        *   `'Special'` -> 'Pyonye Espesyal'
        *   Other values (e.g., `null`, empty string, 'Publisher') -> 'Pwoklamatè ki pa Pyonye'.

*   **Example Usage:**
    *   With auto-detection of JSON file:
        ```bash
        fsr summary monthly-activity --month 2023-10
        ```
        *(fsr will search for `hourglass-export.json` or similar.)*

    *   Specifying the JSON file:
        ```bash
        fsr --json-file path/to/your/data.json summary monthly-activity --month 2023-10
        ```

**2. Export Service Data to a New CSV File:**

The `export field-service` command creates a new CSV file containing a comprehensive report of service activity. It processes all available months from the reports in the input JSON and includes a row for every publisher for each of those months.

*   **Command Structure:**
    ```bash
    fsr export field-service --csv-file <PATH_TO_NEW_CSV_FILE>
    ```
*   **`--csv-file <PATH_TO_NEW_CSV_FILE>` Option:**
    *   This option is **required**.
    *   You must specify the full path (including filename, e.g., `path/to/my_new_report.csv`) where the new CSV file will be created.
    *   Auto-detection of the output CSV path is not supported for this command.

*   **Output Rows:**
    *   For every unique month found across all reports in the input JSON data, a row is generated for *every publisher* listed in the `publishers` section of the JSON.
    *   If a publisher has a specific report for a given month, that data is used to populate their row for that month.
    *   If a publisher does *not* have a specific report for a given month (but that month exists in the overall dataset because other publishers reported), a row is still generated. In this case, it will contain default values indicating no activity for that specific publisher-month (e.g., `SharedInMinistry: False`, empty strings for hours, studies, etc.).

*   **CSV Columns:**
    The generated CSV file will have the following columns:
    `Date`, `FirstName`, `LastName`, `SharedInMinistry`, `BibleStudies`, `AP`, `Hours`, `Credit`, `Remarks`

*   **Key Field Logic Explanation:**
    *   `Date`: Formatted as `YYYY-MM` (e.g., "2023-10").
    *   `SharedInMinistry`: `True` if the report for that month indicates activity (positive `minutes` or `studies`). However, if the `has_reported_field_service` key is explicitly set to `false` in the source JSON for that specific report, `SharedInMinistry` will be `False`, overriding any inference from minutes or studies. Otherwise, it's `False`.
    *   `AP` (Auxiliary Pioneer): `True` if `SharedInMinistry` is `True` AND the `pioneer` status in the report for that month is exactly `'Auxiliary'`. Otherwise `False`.
    *   `Hours`: Calculated from `minutes` in the report (`minutes // 60`). Shown as a string representation of the whole number only if `SharedInMinistry` is `True` and the calculated hours value is `> 0`. Otherwise, it's an empty string.
    *   `BibleStudies`: Shows the number of studies (as a string) if `SharedInMinistry` is `True` and the `studies` value from the report is `> 0`. Otherwise, it's an empty string.
    *   `Credit`: Shows credit hours (as a string) if `SharedInMinistry` is `True` and the `credithours` value from the report is numerically `> 0`. Whole numbers are shown as integers (e.g., "5"), floats as floats (e.g., "1.5"). Otherwise, it's an empty string.
    *   `Remarks`: Shows remarks from the report if present and not just whitespace (after stripping). Otherwise, it's an empty string.

*   **Example Usage:**
    *   **With auto-detection of JSON file:**
        ```bash
        fsr export field-service --csv-file path/to/my_new_report.csv
        ```
    *   **Specifying the JSON file:**
        ```bash
        fsr --json-file path/to/data.json export field-service --csv-file path/to/my_new_report.csv
        ```

## JSON Data Structure

`fsr` expects a JSON file with the following primary top-level keys:

*   `"congregation"`: An object containing general information about the congregation (e.g., name, ID). This data is loaded but not directly used by current commands.
*   `"publishers"`: A list of publisher objects. Each publisher object should ideally contain:
    *   `"id"`: A unique identifier for the publisher.
    *   `"firstname"`: Publisher's first name.
    *   `"lastname"`: Publisher's last name.
*   `"reports"`: A list of individual service report objects. Each report object should contain:
    *   `"user"`: A nested object with an `"id"` field matching a publisher's ID (e.g., `{"user": {"id": 123}}`).
    *   `"year"`: Integer, the year of the report (e.g., `2023`).
    *   `"month"`: Integer, the month of the report (e.g., `10` for October).
    *   `"pioneer"`: String or `null`, indicating pioneer status (e.g., "Auxiliary", "Regular", "Special", or `null`).
    *   `"studies"`: Integer or `null`, number of bible studies.
    *   `"minutes"`: Integer or `null`, total minutes in service.
    *   `"credithours"`: Numeric (integer or float), string representation of a number, or `null`, for hours to be credited.
    *   `"remarks"`: String or `null`, any remarks for the report.
    *   `"has_reported_field_service"`: Boolean (`true`/`false`) or `null`. This field is optional.
        *   If `true`, it confirms the publisher shared in service.
        *   If `false`, it explicitly states the publisher did *not* share in service for that month.
            *   For CSV export (`export field-service`): Fields like `Hours`, `Studies`, `Credit` will be empty, and `AP` status will be `False`, regardless of other data in `minutes`, `studies`, etc. Remarks will still be preserved.
            *   For summary reports (`summary monthly-activity`): The report's numeric activities (minutes, studies) are excluded from aggregation.
        *   If `null` or absent:
            *   For CSV export: Sharing status (`SharedInMinistry`) is inferred based on positive values in `minutes` or `studies`.
            *   For summary reports: Active participation is inferred based on positive values in `minutes` or `studies`.

### Note on Activity Determination (for CSV Export and Summaries)

The determination of whether a publisher's activity is included or how `SharedInMinistry` is set depends on a combination of factors:

1.  **`has_reported_field_service` flag (in JSON report data):**
    *   **Explicit `false`:** This is a definitive indication of no participation.
        *   In `export field-service`: `SharedInMinistry` will be `False`. Consequently, `Hours`, `BibleStudies`, `Credit` will be empty, and `AP` will be `False`. `Remarks` are still shown.
        *   In `summary monthly-activity`: This report's `minutes` and `studies` will be ignored for aggregation into totals. The publisher will not be counted as "reporting" for that category unless they have other qualifying reports for the same month (which is unlikely for a single person).
    *   **Explicit `true`:** This is a definitive indication of participation.
        *   In `export field-service`: `SharedInMinistry` will be `True`. Other fields (`Hours`, `BibleStudies`, etc.) are then populated based on their specific rules (e.g., positive values).
        *   In `summary monthly-activity`: The report's `minutes` and `studies` are included in aggregations if they are positive.
    *   **`null` or Missing:** If the `has_reported_field_service` flag is not present or is `null`:
        *   In `export field-service`: `SharedInMinistry` is inferred. It becomes `True` if the report contains positive `minutes` OR positive `studies`; otherwise, it's `False`.
        *   In `summary monthly-activity`: Active participation for aggregation is inferred. It's considered active if the report contains positive `minutes` OR positive `studies`.

This nuanced handling allows for flexibility if the source JSON sometimes omits the `has_reported_field_service` flag, while still respecting it when it's explicitly provided.
