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
@click.option('--month', 'target_month_str', required=False, default=None, help="The month for the report in YYYY-MM format. Defaults to the *previous* month if not provided.")
@click.pass_context
def monthly_activity_report(ctx: click.Context, target_month_str: str):
    """
    Generates a monthly activity summary report (French-labeled).
    """
    if 'cong_data' not in ctx.obj or not isinstance(ctx.obj['cong_data'], CongregationData):
        click.echo("Error: Congregation data not loaded. Run with --json-file option.", err=True)
        ctx.abort()
        return

    cong_data: CongregationData = ctx.obj['cong_data']

    if target_month_str is None:
        now = datetime.datetime.now()
        first_day_of_current_month = now.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
        target_month_str = last_day_of_previous_month.strftime('%Y-%m')
        click.echo(f"Info: --month not provided, defaulting to previous month ({target_month_str}).")

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(f"Error: Invalid month format. {e}", err=True)
        ctx.abort()
        return

    # Initialization for French Report Logic
    active_sps_set = set()
    active_rps_set = set()
    active_aps_set = set()
    active_pubs_set = set()

    rp_minutes_total = 0
    rp_studies_total = 0
    ap_minutes_total = 0
    ap_studies_total = 0
    pub_minutes_total = 0 # For "Proclamateurs" hours (new for French format)
    pub_studies_total = 0

    # Processing Loop
    for (pub_id, r_year, r_month), report_data in cong_data.reports_by_publisher_month_year.items():
        if not (r_year == target_year and r_month == target_month):
            continue

        publisher_details = cong_data.publishers_by_id.get(pub_id, {})
        pioneer_status_from_report = report_data.get('pioneer')

        is_special_pioneer = (pioneer_status_from_report == 'Special' or
                              publisher_details.get('reportstobranch') is True)

        # This check for 'is_regular_pioneer' needs to ensure they are not also SP
        is_regular_pioneer = pioneer_status_from_report == 'Regular' and not is_special_pioneer
        is_aux_pioneer = pioneer_status_from_report == 'Auxiliary' and not is_special_pioneer
        is_publisher_only = not is_special_pioneer and not is_regular_pioneer and not is_aux_pioneer

        parsed_minutes = 0
        raw_minutes = report_data.get('minutes')
        if raw_minutes is not None:
            try:
                minutes_val = int(raw_minutes)
                if minutes_val > 0:
                    parsed_minutes = minutes_val
            except (ValueError, TypeError):
                pass
        
        parsed_studies = 0
        raw_studies = report_data.get('studies')
        if raw_studies is not None:
            try:
                studies_val = int(raw_studies)
                if studies_val > 0:
                    parsed_studies = studies_val
            except (ValueError, TypeError):
                pass

        is_active_for_month = parsed_minutes > 0 or parsed_studies > 0

        if is_active_for_month:
            if is_special_pioneer:
                active_sps_set.add(pub_id)
            elif is_regular_pioneer:
                active_rps_set.add(pub_id)
                rp_minutes_total += parsed_minutes
                rp_studies_total += parsed_studies
            elif is_aux_pioneer:
                active_aps_set.add(pub_id)
                ap_minutes_total += parsed_minutes
                ap_studies_total += parsed_studies
            elif is_publisher_only: # General Publisher
                active_pubs_set.add(pub_id)
                pub_minutes_total += parsed_minutes
                pub_studies_total += parsed_studies

    # Populate summary_elements for French Report
    summary_elements = {}
    summary_elements['tous_les_proclamateurs_actifs'] = len(active_sps_set) + len(active_rps_set) + len(active_aps_set) + len(active_pubs_set)

    summary_elements['pub_s4_count'] = len(active_pubs_set)
    summary_elements['pub_studies'] = pub_studies_total
    summary_elements['pub_hours'] = f"{pub_minutes_total / 60.0:.2f}" # Publishers now have hours in this format

    summary_elements['ap_s4_count'] = len(active_aps_set)
    summary_elements['ap_hours'] = f"{ap_minutes_total / 60.0:.2f}"
    summary_elements['ap_studies'] = ap_studies_total

    summary_elements['rp_s4_count'] = len(active_rps_set)
    summary_elements['rp_hours'] = f"{rp_minutes_total / 60.0:.2f}"
    summary_elements['rp_studies'] = rp_studies_total

    summary_elements['assistance_moyenne_we'] = cong_data.monthly_attendance_weekend_avg.get((target_year, target_month), 0)

    # Outputting the Report (French Format - revised structure)
    # No main title, month, or creation date to match target structure exactly.
    # Dot leader padding is not implemented; focusing on labels, order, and values.

    click.echo("Tous les proclamateurs actifs") # Label
    click.echo(summary_elements['tous_les_proclamateurs_actifs']) # Value

    click.echo("Assistance moyenne à la réunion de week-end") # Label
    click.echo(summary_elements['assistance_moyenne_we'] if summary_elements['assistance_moyenne_we'] else "N/A") # Value

    # Proclamateurs (Publishers)
    click.echo("\nPROCLAMATEURS") # Section Title (all caps as per target)
    click.echo("Nombre de fiches d’activité (S-4)") # Label
    click.echo(summary_elements['pub_s4_count']) # Value
    click.echo("Cours bibliques") # Label
    click.echo(summary_elements['pub_studies']) # Value
    click.echo("Heures") # Label
    click.echo(summary_elements['pub_hours']) # Value

    # Pionniers auxiliaires
    click.echo("\nPIONNIERS AUXILIAIRES") # Section Title
    click.echo("Nombre de fiches d’activité (S-4)") # Label
    click.echo(summary_elements['ap_s4_count']) # Value
    click.echo("Heures") # Label
    click.echo(summary_elements['ap_hours']) # Value
    click.echo("Cours bibliques") # Label
    click.echo(summary_elements['ap_studies']) # Value

    # Pionniers permanents
    click.echo("\nPIONNIERS PERMANENTS") # Section Title
    click.echo("Nombre de fiches d’activité (S-4)") # Label
    click.echo(summary_elements['rp_s4_count']) # Value
    click.echo("Heures") # Label
    click.echo(summary_elements['rp_hours']) # Value
    click.echo("Cours bibliques") # Label
    click.echo(summary_elements['rp_studies']) # Value

    # No final separator as per target structure
    if summary_elements['tous_les_proclamateurs_actifs'] == 0:
         click.echo(f"\nNote: Aucune donnée d'activité disponible pour le mois {target_month_str}.") # French note
