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

@export_group.command('export-csv')
@click.option(
    '--csv-file',
    'csv_filepath',
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    required=True,
    help="Path to CSV file to create."
)
@click.pass_context
def export_csv_command(ctx: click.Context, csv_filepath: str):
    """
    Exports all congregation report data for all publishers across all months to a new CSV file.

    The CSV file will contain 'Date', 'FirstName', 'LastName', 'SharedInMinistry',
    'BibleStudies', 'AP', 'Hours', 'Credit', 'Remarks' columns.
    If a publisher has no reports, a single line with 'N/A' for Date and default values
    for report fields will be included, with a remark indicating no reports were found.
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo(click.style("Error: Congregation data not loaded. Ensure JSON data is loaded first (e.g., via --json-file).", fg="red"), err=True)
        ctx.abort()
        return

    cong_data: CongregationData = ctx.obj['cong_data']

    fieldnames = [
        'Date', 'FirstName', 'LastName', 'SharedInMinistry', 'BibleStudies',
        'AP', 'Hours', 'Credit', 'Remarks'
    ]

    output_rows = []

    for publisher in cong_data.publishers_list:
        publisher_id = publisher['id'] # Assuming 'id' is guaranteed by data loading
        first_name = publisher.get('firstname', '')
        last_name = publisher.get('lastname', '')
        publisher_has_any_reports = False

        # Iterate through all reports to find those matching this publisher
        # Assuming reports_by_publisher_month_year is {(pub_id, year, month): report_dict}
        for (report_pub_id, report_year, report_month), report_data in cong_data.reports_by_publisher_month_year.items():
            if report_pub_id == publisher_id:
                publisher_has_any_reports = True

                row_data = {
                    'FirstName': first_name,
                    'LastName': last_name,
                    'Date': f"{report_year:04d}-{report_month:02d}",
                    'SharedInMinistry': False, # Default, overridden if has_reported_field_service
                    'AP': False,             # Default, overridden if AP and has_reported_field_service
                    'Hours': '',
                    'BibleStudies': '',
                    'Credit': '',
                    'Remarks': ''
                }

                if report_data and report_data.get('has_reported_field_service', False):
                    row_data['SharedInMinistry'] = True
                    pioneer_status = report_data.get('pioneer')
                    row_data['AP'] = (pioneer_status == 'Auxiliary')

                    # Populate BibleStudies
                    studies_raw = report_data.get('studies')
                    if studies_raw is not None: # Check if the key exists and is not null
                        try:
                            studies_val = int(studies_raw)
                            if studies_val > 0: # Only populate if studies are greater than 0
                                row_data['BibleStudies'] = str(studies_val)
                            # If studies_val is 0 or less, BibleStudies remains '', which is desired
                        except (ValueError, TypeError):
                            # studies_raw was not a valid number, BibleStudies remains ''
                            pass
                    # Else (if studies_raw is None), BibleStudies remains ''

                    # Populate Hours (for any publisher if minutes > 0 and result in hours >=1)
                    minutes_raw = report_data.get('minutes')
                    if minutes_raw is not None:
                        try:
                            minutes_val = int(minutes_raw)
                            if minutes_val > 0:
                                hours_calculated = minutes_val // 60
                                if hours_calculated > 0: # Only show if at least 1 hour
                                    row_data['Hours'] = str(hours_calculated)
                                # If hours_calculated is 0 (e.g. 30 minutes), Hours remains '', which is desired.
                        except (ValueError, TypeError):
                            pass # minutes_raw was not a valid number, Hours remains ''

                    # Populate Credit
                    credit_raw = report_data.get('credithours') # This can be numeric, string, or null in JSON
                    if credit_raw is not None and str(credit_raw).strip(): # Check if it's not None and not an empty/whitespace string
                        try:
                            # Attempt to convert to float first to handle potential decimal strings like "1.5"
                            numeric_credit_val = float(str(credit_raw))

                            if numeric_credit_val > 0:
                                # If it needs to be an integer in the CSV, and it's a whole number:
                                if numeric_credit_val == int(numeric_credit_val):
                                    row_data['Credit'] = str(int(numeric_credit_val))
                                else: # It's a float with decimal part
                                    row_data['Credit'] = str(numeric_credit_val)
                            # If numeric_credit_val is 0 or less, Credit remains '', which is desired

                        except (ValueError, TypeError):
                            # credit_raw was not a valid number (e.g. non-numeric string after strip). Credit remains ''.
                            pass
                    # Else (if credit_raw is None or an empty/whitespace string), Credit remains ''

                    # Remarks population was here, now moved after this if/elif block
                    pass # Placeholder for removed remarks logic

                elif report_data: # Report exists but has_reported_field_service is False
                    # SharedInMinistry and AP remain False, Hours, BibleStudies, Credit remain ''
                    # Remarks population was here, now moved after this if/elif block
                    pass # Placeholder for removed remarks logic

                # Consolidated Remarks population for any valid report_data
                if report_data: # This check is technically redundant if we are inside the publisher_id match
                    remarks_raw = report_data.get('remarks', '') # Get remarks, default to empty string if key missing
                    if isinstance(remarks_raw, str): # Ensure it's a string before stripping
                        remarks_val = remarks_raw.strip()
                    else: # If not a string (e.g. None, or a number by mistake), treat as empty
                        remarks_val = ''
                    row_data['Remarks'] = remarks_val # Assign stripped value

                output_rows.append(row_data)

        if not publisher_has_any_reports:
            # Add a single row for publishers with no reports at all
            output_rows.append({
                'FirstName': first_name,
                'LastName': last_name,
                'Date': 'N/A',
                'SharedInMinistry': False,
                'AP': False,
                'Hours': '',
                'BibleStudies': '',
                'Credit': '',
                'Remarks': '' # Changed from 'No reports found for this publisher'
            })

    temp_csv_filepath = csv_filepath + ".tmp"
    try:
        with open(temp_csv_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

        os.replace(temp_csv_filepath, csv_filepath)
        click.echo(click.style(f"CSV file '{csv_filepath}' created successfully.", fg="green"))

    except Exception as e:
        click.echo(click.style(f"Error writing CSV file '{csv_filepath}': {e}", fg="red"), err=True)
        if os.path.exists(temp_csv_filepath):
            try:
                os.remove(temp_csv_filepath)
            except OSError as ose:
                click.echo(click.style(f"Additionally, failed to remove temporary file '{temp_csv_filepath}': {ose}", fg="red"), err=True)
        ctx.abort()
