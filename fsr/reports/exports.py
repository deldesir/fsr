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
    Publishers with no reports in the dataset will be excluded from the output.

    The CSV file will contain 'Date', 'FirstName', 'LastName', 'SharedInMinistry',
    'BibleStudies', 'AP', 'Hours', 'Credit', 'Remarks' columns.
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
        publisher_id = publisher.get('id') # Use .get for safety, though id is expected
        if not publisher_id:
            click.echo(click.style(f"Warning: Publisher data missing 'id'. Skipping entry: {publisher}", fg="yellow"), err=True)
            continue

        first_name = publisher.get('firstname', '')
        last_name = publisher.get('lastname', '')

        # Filter reports for the current publisher first
        reports_for_this_publisher = {
            (year, month): report_obj
            for (pub_id, year, month), report_obj in cong_data.reports_by_publisher_month_year.items()
            if pub_id == publisher_id
        }

        if not reports_for_this_publisher:
            continue # Skip to the next publisher if they have no reports at all

        # Iterate through the filtered reports for this publisher
        for (report_year, report_month), report_data in reports_for_this_publisher.items():
            # publisher_has_any_reports = True (This flag is no longer needed)
            # if report_pub_id == publisher_id: (This check is no longer needed)

            # Step 1: Initial row_data Setup for a Report
                row_data = {
                    'Date': f"{report_year:04d}-{report_month:02d}",
                    'FirstName': first_name, # Already fetched from publisher object
                    'LastName': last_name,   # Already fetched from publisher object
                    'SharedInMinistry': False,
                    'BibleStudies': '',
                    'AP': False,
                    'Hours': '',
                    'Credit': '',
                    'Remarks': ''
                }

                # Step 2: Determine shared_in_ministry
                # report_data is guaranteed to be non-None here due to the loop structure
                shared_in_ministry = report_data.get('has_reported_field_service', False)
                row_data['SharedInMinistry'] = shared_in_ministry

                # Step 3: Populate Remarks (conditionally)
                actual_remarks = report_data.get('remarks')
                if isinstance(actual_remarks, str) and actual_remarks.strip():
                    row_data['Remarks'] = actual_remarks.strip()
                # Else, it remains '' from default

                # Step 4: Conditional Population based on shared_in_ministry
                if shared_in_ministry:
                    # AP Status
                    pioneer_status = report_data.get('pioneer')
                    if pioneer_status == 'Auxiliary':
                        row_data['AP'] = True
                    # Else AP remains False (its default)

                    # Hours
                    minutes_raw = report_data.get('minutes')
                    if minutes_raw is not None:
                        try:
                            minutes_val = int(minutes_raw)
                            if minutes_val > 0:
                                hours_calculated = minutes_val // 60
                                if hours_calculated > 0:
                                    row_data['Hours'] = str(hours_calculated)
                                # else: Hours remains '' (for <60 mins but >0 mins)
                        except (ValueError, TypeError):
                            pass # Hours remains ''

                    # Bible Studies
                    studies_raw = report_data.get('studies')
                    if studies_raw is not None:
                        try:
                            studies_val = int(studies_raw)
                            if studies_val > 0:
                                row_data['BibleStudies'] = str(studies_val)
                        except (ValueError, TypeError):
                            pass # BibleStudies remains ''

                    # Credit Hours
                    credit_raw = report_data.get('credithours')
                    if credit_raw is not None and str(credit_raw).strip():
                        try:
                            numeric_credit_val = float(str(credit_raw))
                            if numeric_credit_val > 0:
                                if numeric_credit_val == int(numeric_credit_val):
                                    row_data['Credit'] = str(int(numeric_credit_val))
                                else:
                                    row_data['Credit'] = str(numeric_credit_val)
                        except (ValueError, TypeError):
                            pass # Credit remains ''
                else:
                    # shared_in_ministry is False
                    # Confirming defaults (already set, but for clarity as per request)
                    row_data['AP'] = False
                    row_data['Hours'] = ''
                    row_data['BibleStudies'] = ''
                    row_data['Credit'] = ''
                    # Remarks are handled prior to this if/else

                output_rows.append(row_data)

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
