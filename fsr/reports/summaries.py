"""
Commands for generating summary reports.
"""
import click
import datetime
from collections import defaultdict 
from fsr.core.data_loader import CongregationData
from fsr.core.utils import parse_year_month

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
        click.echo(f"Info: --month not provided, defaulting to previous month ({target_month_str}).") # No fg="blue"

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(f"Error: Invalid month format. {e}", err=True)
        ctx.abort()
        return

    # Calculate 6-month window for "Tous les proclamateurs actifs"
    six_month_tuples = []
    calc_yr, calc_mth = target_year, target_month
    for _ in range(6):
        six_month_tuples.append((calc_yr, calc_mth))
        calc_mth -= 1
        if calc_mth == 0:
            calc_mth = 12
            calc_yr -= 1

    publishers_active_in_last_six_months = set()

    # Initialization for single-month (target_month) French Report Details
    active_sps_for_target_month_set = set()
    active_rps_for_target_month_set = set()
    active_aps_for_target_month_set = set()
    active_pubs_for_target_month_set = set()

    rp_minutes_target_month = 0
    rp_studies_target_month = 0
    ap_minutes_target_month = 0
    ap_studies_target_month = 0
    pub_minutes_target_month = 0
    pub_studies_target_month = 0

    # Processing Loop
    for (pub_id, r_year, r_month), report_data in cong_data.reports_by_publisher_month_year.items():
        # 6-Month Window Check for "Tous les proclamateurs actifs"
        # Any report in the window counts the publisher.
        if (r_year, r_month) in six_month_tuples:
            publishers_active_in_last_six_months.add(pub_id)

        # Process data only for the single target_month for detailed category stats
        if not (r_year == target_year and r_month == target_month):
            continue

        publisher_details = cong_data.publishers_by_id.get(pub_id, {})
        pioneer_status_from_report = report_data.get('pioneer')

        is_special_pioneer = (pioneer_status_from_report == 'Special' or
                              publisher_details.get('reportstobranch') is True)
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

        is_active_this_month = parsed_minutes > 0 or parsed_studies > 0

        if is_active_this_month:
            if is_special_pioneer:
                active_sps_for_target_month_set.add(pub_id)
                # SP minutes/studies do NOT contribute to category totals for this French report.
            elif is_regular_pioneer:
                active_rps_for_target_month_set.add(pub_id)
                rp_minutes_target_month += parsed_minutes
                rp_studies_target_month += parsed_studies
            elif is_aux_pioneer:
                active_aps_for_target_month_set.add(pub_id)
                ap_minutes_target_month += parsed_minutes
                ap_studies_target_month += parsed_studies
            elif is_publisher_only:
                active_pubs_for_target_month_set.add(pub_id)
                pub_minutes_target_month += parsed_minutes
                pub_studies_target_month += parsed_studies

    # Populate summary_elements for French Report
    summary_elements = {}
    summary_elements['tous_les_proclamateurs_actifs'] = len(publishers_active_in_last_six_months)

    summary_elements['pub_s4_count'] = len(active_pubs_for_target_month_set)
    summary_elements['pub_studies'] = pub_studies_target_month
    summary_elements['pub_hours'] = f"{pub_minutes_target_month / 60.0:.2f}"

    summary_elements['ap_s4_count'] = len(active_aps_for_target_month_set)
    summary_elements['ap_hours'] = f"{ap_minutes_target_month / 60.0:.2f}"
    summary_elements['ap_studies'] = ap_studies_target_month

    summary_elements['rp_s4_count'] = len(active_rps_for_target_month_set)
    summary_elements['rp_hours'] = f"{rp_minutes_target_month / 60.0:.2f}"
    summary_elements['rp_studies'] = rp_studies_target_month

    summary_elements['assistance_moyenne_we'] = cong_data.monthly_attendance_weekend_avg.get((target_year, target_month), 0)

    # Outputting the Report (French Format)
    # No main title, month, or creation date, or initial "---" line to match target structure.

    click.echo("Tous les proclamateurs actifs")
    click.echo(summary_elements['tous_les_proclamateurs_actifs'])

    click.echo("Assistance moyenne à la réunion de week-end")
    click.echo(summary_elements['assistance_moyenne_we'] if summary_elements['assistance_moyenne_we'] else "N/A")

    click.echo("\nPROCLAMATEURS")
    click.echo("Nombre de fiches d’activité (S-4)")
    click.echo(summary_elements['pub_s4_count'])
    click.echo("Cours bibliques")
    click.echo(summary_elements['pub_studies'])
    # click.echo("Heures") # Removed as per requirement
    # click.echo(summary_elements['pub_hours']) # Removed as per requirement

    click.echo("\nPIONNIERS AUXILIAIRES")
    click.echo("Nombre de fiches d’activité (S-4)")
    click.echo(summary_elements['ap_s4_count'])
    click.echo("Heures")
    click.echo(summary_elements['ap_hours'])
    click.echo("Cours bibliques")
    click.echo(summary_elements['ap_studies'])

    click.echo("\nPIONNIERS PERMANENTS")
    click.echo("Nombre de fiches d’activité (S-4)")
    click.echo(summary_elements['rp_s4_count'])
    click.echo("Heures")
    click.echo(summary_elements['rp_hours'])
    click.echo("Cours bibliques")
    click.echo(summary_elements['rp_studies'])

    # No final separator.
    # The "Note" should only appear if there's genuinely no activity to show *at all*
    # for the main 'tous_les_proclamateurs_actifs' (6-month window).
    if summary_elements['tous_les_proclamateurs_actifs'] == 0:
         click.echo(f"\nNote: Aucune donnée d'activité disponible pour le mois {target_month_str}.")
