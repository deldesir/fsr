"""
Commands for generating summary reports.
"""
import click
import datetime
from collections import defaultdict 
from fsr.core.data_loader import CongregationData
from fsr.core.utils import parse_year_month
# Unused imports get_publisher_role, format_minutes_to_hr_min, 
# ALL_PIONEER_ROLES, ROLE_NON_PIONEER were here.

@click.group('summary')
def summary_group():
    """Commands for generating summary reports."""
    pass

@summary_group.command('monthly-activity')
@click.option('--month', 'target_month_str', required=False, default=None, help="The month for the report in YYYY-MM format. Defaults to the current month if not provided.")
@click.pass_context
def monthly_activity_report(ctx: click.Context, target_month_str: str):
    """
    Generates a monthly activity summary report using the new format.
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo("Error: Congregation data not loaded. Run with --json-file option.", err=True)
        ctx.abort()
        return

    cong_data: CongregationData = ctx.obj['cong_data']

    if target_month_str is None:
        now = datetime.datetime.now()
        target_month_str = now.strftime("%Y-%m")
        click.echo(f"Info: --month not provided, defaulting to current month ({target_month_str}).")

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(f"Error: Invalid month format. {e}", err=True)
        ctx.abort()
        return

    # Initialize Summary Data Structures (New)
    summary_data = {
        'publishers': defaultdict(int),      # For 'Proclamateurs'
        'aux_pioneers': defaultdict(int),    # For 'Pionniers auxiliaires'
        'reg_pioneers': defaultdict(int),    # For 'Pionniers permanents'
    }
    reporting_publishers_by_category = {
        'publishers': set(),
        'aux_pioneers': set(),
        'reg_pioneers': set(),
    }
    all_active_reporters = set() # To count unique publishers who reported (excluding special)

    # Processing Loop
    for (pub_id, r_year, r_month), report in cong_data.reports_by_publisher_month_year.items():
        if not (r_year == target_year and r_month == target_month):
            continue

        # Exclude Special Pioneers
        if report.get('pioneer') == 'Special':
            continue

        # Infer has_reported_service and get current_minutes, current_studies
        minutes_raw = report.get('minutes')
        studies_raw = report.get('studies')

        has_reported_service = False
        current_minutes = 0
        current_studies = 0

        if minutes_raw is not None:
            try:
                current_minutes = int(minutes_raw)
                if current_minutes < 0: current_minutes = 0 # Treat negative as zero
                if current_minutes > 0:
                    has_reported_service = True
            except (ValueError, TypeError):
                current_minutes = 0
        
        if studies_raw is not None:
            try:
                current_studies = int(studies_raw)
                if current_studies < 0: current_studies = 0 # Treat negative as zero
                if current_studies > 0:
                    has_reported_service = True 
            except (ValueError, TypeError):
                current_studies = 0
        
        if report.get('has_reported_field_service') == False:
            has_reported_service = False
            current_minutes = 0
            current_studies = 0

        if not has_reported_service:
            continue 

        all_active_reporters.add(pub_id)

        # Categorize Publisher (Revised)
        pioneer_status_from_report = report.get('pioneer')
        category_key = ''
        if pioneer_status_from_report == 'Auxiliary':
            category_key = 'aux_pioneers'
        elif pioneer_status_from_report == 'Regular':
            category_key = 'reg_pioneers'
        else: 
            category_key = 'publishers' # Default to publishers
        
        # Aggregate Data
        summary_data[category_key]['minutes'] += current_minutes
        summary_data[category_key]['studies'] += current_studies
        reporting_publishers_by_category[category_key].add(pub_id)

    # Post-Loop Calculations
    for cat_key, cat_data in summary_data.items():
        cat_data['count'] = len(reporting_publishers_by_category[cat_key])
        cat_data['hours_display'] = cat_data.get('minutes', 0) // 60

    total_active_publishers_count = len(all_active_reporters)

    # Fetch Meeting Attendance
    avg_weekend_attendance = cong_data.monthly_attendance_weekend_avg.get((target_year, target_month), 0)

    # Outputting the Report (New Format)
    click.echo(click.style("Rezime Rapò Aktivite Mansyèl", bold=True))
    click.echo(f"Pou Mwa: {target_month_str}")
    click.echo(f"Rapò kreye: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    click.echo("-----------------------------")

    click.echo("Tous les proclamateurs actifs")
    click.echo(total_active_publishers_count)

    click.echo("Assistance moyenne à la réunion de week-end")
    click.echo(avg_weekend_attendance if avg_weekend_attendance else "N/A")

    # Proclamateurs (Publishers)
    click.echo("\nProclamateurs")
    click.echo("Nombre de fiches d’activité (S-4)")
    click.echo(summary_data['publishers'].get('count', 0))
    click.echo("Cours bibliques")
    click.echo(summary_data['publishers'].get('studies', 0))

    # Pionniers auxiliaires
    click.echo("\nPionniers auxiliaires")
    click.echo("Nombre de fiches d’activité (S-4)")
    click.echo(summary_data['aux_pioneers'].get('count', 0))
    click.echo("Heures")
    click.echo(summary_data['aux_pioneers'].get('hours_display', 0))
    click.echo("Cours bibliques")
    click.echo(summary_data['aux_pioneers'].get('studies', 0))

    # Pionniers permanents
    click.echo("\nPionniers permanents")
    click.echo("Nombre de fiches d’activité (S-4)")
    click.echo(summary_data['reg_pioneers'].get('count', 0))
    click.echo("Heures")
    click.echo(summary_data['reg_pioneers'].get('hours_display', 0))
    click.echo("Cours bibliques")
    click.echo(summary_data['reg_pioneers'].get('studies', 0))
    
    click.echo("\n-----------------------------")
    # Check if any report data exists or attendance exists before printing no data note
    no_report_data = total_active_publishers_count == 0
    no_attendance_data = not avg_weekend_attendance # Assuming 0 or "N/A" means no data for this context

    # More precise check: if all specific counts are zero and attendance is zero/NA
    all_counts_zero = all(summary_data[cat_key].get('count', 0) == 0 for cat_key in summary_data)


    if all_counts_zero and no_attendance_data : # If no publishers reported and no attendance data
        click.echo(f"\nNote: Pa gen rapò ki disponib pou mwa {target_month_str}.")
