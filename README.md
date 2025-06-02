# Field Service Reporter (fsr)

**fsr** is a command-line interface (CLI) tool designed to process congregation field service data from a JSON file. It can generate various summary reports and assist with data export tasks, like updating CSV files.

## Features

*   Load and parse service data from a structured JSON file.
*   Auto-detects the main JSON data file (typically `hourglass-export.json`) if not specified.
*   Generate monthly activity summary reports, detailing pioneer and publisher activity.
*   Update existing CSV files with monthly service report data. The CSV file for update (e.g., `Descahos Rapò Sèvis.csv` or `FSGExtract.csv`) can also be auto-detected.
*   Modular design, allowing for future expansion with new report types or export formats.

## Installation

To install `fsr` locally, run:
```bash
pip install .
```

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

This command generates a summary for a specific month (e.g., October 2023).

*   **With auto-detection of JSON file:**
    ```bash
    fsr summary monthly-activity --month 2023-10
    ```
    *(fsr will search for `hourglass-export.json` or similar.)*

*   **Specifying the JSON file:**
    ```bash
    fsr --json-file path/to/your/data.json summary monthly-activity --month 2023-10
    ```

**2. Update a CSV Export:**

The `export update-csv` command updates an existing CSV file with data for a specific month.
The `--csv-file <path_to_report.csv>` option for this command is also **optional**.

*   **If you provide the CSV file path** using `--csv-file`, `fsr` will use that specific file.
*   **If you do not provide the CSV file path**, `fsr` will attempt to auto-detect it. It searches for files named `Descahos Rapò Sèvis.csv` or `FSGExtract.csv` (and their numbered variants like `Descahos Rapò Sèvis (1).csv`) in the current directory and your Downloads folder.
*   Similar to JSON auto-detection, the latest version of the CSV file will be chosen if multiple are found.

Here are various ways to use the `export update-csv` command:

*   **Both JSON and CSV files specified:**
    ```bash
    fsr --json-file path/to/data.json export update-csv --csv-file path/to/report.csv --month 2023-10
    ```

*   **Only JSON file specified (CSV auto-detected):**
    ```bash
    fsr --json-file path/to/data.json export update-csv --month 2023-10
    ```
    *(fsr will search for `Descahos Rapò Sèvis.csv`, `FSGExtract.csv`, or similar for the CSV file.)*

*   **Only CSV file specified (JSON auto-detected):**
    ```bash
    fsr export update-csv --csv-file path/to/report.csv --month 2023-10
    ```
    *(fsr will search for `hourglass-export.json` or similar for the JSON data.)*

*   **Neither JSON nor CSV file specified (both auto-detected):**
    ```bash
    fsr export update-csv --month 2023-10
    ```
    *(fsr will search for both files in their respective default patterns and locations.)*


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
    *   `"pioneer"`: String or `null`, indicating pioneer status (e.g., "Auxiliary Pioneer", "Regular", "Special", or `null`). Used by `get_publisher_role`.
    *   `"studies"`: Integer, number of bible studies.
    *   `"minutes"`: Integer, total minutes in service. (Note: For the `monthly-activity` summary, minutes for non-pioneers are ignored).
    *   `"credithours"`: Integer or `null`, hours to be credited (assumed to be in hours).
    *   `"remarks"`: String, any remarks for the report.
    *   `"has_reported_field_service"`: Boolean (optional, defaults to `False` if missing). If this field is present, it must be `true` for the report's activity (minutes, studies) to be included in summaries and CSV exports. If this field is `false`, the person is considered to have not shared in service for that month for aggregation purposes.

### Note on `has_reported_field_service`

The `monthly-activity` summary and `update-csv` export commands rely on the `has_reported_field_service` field within each report object in your JSON data.
- If this field is present and set to `true`, the publisher's activity (minutes, studies, etc.) for that month is included in aggregations.
- If this field is `false`, or if the field is entirely **absent** from a report object, `fsr` will consider that publisher as not having reported field service for that month, and their specific activity metrics (minutes, studies) will generally be excluded or zeroed out in generated reports and exports (though they may still be listed as having 'SharedInMinistry: False' in a CSV update if a row exists for them).

Ensure your JSON data includes this field appropriately if you need fine-grained control over who is counted as an active reporter.
