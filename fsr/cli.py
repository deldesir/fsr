"""
Main CLI entry point for the Congregation Reporter.
"""
import click
import sys
import json # Required for json.JSONDecodeError
from typing import Optional

from fsr.core.constants import DEFAULT_JSON_TYPE_KEY, CONFIGURABLE_JSON_TYPES
from fsr.core.cli_utils import AliasedGroup
from fsr.core.data_loader import load_and_prepare_data, CongregationData
from fsr.core.file_finder import find_json_file

@click.group(cls=AliasedGroup, aliases={
    'x': 'export', 'exp': 'export',
    'sum': 'summary',
    'dr': 'doctor', 'check': 'doctor',
})
@click.version_option(package_name='fsr', prog_name='fsr')
@click.option(
    '--json-file',
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    required=False,
    default=None,
    help="Path to the congregation JSON data file. Optional; if not provided, attempts to auto-detect."
)
@click.option(
    '--json-type',
    type=click.Choice(list(CONFIGURABLE_JSON_TYPES.keys()), case_sensitive=False),
    default=DEFAULT_JSON_TYPE_KEY,
    show_default=True,
    help="Specify the type of JSON file to auto-detect (e.g., 'hourglass'). Used when --json-file is not provided."
)
@click.pass_context
def cli(ctx: click.Context, json_file: Optional[str], json_type: str):
    """
    Field Service Reporter (fsr) CLI.

    This tool processes JSON data to generate field service activity
    reports and exports.
    """
    ctx.ensure_object(dict) # Ensure ctx.obj exists and is a dict

    actual_json_file_path = json_file

    if actual_json_file_path is None:
        # Determine the display name for the JSON type being searched.
        # CONFIGURABLE_JSON_TYPES maps key to filename part, e.g., "hourglass" -> "hourglass-export"
        # For the message, we use the key itself, which is more user-friendly.
        json_type_display_name = json_type # This is the key like "hourglass"
        click.echo(f"Info: --json-file not provided. Attempting to auto-detect '{json_type_display_name}' JSON export...")
        try:
            actual_json_file_path = find_json_file(json_type_key=json_type)
        except ValueError as e:
            click.echo(click.style(f"Error: {e}", fg="red"), err=True)
            ctx.abort()

        if actual_json_file_path is None:
            # Not fatal: docx-driven commands (export midweek-program /
            # public-talks) need no JSON. Commands that DO need it already
            # check ctx.obj['cong_data'] and error out with guidance.
            click.echo(click.style(
                f"Info: no '{json_type_display_name}' JSON export found — "
                "continuing without congregation data (program exports from "
                "the .docx still work).", fg="yellow"))
            return
        else:
            click.echo(click.style(f"Info: Auto-detected '{json_type_display_name}' JSON file: {actual_json_file_path}", fg="green"))

    try:
        cong_data = load_and_prepare_data(actual_json_file_path)
        if cong_data is None: # Should not happen if exceptions are raised properly
            click.echo("Error: Failed to load data. The loader returned None.", err=True)
            ctx.abort()

        ctx.obj['cong_data'] = cong_data
        # Store the actual path used, whether provided or detected
        ctx.obj['json_file_path'] = actual_json_file_path

    except FileNotFoundError: # Handles case where a path was given via option but file doesn't exist (Path(exists=True) should catch this, but good to be robust)
        click.echo(f"Error: The file '{actual_json_file_path}' was not found.", err=True)
        ctx.abort()
    except json.JSONDecodeError as e:
        click.echo(f"Error: Failed to decode JSON from '{actual_json_file_path}'. Invalid JSON format. Details: {e}", err=True)
        ctx.abort()
    except KeyError as e:
        click.echo(f"Error: Missing essential data key {e} in '{actual_json_file_path}'. The file structure is not as expected.", err=True)
        ctx.abort()
    except Exception as e: # Catch any other unexpected errors during data loading
        click.echo(f"An unexpected error occurred during data loading from '{actual_json_file_path}': {e}", err=True)
        ctx.abort()

from fsr.reports.summaries import summary_group
cli.add_command(summary_group)

from fsr.reports.exports import export_group
cli.add_command(export_group)

from fsr.reports.doctor import doctor
cli.add_command(doctor)

if __name__ == "__main__":
    # The type hint for json_file needs to be Optional[str] for the cli function
    # but click itself when running __main__ might not pass None if default is not specified at option level
    # However, with default=None, it should be fine.
    # from typing import Optional # No longer needed here as it's at the top
    cli(obj={}) # type: ignore
