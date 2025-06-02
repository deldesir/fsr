# Field Service Reporter (fsr)

**fsr** is a command-line interface (CLI) tool designed to process congregation field service data from a JSON file. It can generate various summary reports and assist with data export tasks, like updating CSV files.

## Features

*   Load and parse service data from a structured JSON file.
*   Generate monthly activity summary reports, detailing pioneer and publisher activity.
*   Update existing CSV files with monthly service report data.
*   Modular design, allowing for future expansion with new report types or export formats.

## Installation

To install `fsr` locally, run:
```bash
pip install .
```

## Usage

The general command structure for `fsr` is:

```bash
fsr --json-file <path_to_data.json> <command> <subcommand> [options]
```

You must always provide the path to your JSON data file using the `--json-file` option.

### Examples:

**1. Generate a Monthly Activity Summary:**

To generate a summary for a specific month (e.g., October 2023):

```bash
fsr --json-file path/to/your/data.json summary monthly-activity --month 2023-10
```

**2. Update a CSV Export:**

To update an existing CSV file with data for a specific month:

```bash
fsr --json-file path/to/your/data.json export update-csv --csv-file path/to/your/report.csv --month 2023-10
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
