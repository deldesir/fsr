"""
Main CLI entry point for the Congregation Reporter.
"""
import click
import sys
import json # Required for json.JSONDecodeError
from typing import Optional

from core.data_loader import load_and_prepare_data, CongregationData
from core.file_finder import find_json_file

@click.group()
@click.option(
    '--json-file',
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    required=False,
    default=None,
    help="Path to the congregation JSON data file. Optional; if not provided, attempts to auto-detect common Hourglass export files."
)
@click.pass_context
def cli(ctx: click.Context, json_file: Optional[str]):
    """
    Field Service Reporter (fsr) CLI.

    This tool processes JSON data to generate field service activity
    reports and exports.
    """
    ctx.ensure_object(dict) # Ensure ctx.obj exists and is a dict

    actual_json_file_path = json_file

    if actual_json_file_path is None:
        click.echo("Info: --json-file not provided. Attempting to auto-detect Hourglass JSON export...")
        actual_json_file_path = find_json_file()
        if actual_json_file_path is None:
            click.echo(click.style("Error: Auto-detection failed. No suitable JSON file found in standard locations (current directory, Downloads).", fg="red"), err=True)
            click.echo(click.style("Please specify the file path using the --json-file option.", fg="red"), err=True)
            ctx.abort()
        else:
            click.echo(click.style(f"Info: Auto-detected JSON file: {actual_json_file_path}", fg="green"))

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

from .reports.summaries import summary_group # type: ignore
cli.add_command(summary_group)

from .reports.exports import export_group # type: ignore
cli.add_command(export_group)

if __name__ == "__main__":
    # The type hint for json_file needs to be Optional[str] for the cli function
    # but click itself when running __main__ might not pass None if default is not specified at option level
    # However, with default=None, it should be fine.
    # from typing import Optional # No longer needed here as it's at the top
    cli(obj={}) # type: ignore
