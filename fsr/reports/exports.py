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

@export_group.command('field-service')
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
    Exports congregation report data to a CSV file. 
    For each month that has any reported activity in the entire dataset, a row is generated for every publisher listed.
    If a publisher does not have a specific report for one of these months, their row for that month will show default values 
    (e.g., False for booleans, empty strings for text/numeric fields).

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

    # Collect Unique Months from all reports in the dataset
    all_report_months = set()
    if cong_data.reports_by_publisher_month_year: # Check if there are any reports at all
        for _, year, month in cong_data.reports_by_publisher_month_year.keys():
            all_report_months.add((year, month))
    
    # If there are publishers but absolutely no reports for anyone,
    # all_report_months will be empty. The subsequent loops based on sorted_months
    # or publishers_list will handle this by likely producing an empty data CSV.
    # No special row generation needed here if no report months exist.
    
    sorted_months = sorted(list(all_report_months))

    # The main iteration logic will be changed in a subsequent step.
    # For now, this subtask only focuses on collecting and sorting these unique months.
    # New loop structure: Iterate through months, then publishers.
    for current_year, current_month in sorted_months:
        for publisher in cong_data.publishers_list:
            publisher_id = publisher.get('id')
            if not publisher_id:
                # This case should ideally be handled when loading/validating CongregationData
                # or at the start of publisher iteration if a publisher absolutely needs an ID.
                # For robustness here, we can skip if ID is essential for report lookup.
                click.echo(click.style(f"Warning: Publisher data missing 'id', cannot process for month {current_year}-{current_month}. Data: {publisher}", fg="yellow"), err=True)
                continue

            first_name = publisher.get('firstname', '')
            last_name = publisher.get('lastname', '')

            report_data = cong_data.reports_by_publisher_month_year.get((publisher_id, current_year, current_month))

            # Initialize row_data with defaults for all fields for this specific month and publisher
            row_data = {
                'Date': f"{current_year:04d}-{current_month:02d}",
                'FirstName': first_name,
                'LastName': last_name,
                'SharedInMinistry': False,
                'BibleStudies': '',
                'AP': False,
                'Hours': '',
                'Credit': '',
                'Remarks': ''
            }

            if report_data:
                # If a report exists for this publisher and month, populate from it
                
                # Determine shared_in_ministry status:
                # 1. Infer from activity (minutes, studies)
                # 2. Allow explicit has_reported_field_service: False to override inference.
                # 3. If has_reported_field_service is True, it confirms service.
                # 4. If has_reported_field_service is missing/None, rely on inference.

                inferred_shared_in_ministry = False
                minutes_raw = report_data.get('minutes')
                if minutes_raw is not None:
                    try:
                        if int(minutes_raw) > 0:
                            inferred_shared_in_ministry = True
                    except (ValueError, TypeError):
                        pass 
                
                if not inferred_shared_in_ministry: # Only check studies if minutes didn't make it true
                    studies_raw = report_data.get('studies')
                    if studies_raw is not None:
                        try:
                            if int(studies_raw) > 0:
                                inferred_shared_in_ministry = True
                        except (ValueError, TypeError):
                            pass
                
                has_reported_flag = report_data.get('has_reported_field_service')
                
                shared_in_ministry_final = False # Initialize final determination
                if has_reported_flag is False:    # Explicitly False in JSON overrides inference
                    shared_in_ministry_final = False
                elif has_reported_flag is True:   # Explicitly True in JSON confirms service
                    shared_in_ministry_final = True
                else:                             # Flag is missing (None) or other, rely on inference
                    shared_in_ministry_final = inferred_shared_in_ministry
                
                row_data['SharedInMinistry'] = shared_in_ministry_final
                # Use shared_in_ministry_final for the subsequent conditional block
                # To avoid confusion, let's rename the variable used in the 'if' condition
                # The original 'shared_in_ministry' variable will now hold the final correct value.
                shared_in_ministry = shared_in_ministry_final


                actual_remarks = report_data.get('remarks')
                if isinstance(actual_remarks, str) and actual_remarks.strip():
                    row_data['Remarks'] = actual_remarks.strip()
                
                if shared_in_ministry:
                    # AP Status
                    pioneer_status = report_data.get('pioneer')
                    if pioneer_status == 'Auxiliary':
                        row_data['AP'] = True

                    # Hours
                    minutes_raw = report_data.get('minutes')
                    if minutes_raw is not None:
                        try:
                            minutes_val = int(minutes_raw)
                            if minutes_val > 0:
                                hours_calculated = minutes_val // 60
                                if hours_calculated > 0:
                                    row_data['Hours'] = str(hours_calculated)
                        except (ValueError, TypeError):
                            pass 

                    # Bible Studies
                    studies_raw = report_data.get('studies')
                    if studies_raw is not None:
                        try:
                            studies_val = int(studies_raw)
                            if studies_val > 0:
                                row_data['BibleStudies'] = str(studies_val)
                        except (ValueError, TypeError):
                            pass 
                    
                    # Credit Hours
                    credit_raw = report_data.get('credithours')
                    if credit_raw is not None and str(credit_raw).strip():
                        try:
                            numeric_credit_val = float(str(credit_raw))
                            if numeric_credit_val > 0:
                                if numeric_credit_val.is_integer():
                                    row_data['Credit'] = str(int(numeric_credit_val))
                                else:
                                    row_data['Credit'] = str(numeric_credit_val)
                        except (ValueError, TypeError):
                            pass
                # else for shared_in_ministry: AP, Hours, BibleStudies, Credit remain False or '' (their defaults)
            # else for report_data: all fields remain their defaults for this month

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
