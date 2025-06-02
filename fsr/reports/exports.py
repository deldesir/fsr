"""
Commands for exporting congregation data.
"""
import click
import csv
import os
from typing import Optional
from fsr.core.data_loader import CongregationData
from fsr.core.file_finder import find_csv_file
from fsr.core.utils import get_publisher_role, parse_year_month
from fsr.core.constants import ROLE_AUXILIARY_PIONEER, ALL_PIONEER_ROLES

@click.group('export')
def export_group():
    """Commands for exporting data."""
    pass

@export_group.command('update-csv')
@click.option(
    '--csv-file',
    'csv_filepath_str',
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    required=False,
    default=None,
    help="Path to CSV file to update. Optional; if not provided, attempts to auto-detect common CSV export files (e.g., 'Descahos Rapò Sèvis.csv', 'FSGExtract.csv')."
)
@click.option('--month', 'target_month_str', required=True, help="The month for the data in YYYY-MM format.")
@click.pass_context
def update_csv_command(ctx: click.Context, csv_filepath_str: Optional[str], target_month_str: str):
    """
    Updates an existing CSV file with congregation report data for a specific month.

    The CSV file is expected to have at least 'FirstName' and 'LastName' columns
    for matching publishers. Other relevant columns like 'Date', 'SharedInMinistry',
    'AP', 'Hours', 'BibleStudies', 'Credit', 'Remarks' will be updated.
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo(click.style("Error: Congregation data not loaded. Ensure JSON data is loaded first (e.g., via --json-file).", fg="red"), err=True)
        ctx.abort()
        return # Abort will exit, but for clarity and type checking.

    cong_data: CongregationData = ctx.obj['cong_data']

    actual_csv_filepath = csv_filepath_str
    if actual_csv_filepath is None:
        click.echo("Info: --csv-file not provided. Attempting to auto-detect CSV file...")
        actual_csv_filepath = find_csv_file()
        if actual_csv_filepath is None:
            click.echo(click.style("Error: Auto-detection failed. No suitable CSV file found (e.g., 'Descahos Rapò Sèvis.csv', 'FSGExtract.csv') in standard locations.", fg="red"), err=True)
            click.echo(click.style("Please specify the CSV file path using the --csv-file option.", fg="red"), err=True)
            ctx.abort()
            return
        else:
            click.echo(click.style(f"Info: Auto-detected CSV file: {actual_csv_filepath}", fg="green"))

    # Type checker might complain actual_csv_filepath could be None here if abort() isn't understood.
    # Adding an explicit check or assert can help, or rely on abort() exiting.
    if actual_csv_filepath is None: # Should be unreachable due to abort above
        click.echo(click.style("Critical Error: CSV filepath is None after auto-detection logic.", fg="red"), err=True)
        ctx.abort()
        return

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(click.style(f"Error: Invalid month format. {e}", fg="red"), err=True)
        ctx.abort()
        return

    # The type Path(writable=True) in Click option implies it might create the file.
    # However, the current logic reads from it first. If it should create, os.path.exists check needs adjustment.
    # For "update", it must exist. For "create or update", logic changes.
    # Assuming "update" means it must exist.
    if not os.path.exists(actual_csv_filepath):
        click.echo(click.style(f"Error: CSV file '{actual_csv_filepath}' not found.", fg="red"), err=True)
        ctx.abort()
        return

    original_rows = []
    fieldnames = []
    try:
        with open(actual_csv_filepath, mode='r', newline='', encoding='utf-8-sig') as csvfile: # utf-8-sig to handle BOM
            reader = csv.DictReader(csvfile)
            if not reader.fieldnames:
                click.echo(click.style(f"Error: CSV file '{actual_csv_filepath}' is empty or has no header row.", fg="red"), err=True)
                ctx.abort()
                return
            fieldnames = reader.fieldnames
            # Ensure required columns for matching are present
            if not ('FirstName' in fieldnames and 'LastName' in fieldnames):
                click.echo(click.style(f"Error: CSV file '{actual_csv_filepath}' must contain 'FirstName' and 'LastName' columns.", fg="red"), err=True)
                ctx.abort()
                return
            for row in reader:
                original_rows.append(row)
    except Exception as e:
        click.echo(click.style(f"Error reading CSV file '{actual_csv_filepath}': {e}", fg="red"), err=True)
        ctx.abort()
        return

    if not original_rows:
        click.echo(click.style(f"Warning: CSV file '{actual_csv_filepath}' is empty (contains only headers or is completely empty). No data to update.", fg="yellow"), err=True)
        # No need to abort, just inform. If an empty file (post-headers) is an error, behavior would change.

    updated_rows = []
    publishers_processed_in_csv = set() # To track which publishers from JSON data we've updated in CSV

    for row_idx, csv_row in enumerate(original_rows):
        updated_row = csv_row.copy() # Start with existing data

        first_name_csv = csv_row.get('FirstName', '').strip()
        last_name_csv = csv_row.get('LastName', '').strip()

        if not first_name_csv or not last_name_csv:
            click.echo(click.style(f"Warning: CSV row {row_idx + 2} (data row {row_idx +1}) is missing FirstName or LastName. Skipping update for this row.", fg="yellow"), err=True)
            updated_rows.append(updated_row) # Keep original row
            continue

        matched_publisher = cong_data.publishers_by_name.get((first_name_csv.lower(), last_name_csv.lower()))

        if matched_publisher:
            publisher_id = matched_publisher['id']
            publishers_processed_in_csv.add(publisher_id)
            report = cong_data.reports_by_publisher_month_year.get((publisher_id, target_year, target_month))

            # Update common fields first
            updated_row['Date'] = f"{target_year:04d}-{target_month:02d}-01" # Standardize date to first of month

            if report and report.get('has_reported_field_service', False):
                role = get_publisher_role(report.get('pioneer'))
                minutes_raw = report.get('minutes')
                studies_raw = report.get('studies')
                credit_raw = report.get('credithours') # Assuming 'credithours' is the key from JSON

                # Ensure numeric fields are valid integers, default to 0 if not.
                try:
                    minutes = int(minutes_raw) if minutes_raw is not None else 0
                except (ValueError, TypeError):
                    minutes = 0
                try:
                    studies = int(studies_raw) if studies_raw is not None else 0
                except (ValueError, TypeError):
                    studies = 0

                # Credit can be varied, handle as string or numeric if defined
                credit_val = '' # Default to empty string
                if isinstance(credit_raw, (int, float)):
                    credit_val = str(credit_raw)
                elif isinstance(credit_raw, str):
                    credit_val = credit_raw.strip()


                updated_row['SharedInMinistry'] = True # Or "Yes" / "No" if preferred string values
                updated_row['AP'] = (role == ROLE_AUXILIARY_PIONEER) # True / False

                if role in ALL_PIONEER_ROLES:
                    updated_row['Hours'] = minutes // 60 # Integer hours
                else: # Non-Pioneer (or any role not in ALL_PIONEER_ROLES)
                    updated_row['Hours'] = 0

                updated_row['BibleStudies'] = studies
                updated_row['Credit'] = credit_val
                updated_row['Remarks'] = report.get('remarks', '').strip()
            else:
                # No report for this publisher/month, or did not report field service
                updated_row['SharedInMinistry'] = False
                updated_row['AP'] = False # Explicitly set AP status based on report
                updated_row['Hours'] = 0
                updated_row['BibleStudies'] = 0
                updated_row['Credit'] = ''
                updated_row['Remarks'] = 'No report or did not share in ministry' # Clarify remarks
        else:
            # Publisher from CSV not found in JSON data.
            # Clear month-specific fields for this row to indicate no data for this specific month.
            # Keep FirstName, LastName. Other identifying fields could also be kept if they exist.
            click.echo(click.style(f"Warning: Publisher '{first_name_csv} {last_name_csv}' from CSV row {row_idx + 2} (data row {row_idx+1}) not found in JSON data. Clearing their report fields for month {target_month_str}.", fg="yellow"), err=True)
            updated_row['Date'] = f"{target_year:04d}-{target_month:02d}-01"
            updated_row['SharedInMinistry'] = False
            updated_row['AP'] = False
            updated_row['Hours'] = 0
            updated_row['BibleStudies'] = 0
            updated_row['Credit'] = ''
            updated_row['Remarks'] = 'Publisher not found in source data for this month'

        updated_rows.append(updated_row)

    # Optional: Add publishers from JSON data who were not in the original CSV.
    # Current logic only updates existing entries or blanks them if not found in JSON.

    temp_csv_filepath = actual_csv_filepath + ".tmp"
    try:
        with open(temp_csv_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
            # Use extrasaction='ignore' to avoid errors if CSV has more columns than JSON processing provides
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(updated_rows)

        os.replace(temp_csv_filepath, actual_csv_filepath) # Atomic rename if possible
        click.echo(click.style(f"CSV file '{actual_csv_filepath}' updated successfully for month {target_month_str}.", fg="green"))

    except Exception as e:
        click.echo(click.style(f"Error writing updated CSV file '{actual_csv_filepath}': {e}", fg="red"), err=True)
        if os.path.exists(temp_csv_filepath):
            try:
                os.remove(temp_csv_filepath) # Clean up temp file on error
            except OSError as ose:
                click.echo(click.style(f"Additionally, failed to remove temporary file '{temp_csv_filepath}': {ose}", fg="red"), err=True)
        ctx.abort()
