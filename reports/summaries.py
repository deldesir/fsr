"""
Commands for generating summary reports.
"""
import click
from core.data_loader import CongregationData
from core.utils import get_publisher_role, format_minutes_to_hr_min, parse_year_month
from ..core.constants import ALL_PIONEER_ROLES, ROLE_NON_PIONEER

@click.group('summary')
def summary_group():
    """Commands for generating summary reports."""
    pass

@summary_group.command('monthly-activity')
@click.option('--month', 'target_month_str', required=True, help="The month for the report in YYYY-MM format.")
@click.pass_context
def monthly_activity_report(ctx: click.Context, target_month_str: str):
    """
    Generates a monthly activity summary report.
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo("Error: Congregation data not loaded. Run with --json-file option.", err=True)
        ctx.abort()
        return # Should be unreachable due to abort, but good for linters

    cong_data: CongregationData = ctx.obj['cong_data']

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(f"Error: Invalid month format. {e}", err=True)
        ctx.abort()
        return # Should be unreachable

    pioneer_total_minutes = 0
    pioneer_total_studies = 0
    publisher_total_studies = 0
    pioneer_ids_reporting = set()
    publisher_ids_reporting = set()

    for (pub_id, r_year, r_month), report in cong_data.reports_by_publisher_month_year.items():
        if r_year == target_year and r_month == target_month:
            # publisher_details = cong_data.publishers_by_id.get(pub_id) # Not strictly needed for this report
            # if not publisher_details:
            #     click.echo(f"Warning: Publisher ID {pub_id} from report not found in publisher list. Skipping report.", err=True)
            #     continue

            # The 'pioneer' field in the report itself should determine role for that month's activity
            role = get_publisher_role(report.get('pioneer'))
            minutes = report.get('minutes') if report.get('has_reported_field_service', False) else 0
            studies = report.get('studies') if report.get('has_reported_field_service', False) else 0

            # Ensure minutes and studies are integers, default to 0 if None or invalid
            try:
                minutes = int(minutes) if minutes is not None else 0
            except (ValueError, TypeError):
                minutes = 0

            try:
                studies = int(studies) if studies is not None else 0
            except (ValueError, TypeError):
                studies = 0

            if role in ALL_PIONEER_ROLES:
                if report.get('has_reported_field_service', False): # Only count if they reported service
                    pioneer_total_minutes += minutes
                    pioneer_total_studies += studies
                    pioneer_ids_reporting.add(pub_id)
            elif role == ROLE_NON_PIONEER: # Includes unbaptized publishers if they are in the system without a specific role
                if report.get('has_reported_field_service', False): # Only count if they reported service
                    # Non-pioneer minutes are not counted for this specific Haitian summary
                    publisher_total_studies += studies
                    publisher_ids_reporting.add(pub_id)
            # else: role is "Unknown" or something else, ignore. Or could add a warning.

    pioneer_reporter_count = len(pioneer_ids_reporting)
    publisher_reporter_count = len(publisher_ids_reporting)
    formatted_pioneer_hours = format_minutes_to_hr_min(pioneer_total_minutes)

    # Outputting the report
    click.echo("Monthly Activity Summary Report")
    click.echo("-----------------------------")
    click.echo(f"Month: {target_month_str}")
    # Using a generic "Report Generated:" timestamp, can be adjusted if a specific "data as of" date is available
    click.echo(f"Report Generated: {click.DateTime().strftime('%Y-%m-%d %H:%M')}")
    click.echo("-----------------------------")
    click.echo("--- Pioneers (Auxiliary, Regular, Special) ---")
    click.echo("-----------------------------")
    click.echo(f"Number of Pioneers Reporting: {pioneer_reporter_count}")
    click.echo(f"Total Hours: {formatted_pioneer_hours}")
    click.echo(f"Total Bible Studies (Pioneers): {pioneer_total_studies}")
    click.echo("-----------------------------")
    click.echo("--- Publishers (Non-Pioneer) ---")
    click.echo("-----------------------------")
    click.echo(f"Number of Publishers Reporting: {publisher_reporter_count}")
    click.echo(f"Total Bible Studies (Publishers): {publisher_total_studies}")
    click.echo("-----------------------------")
    click.echo(f"Total Congregation Bible Studies: {pioneer_total_studies + publisher_total_studies}")
    click.echo("-----------------------------")

    # Additional check for clarity:
    if not cong_data.reports_by_publisher_month_year:
        click.echo("\nNote: No reports recorded in the data.")
    elif pioneer_reporter_count == 0 and publisher_reporter_count == 0:
        click.echo(f"\nNote: No reports found for month {target_month_str}.")
