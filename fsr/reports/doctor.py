"""`fsr doctor` — diagnose what fsr can (and cannot) see.

The exporters auto-detect their inputs, which is convenient right up until a
file is missing or stale and a command silently exports less than expected.
This command makes discovery explicit: which Hourglass JSON and program docx
would be used, how fresh they are, whether the S-34 corpus is available for
outline resolution, and which exports are therefore possible right now.
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path

import click

from fsr.core.file_finder import find_docx_file, find_json_file


def _ok(label: str, detail: str) -> None:
    click.echo(click.style('  ✔ ', fg='green') + f"{label}: {detail}")


def _warn(label: str, detail: str, hint: str = '') -> None:
    click.echo(click.style('  ✖ ', fg='red') + f"{label}: {detail}")
    if hint:
        click.echo(click.style(f"      ↳ {hint}", fg='yellow'))


def _age(path: str) -> str:
    mtime = datetime.fromtimestamp(Path(path).stat().st_mtime)
    days = (datetime.now() - mtime).days
    when = mtime.strftime('%Y-%m-%d %H:%M')
    if days <= 0:
        return f"{when} (today)"
    return f"{when} ({days} day{'s' if days != 1 else ''} old)"


@click.command('doctor')
@click.option('--s34-db', default='/library/jwlinker/jw_library.db',
              show_default=True, help='jwlinker corpus DB to check.')
def doctor(s34_db: str):
    """Show what fsr auto-detects and which exports are possible."""
    click.echo(click.style('fsr environment check', bold=True))

    click.echo('\nInputs:')
    try:
        json_path = find_json_file()
    except ValueError:
        json_path = None
    if json_path:
        _ok('Hourglass JSON', f"{json_path} — {_age(json_path)}")
    else:
        _warn('Hourglass JSON', 'not found',
              "export it from Hourglass and drop it in the current "
              "directory, Downloads, or /library/hourglass "
              "(expected name: hourglass-export*.json)")

    docx_path = find_docx_file()
    if docx_path:
        _ok('Program docx', f"{docx_path} — {_age(docx_path)}")
    else:
        _warn('Program docx', 'not found',
              "export 'Tout pwogram ansanm' from Hourglass and drop it in "
              "the current directory, Downloads, or /library/hourglass")

    if Path(s34_db).exists():
        try:
            conn = sqlite3.connect(s34_db)
            count = conn.execute(
                "SELECT count(*) FROM Topics t "
                "JOIN Categories c ON t.category_id=c.id "
                "JOIN Publications p ON c.publication_id=p.id "
                "WHERE p.code='s34'").fetchone()[0]
            conn.close()
            _ok('S-34 corpus', f"{s34_db} — {count} outline topics")
        except sqlite3.Error as e:
            _warn('S-34 corpus', f"unreadable ({e})",
                  'public-talk outline numbers will be 0')
    else:
        _warn('S-34 corpus', f"{s34_db} not found",
              'public-talk outline numbers will be 0 (titles still export)')

    out_dir = os.getcwd()
    writable = os.access(out_dir, os.W_OK)
    click.echo('\nOutput:')
    if writable:
        _ok('Working directory', f"{out_dir} (writable)")
    else:
        _warn('Working directory', f"{out_dir} is NOT writable",
              'cd somewhere writable or pass explicit output paths')

    click.echo('\nExports possible right now:')
    rows = [
        ('field-service (NWS CSV)', bool(json_path)),
        ('midweek-program (NWS CSV)', bool(docx_path)),
        ('public-talks (NWS CSV)', bool(docx_path)),
        ('organized (unified JSON)', bool(json_path and docx_path)),
    ]
    for name, possible in rows:
        mark = click.style('✔', fg='green') if possible \
            else click.style('✖', fg='red')
        click.echo(f"  {mark} fsr export {name}")

    if all(possible for _, possible in rows):
        click.echo(click.style(
            "\nAll set — `fsr export all` produces everything in one run.",
            fg='green'))
