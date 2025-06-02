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
@click.option('--month', 'target_month_str', required=True, help="The month for the data in YYYY-MM format.")
@click.pass_context
def export_csv_command(ctx: click.Context, csv_filepath: str, target_month_str: str):
    """
    Exports congregation report data for a specific month to a new CSV file.

    The CSV file will contain 'FirstName', 'LastName', 'Date', 'SharedInMinistry',
    'AP', 'Hours', 'BibleStudies', 'Credit', 'Remarks' columns.
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo(click.style("Error: Congregation data not loaded. Ensure JSON data is loaded first (e.g., via --json-file).", fg="red"), err=True)
        ctx.abort()
        return

    cong_data: CongregationData = ctx.obj['cong_data']

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(click.style(f"Error: Invalid month format. {e}", fg="red"), err=True)
        ctx.abort()
        return

    fieldnames = [
        'FirstName', 'LastName', 'Date', 'SharedInMinistry', 'AP',
        'Hours', 'BibleStudies', 'Credit', 'Remarks'
    ]

    output_rows = []

    for publisher in cong_data.publishers_list:
        publisher_id = publisher['id']
        first_name = publisher['firstName']
        last_name = publisher['lastName']

        report = cong_data.reports_by_publisher_month_year.get((publisher_id, target_year, target_month))

        row_data = {
            'FirstName': first_name,
            'LastName': last_name,
            'Date': f"{target_year:04d}-{target_month:02d}-01",
            'SharedInMinistry': False,
            'AP': False,
            'Hours': 0,
            'BibleStudies': 0,
            'Credit': '',
            'Remarks': 'No report found for this month'
        }

        if report and report.get('has_reported_field_service', False):
            role = get_publisher_role(report.get('pioneer'))
            minutes_raw = report.get('minutes')
            studies_raw = report.get('studies')
            credit_raw = report.get('credithours') # Assuming 'credithours' is the key from JSON

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
                row_data['Hours'] = 0 # Per requirement, non-pioneers Hours = 0

            row_data['BibleStudies'] = studies
            row_data['Credit'] = credit_val
            row_data['Remarks'] = report.get('remarks', '').strip()
        elif report and not report.get('has_reported_field_service', False):
            # Has a report, but did not report field service
            row_data['Remarks'] = 'Did not report field service'
            # Other fields remain as default (False, 0, empty string)

        output_rows.append(row_data)

    temp_csv_filepath = csv_filepath + ".tmp"
    try:
        with open(temp_csv_filepath, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(output_rows)

        os.replace(temp_csv_filepath, csv_filepath)
        click.echo(click.style(f"CSV file '{csv_filepath}' created successfully for month {target_month_str}.", fg="green"))

    except Exception as e:
        click.echo(click.style(f"Error writing CSV file '{csv_filepath}': {e}", fg="red"), err=True)
        if os.path.exists(temp_csv_filepath):
            try:
                os.remove(temp_csv_filepath)
            except OSError as ose:
                click.echo(click.style(f"Additionally, failed to remove temporary file '{temp_csv_filepath}': {ose}", fg="red"), err=True)
        ctx.abort()
