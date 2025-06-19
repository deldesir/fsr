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
@click.option('--month', 'target_month_str', required=True, help="The month for the report in YYYY-MM format.")
@click.pass_context
def monthly_activity_report(ctx: click.Context, target_month_str: str):
    """
    Generates a monthly activity summary report in French/Haitian Creole.
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

    # Initialize Summary Data Structures
    summary_data = {
        'pwoklamatè ki pa pyonye': defaultdict(int),
        'pyonye oksilyè': defaultdict(int),
        'pyonye pèmanan': defaultdict(int),
        'pyonye espesyal': defaultdict(int)
    }
    reporting_publishers_by_category = {
        'pwoklamatè ki pa pyonye': set(),
        'pyonye oksilyè': set(),
        'pyonye pèmanan': set(),
        'pyonye espesyal': set()
    }

    # Refactor Report Processing Loop
    for (pub_id, r_year, r_month), report in cong_data.reports_by_publisher_month_year.items():
        if not (r_year == target_year and r_month == target_month):
            continue

        # Infer has_reported_service and get current_minutes, current_studies
        minutes_raw = report.get('minutes')
        studies_raw = report.get('studies')
        # Placements and videos not considered for has_reported_service for now as per instruction

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
        
        # If explicitly marked as not sharing, override inference
        if report.get('has_reported_field_service') == False: # Check for explicit False
            has_reported_service = False
            # Reset potentially inferred values if has_reported_field_service is explicitly False
            current_minutes = 0
            current_studies = 0
            # Note: Credit hours are not part of this summary, so not reset here.

        if not has_reported_service:
            continue 

        # Categorize Publisher
        pioneer_status_from_report = report.get('pioneer')
        category_key = ''
        if pioneer_status_from_report == 'Auxiliary':
            category_key = 'pyonye oksilyè'
        elif pioneer_status_from_report == 'Regular':
            category_key = 'pyonye pèmanan'
        elif pioneer_status_from_report == 'Special':
            category_key = 'pyonye espesyal'
        else: 
            category_key = 'pwoklamatè ki pa pyonye'
        
        # Aggregate Data
        summary_data[category_key]['minutes'] += current_minutes
        summary_data[category_key]['studies'] += current_studies
        reporting_publishers_by_category[category_key].add(pub_id)

    # Prepare Data for Printing (After Loop)
    for cat_name_loop, cat_data_loop in summary_data.items():
        cat_data_loop['count'] = len(reporting_publishers_by_category[cat_name_loop])
        # Ensure minutes is an int before division
        cat_data_loop['hours_display'] = int(cat_data_loop.get('minutes', 0)) // 60


    # Helper function for printing (defined within or accessible)
    def print_category_summary(p_category_name, p_data, p_month_num, p_year_num):
        # Convert month number to month name if desired, or use number
        # For this example, directly using the number as in YYYY-MM format
        month_str = f"{p_month_num:02d}"
        click.echo(f"\n*Rapò pou {p_category_name.title()} ({month_str}-{p_year_num})*")
        # Only print hours for pioneer categories as per original logic implied
        if p_category_name != 'pwoklamatè ki pa pyonye':
            click.echo(f"Total Lè: {p_data.get('hours_display', 0)}")
        click.echo(f"Total Etid: {p_data.get('studies', 0)}") # Use .get for safety
        click.echo(f"_Te gen {p_data.get('count', 0)} {p_category_name.lower()} ki te bay rapò pou mwa sa._")

    # Refactor Printing Section
    click.echo(click.style("Rezime Rapò Aktivite Mansyèl", bold=True))
    # Use target_month_str for display as it's already in YYYY-MM
    click.echo(f"Pou Mwa: {target_month_str}") 
    click.echo(f"Rapò kreye: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    click.echo("-----------------------------")

    print_category_summary('pwoklamatè ki pa pyonye', summary_data['pwoklamatè ki pa pyonye'], target_month, target_year)
    print_category_summary('pyonye oksilyè', summary_data['pyonye oksilyè'], target_month, target_year)
    print_category_summary('pyonye pèmanan', summary_data['pyonye pèmanan'], target_month, target_year)
    print_category_summary('pyonye espesyal', summary_data['pyonye espesyal'], target_month, target_year)
    
    click.echo("\n-----------------------------")
    total_cong_studies = sum(s_data.get('studies', 0) for s_data in summary_data.values())
    click.echo(f"Total Etid Kongregasyon an: {total_cong_studies}")
    click.echo("-----------------------------")

    if sum(s_data.get('count', 0) for s_data in summary_data.values()) == 0:
        click.echo(f"\nNote: Pa gen rapò ki disponib pou mwa {target_month_str}.")
    
    # Confirm unused imports
    # get_publisher_role - Not used
    # format_minutes_to_hr_min - Not used (using direct // 60)
    # ALL_PIONEER_ROLES - Not used
    # ROLE_NON_PIONEER - Not used
    # These can be removed from the import statement.
    # This will be done in a separate step if this refactor is successful.
