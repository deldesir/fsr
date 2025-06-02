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
                    'Date': f"{report_year:04d}-{report_month:02d}-01",
                    'SharedInMinistry': False,
                    'AP': False,
                    'Hours': 0,
                    'BibleStudies': 0,
                    'Credit': '',
                    'Remarks': '' # Default empty, will be overridden
                }

                if report_data and report_data.get('has_reported_field_service', False):
                    role = get_publisher_role(report_data.get('pioneer'))
                    minutes_raw = report_data.get('minutes')
                    studies_raw = report_data.get('studies')
                    credit_raw = report_data.get('credithours')

                    try:
                        minutes = int(minutes_raw) if minutes_raw is not None else 0
                    except (ValueError, TypeError):
                        minutes = 0
                    try:
                        studies = int(studies_raw) if studies_raw is not None else 0
                    except (ValueError, TypeError):
                        studies = 0

                    credit_val = ''
                    if isinstance(credit_raw, (int, float)):
                        credit_val = str(credit_raw)
                    elif isinstance(credit_raw, str):
                        credit_val = credit_raw.strip()

                    row_data['SharedInMinistry'] = True
                    row_data['AP'] = (role == ROLE_AUXILIARY_PIONEER)

                    if role in ALL_PIONEER_ROLES:
                        row_data['Hours'] = minutes // 60
                    else:
                        row_data['Hours'] = 0

                    row_data['BibleStudies'] = studies
                    row_data['Credit'] = credit_val
                    row_data['Remarks'] = report_data.get('remarks', '').strip()
                elif report_data: # Report exists but not field service
                    row_data['Remarks'] = 'Did not report field service'
                else: # Should not happen if iterating items from reports_by_publisher_month_year
                    row_data['Remarks'] = 'Error: Report data missing unexpectedly'

                output_rows.append(row_data)

        if not publisher_has_any_reports:
            # Add a single row for publishers with no reports at all
            output_rows.append({
                'FirstName': first_name,
                'LastName': last_name,
                'Date': 'N/A',
                'SharedInMinistry': False,
                'AP': False,
                'Hours': 0,
                'BibleStudies': 0,
                'Credit': '',
                'Remarks': 'No reports found for this publisher'
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
