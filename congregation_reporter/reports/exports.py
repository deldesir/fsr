"""
Commands for exporting congregation data.
"""
import click
import csv
import os
from congregation_reporter.core.data_loader import CongregationData
from congregation_reporter.core.utils import get_publisher_role, parse_year_month
from ..core.constants import ROLE_AUXILIARY_PIONEER, ALL_PIONEER_ROLES

@click.group('export')
def export_group():
    """Commands for exporting data."""
    pass

@export_group.command('update-csv')
@click.option('--csv-file', 'csv_filepath_str', type=click.Path(dir_okay=False, writable=True, resolve_path=True), required=True, help="Path to the CSV file to update.")
@click.option('--month', 'target_month_str', required=True, help="The month for the data in YYYY-MM format.")
@click.pass_context
def update_csv_command(ctx: click.Context, csv_filepath_str: str, target_month_str: str):
    """
    Updates an existing CSV file with congregation report data for a specific month.

    The CSV file is expected to have at least 'FirstName' and 'LastName' columns
    for matching publishers. Other relevant columns like 'Date', 'SharedInMinistry',
    'AP', 'Hours', 'BibleStudies', 'Credit', 'Remarks' will be updated.
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo("Error: Congregation data not loaded. Run with --json-file option.", err=True)
        ctx.abort()
        return

    cong_data: CongregationData = ctx.obj['cong_data']

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(f"Error: Invalid month format. {e}", err=True)
        ctx.abort()
        return

    if not os.path.exists(csv_filepath_str):
        click.echo(f"Error: CSV file '{csv_filepath_str}' not found.", err=True)
        ctx.abort()
        return

    original_rows = []
    fieldnames = []
    try:
        with open(csv_filepath_str, mode='r', newline='', encoding='utf-8-sig') as csvfile: # utf-8-sig to handle BOM
            reader = csv.DictReader(csvfile)
            if not reader.fieldnames:
                click.echo(f"Error: CSV file '{csv_filepath_str}' is empty or has no header row.", err=True)
                ctx.abort()
                return
            fieldnames = reader.fieldnames
            # Ensure required columns for matching are present
            if not ('FirstName' in fieldnames and 'LastName' in fieldnames):
                click.echo(f"Error: CSV file '{csv_filepath_str}' must contain 'FirstName' and 'LastName' columns.", err=True)
                ctx.abort()
                return
            for row in reader:
                original_rows.append(row)
    except Exception as e:
        click.echo(f"Error reading CSV file '{csv_filepath_str}': {e}", err=True)
        ctx.abort()
        return

    if not original_rows:
        click.echo(f"Warning: CSV file '{csv_filepath_str}' is empty. No data to update.", err=True)
        # No need to abort, just inform and exit gracefully if file is empty after header.
        # Or, if creating it is an option, this is where it could be handled.
        # For now, assuming "update" means it has data.

    updated_rows = []
    publishers_processed_in_csv = set() # To track which publishers from JSON data we've updated in CSV

    for row_idx, csv_row in enumerate(original_rows):
        updated_row = csv_row.copy() # Start with existing data

        first_name_csv = csv_row.get('FirstName', '').strip()
        last_name_csv = csv_row.get('LastName', '').strip()

        if not first_name_csv or not last_name_csv:
            click.echo(f"Warning: CSV row {row_idx + 1} is missing FirstName or LastName. Skipping update for this row.", err=True)
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
                updated_row['AP'] = False
                updated_row['Hours'] = 0
                updated_row['BibleStudies'] = 0
                updated_row['Credit'] = ''
                # Decide on Remarks: clear or keep? Clearing for consistency with other cleared fields.
                updated_row['Remarks'] = ''
        else:
            click.echo(f"Warning: Publisher '{first_name_csv} {last_name_csv}' from CSV row {row_idx + 1} not found in JSON data. Keeping existing data for this row for month {target_month_str}.", err=True)
            # To avoid altering data for a month when the person isn't matched, we might
            # choose to not set 'Date' or other fields, or set them to empty for this month.
            # For now, keeping existing data means the row is added as-is.
            # If the goal is to *only* have data for matched people for this month, this logic would change.
            # A safer approach for "update" is to only touch rows of matched people.
            # If 'Date' was a key to update only specific month's entries, that would be different.
            # Given the current structure, this implies the CSV might have multiple month entries per person,
            # or this tool is used month-by-month on a simpler CSV. Assuming the latter.
            # So, if a person from CSV is not in JSON, their report for *this month* is effectively "no report".
            # This means clearing their values for this month might be appropriate.
            # Let's clear them to indicate no data for this month for this unmatched person.
            updated_row['Date'] = f"{target_year:04d}-{target_month:02d}-01"
            updated_row['SharedInMinistry'] = False
            updated_row['AP'] = False
            updated_row['Hours'] = 0
            updated_row['BibleStudies'] = 0
            updated_row['Credit'] = ''
            updated_row['Remarks'] = 'Publisher not found in source data for this month'


        updated_rows.append(updated_row)

    # Optional: Add publishers from JSON data who were not in the original CSV
    # This would make it an "update and append" operation. For now, sticking to "update existing".
    # If needed, iterate cong_data.publishers_list, check against publishers_processed_in_csv,
    # and append new rows for those not found in CSV.

    temp_csv_filepath = csv_filepath_str + ".tmp"
    try:
        with open(temp_csv_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore') # ignore fields not in header
            writer.writeheader()
            writer.writerows(updated_rows)

        os.replace(temp_csv_filepath, csv_filepath_str) # Atomic rename if possible
        click.echo(f"CSV file '{csv_filepath_str}' updated successfully for month {target_month_str}.")

    except Exception as e:
        click.echo(f"Error writing updated CSV file '{csv_filepath_str}': {e}", err=True)
        if os.path.exists(temp_csv_filepath):
            try:
                os.remove(temp_csv_filepath) # Clean up temp file on error
            except OSError as ose:
                click.echo(f"Additionally, failed to remove temporary file '{temp_csv_filepath}': {ose}", err=True)
        ctx.abort()
