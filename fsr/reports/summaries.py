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
    Generates a monthly activity summary report using the new format.
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
        click.echo(f"Info: --month not provided, defaulting to previous month ({target_month_str}).", fg="blue")

    try:
        target_year, target_month = parse_year_month(target_month_str)
    except ValueError as e:
        click.echo(f"Error: Invalid month format. {e}", err=True)
        ctx.abort()
        return

    # Initialization
    categorized_s4_counts = {
        'publishers': set(),
        'aux_pioneers': set(),
        'reg_pioneers': set()
    }
    categorized_minutes = defaultdict(int)
    categorized_studies = defaultdict(int)

    active_non_sp_publishers_set = set() # For average calculations (denominator)
    total_non_sp_reporters_set = set()   # For "Kantite pwoklamatè" and "Tous les proclamateurs actifs" (excluding SPs)

    special_pioneer_reporters_count = 0 # Count of SPs who reported

    total_minutes_for_report_display = 0 # Sum of minutes from non-SPs
    total_studies_for_report_display = 0 # Sum of studies from non-SPs

    # Processing Loop
    for (pub_id, r_year, r_month), report_data in cong_data.reports_by_publisher_month_year.items():
        if not (r_year == target_year and r_month == target_month):
            continue

        publisher_details = cong_data.publishers_by_id.get(pub_id, {})
        pioneer_status_from_report = report_data.get('pioneer') # Status from S-1 report

        # Determine if Special Pioneer
        is_special_pioneer = (pioneer_status_from_report == 'Special' or
                              publisher_details.get('reportstobranch') is True)

        if is_special_pioneer:
            special_pioneer_reporters_count += 1
            # SPs are excluded from all other detailed stats in this report version
            continue

        # If NOT a Special Pioneer:
        total_non_sp_reporters_set.add(pub_id) # Count this non-SP publisher as having reported

        current_minutes_raw = report_data.get('minutes')
        current_studies_raw = report_data.get('studies')

        current_minutes = 0
        if current_minutes_raw is not None:
            try:
                minutes_val = int(current_minutes_raw)
                if minutes_val > 0:
                    current_minutes = minutes_val
            except (ValueError, TypeError):
                pass
        
        current_studies = 0
        if current_studies_raw is not None:
            try:
                studies_val = int(current_studies_raw)
                if studies_val > 0:
                    current_studies = studies_val
            except (ValueError, TypeError):
                pass
        
        # Determine category for non-SP
        category_key = ''
        if pioneer_status_from_report == 'Auxiliary':
            category_key = 'aux_pioneers'
        elif pioneer_status_from_report == 'Regular':
            category_key = 'reg_pioneers'
        else:
            category_key = 'publishers' # Default to publishers

        categorized_s4_counts[category_key].add(pub_id)
        categorized_minutes[category_key] += current_minutes
        categorized_studies[category_key] += current_studies

        total_minutes_for_report_display += current_minutes
        total_studies_for_report_display += current_studies
        
        # Active for averages means positive minutes OR studies
        if current_minutes > 0 or current_studies > 0:
            active_non_sp_publishers_set.add(pub_id)

    # Post-Loop Calculations
    val_kantite_pwoklamate_header = len(total_non_sp_reporters_set)
    val_pyonye_permanan_count = len(categorized_s4_counts['reg_pioneers'])
    val_pyonye_oksilye_count = len(categorized_s4_counts['aux_pioneers'])
    val_pwoklamate_count = len(categorized_s4_counts['publishers'])

    val_total_edtans = total_minutes_for_report_display / 60.0
    val_total_etid_biblik = total_studies_for_report_display

    val_mwayen_pwoklamate_patisipe = len(active_non_sp_publishers_set)

    val_mwayen_edtan = (val_total_edtans / val_mwayen_pwoklamate_patisipe) if val_mwayen_pwoklamate_patisipe > 0 else 0.0
    val_mwayen_etid = (val_total_etid_biblik / val_mwayen_pwoklamate_patisipe) if val_mwayen_pwoklamate_patisipe > 0 else 0.0

    val_kantite_pwoklamate_lengwistik = 0 # Assuming 0 for now, logic can be added if data is available
    val_tous_les_proclamateurs_actifs = val_kantite_pwoklamate_header # This line now excludes SPs
    val_pyonye_espesyal_count = special_pioneer_reporters_count # This is the count of SPs who reported
                                                              # but per instructions, the line in report should show 0.
                                                              # So, we'll use a hardcoded 0 for display on that line.

    avg_weekend_attendance = cong_data.monthly_attendance_weekend_avg.get((target_year, target_month), 0)

    # Outputting the Report (Haitian Creole Format)
    # Note: The subtask implies the line "Pyonye espesyal" should display 0.
    # The "Kantite pwoklamatè" and "Tous les proclamateurs actifs" lines should exclude SPs.

    click.echo(f"RAPÒ AKTIVITE PREDIKASYON ASANBLE POU {target_month_str.split('-')[1].upper()} {target_year}") # Simplified month name for now
    click.echo(f"\nRapò kreye: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}") # Added by convention, can be removed if not in expected output

    click.echo(f"\nKantite pwoklamatè................................. {val_kantite_pwoklamate_header}")
    click.echo(f"Pyonye pèmanan.................................... {val_pyonye_permanan_count}")
    click.echo(f"Pyonye oksilyè.................................... {val_pyonye_oksilye_count}")
    click.echo(f"Pwoklamatè........................................ {val_pwoklamate_count}")
    click.echo(f"Total èdtan....................................... {val_total_edtans:.2f}")
    click.echo(f"Total etid biblik................................. {val_total_etid_biblik}")
    click.echo(f"Mwayèn pwoklamatè ki patisipe nan ministè a chak mwa.... {val_mwayen_pwoklamate_patisipe}")
    click.echo(f"Mwayèn èdtan chak pwoklamatè fè................... {val_mwayen_edtan:.2f}")
    click.echo(f"Mwayèn etid biblik chak pwoklamatè fè............. {val_mwayen_etid:.2f}")
    click.echo(f"Kantite pwoklamatè ki lengwistik.................. {val_kantite_pwoklamate_lengwistik}")
    click.echo(f"Tous les proclamateurs actifs..................... {val_tous_les_proclamateurs_actifs}") # Excludes SP
    click.echo(f"Pyonye espesyal................................... 0") # Hardcoded to 0 as per instruction
    click.echo(f"Assistance moyenne à la réunion de week-end....... {avg_weekend_attendance if avg_weekend_attendance else 0}")


    # Fallback "no data" note if no non-SP publishers reported
    if val_kantite_pwoklamate_header == 0 and special_pioneer_reporters_count == 0:
         click.echo(f"\nNote: Pa gen rapò ki disponib pou mwa {target_month_str}.")
