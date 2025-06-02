"""
Main CLI entry point for the Congregation Reporter.
"""
import click
import sys
import json # Required for json.JSONDecodeError

from congregation_reporter.core.data_loader import load_and_prepare_data, CongregationData

@click.group()
@click.option(
    '--json-file',
    type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
    required=True,
    help="Path to the congregation JSON data file."
)
@click.pass_context
def cli(ctx: click.Context, json_file: str):
    """
    Field Service Reporter (fsr) CLI.

    This tool processes JSON data to generate field service activity
    reports and exports.
    """
    ctx.ensure_object(dict) # Ensure ctx.obj exists and is a dict

    try:
        cong_data = load_and_prepare_data(json_file)
        if cong_data is None: # Should not happen if exceptions are raised properly
            click.echo("Error: Failed to load data. The loader returned None.", err=True)
            ctx.abort()

        ctx.obj['cong_data'] = cong_data
        ctx.obj['json_file_path'] = json_file # Store for potential use in subcommands

    except FileNotFoundError as e:
        click.echo(f"Error: The file '{json_file}' was not found.", err=True)
        # load_and_prepare_data might print its own message, this is an additional one from CLI.
        ctx.abort()
    except json.JSONDecodeError as e:
        click.echo(f"Error: Failed to decode JSON from '{json_file}'. Invalid JSON format. Details: {e}", err=True)
        # load_and_prepare_data might print its own message.
        ctx.abort()
    except KeyError as e:
        click.echo(f"Error: Missing essential data key {e} in '{json_file}'. The file structure is not as expected.", err=True)
        # load_and_prepare_data might print its own message.
        ctx.abort()
    except Exception as e: # Catch any other unexpected errors during data loading
        click.echo(f"An unexpected error occurred during data loading: {e}", err=True)
        ctx.abort()

from .reports.summaries import summary_group
cli.add_command(summary_group)

from .reports.exports import export_group
cli.add_command(export_group)

if __name__ == "__main__":
    cli()
