"""Meeting-program exports for New World Scheduler.

Two commands that read the Hourglass "Tout pwogram ansanm" .docx (the only
place the meeting program leaves Hourglass — it is not in the JSON export)
and write the CSVs New World Scheduler imports:

  fsr export midweek-program   -> Date,Person,PartType,Assignment,School,LanguageGroupID
  fsr export public-talks      -> Date,Congregation,PublicSpeaker,OutlineNumber,
                                  OutlineName,Song,SpeakerConfirmed,Notes,
                                  LanguageGroupID,Chairman,WatchtowerReader,
                                  CustomWeekendAssignment1,CustomWeekendAssignment2,
                                  Hospitality

Formats match New World Scheduler's own exports byte-for-byte conventions:
UTF-8 with BOM, midweek dated by the week's Monday, public talks dated by the
Sunday itself, persons as "Firstname Lastname".

The public-talk outline number is not printed in the document (only the talk
title), so it is resolved against a jwlinker S-34 corpus database when one is
available (--s34-db); otherwise the number is 0 and the title is used as-is —
the same convention NWS uses for talks it cannot identify.
"""

import csv
import os
import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from fsr.core.docx_parser import (
    docx_rows, parse_midweek, parse_weekend, split_meetings, _fold,
)
from fsr.core.file_finder import find_docx_file, find_docx_files

DEFAULT_S34_DB = '/library/jwlinker/jw_library.db'


def _resolve_docx(docx_path: Optional[str]) -> str:
    if docx_path:
        return docx_path
    found = find_docx_file()
    if not found:
        raise click.ClickException(
            "No program .docx found (looked for 'Tout pwogram*.docx' in the "
            "current directory, Downloads and /library/hourglass). "
            "Pass --docx explicitly.")
    click.echo(click.style(f"Info: using program document: {found}", fg="green"))
    return found


def _resolve_docxs(docx_paths) -> list[str]:
    """All program documents to merge, oldest export first (so overlapping
    weeks resolve to the most recently exported data). Hourglass exports one
    month per .docx — merging the recent ones is what covers a quarter."""
    if docx_paths:
        return list(docx_paths)
    found = find_docx_files()
    if not found:
        raise click.ClickException(
            "No program .docx found (looked for 'Tout pwogram*.docx' in the "
            "current directory, Downloads and /library/hourglass). "
            "Pass --docx explicitly (repeatable).")
    ordered = list(reversed(found))
    for p in ordered:
        click.echo(click.style(f"Info: using program document: {p}", fg="green"))
    return ordered


def _load_meetings(docx_path: str):
    meetings = split_meetings(docx_rows(docx_path))
    if not meetings:
        raise click.ClickException(
            f"No meetings found in '{docx_path}' — is this the Hourglass "
            f"'all programs' export?")
    return meetings


def _monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _write_csv(path: str, fieldnames, rows, summary: str = '') -> None:
    tmp = path + '.tmp'
    # utf-8-sig: NWS's own exports carry a BOM.
    with open(tmp, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)
    detail = f" ({summary})" if summary else ''
    click.echo(click.style(
        f"CSV file '{path}' created successfully{detail}.", fg="green"))


def _default_out(stem: str) -> str:
    return os.path.join(
        os.getcwd(), f"NWScheduler_{stem}_{datetime.now():%Y%m%d}.csv")


def _bundled_titles(lang_id: str):
    """(number, folded_title) pairs from the packaged title index."""
    import importlib.resources as resources
    import json as _json

    try:
        data = _json.loads(
            resources.files('fsr').joinpath('data/s34_titles.json')
            .read_text(encoding='utf-8'))
    except (FileNotFoundError, OSError, ValueError):
        return []
    titles = data.get('titles', {}).get(str(lang_id), {})
    return [(int(num), _fold(title)) for num, title in titles.items()]


class OutlineResolver:
    """Talk title -> S-34 outline number via a jwlinker corpus database.

    The corpus stores topics under two naming formats ('103. Title' and
    'No 78 Title'); both are matched, accent- and case-insensitively.
    """

    def __init__(self, db_path: Optional[str], lang_id: str):
        self.titles = []
        self.source = 'none'
        if db_path and Path(db_path).exists():
            conn = sqlite3.connect(db_path)
            rows = conn.execute(
                "SELECT DISTINCT t.name FROM Topics t "
                "JOIN Categories c ON t.category_id=c.id "
                "JOIN Publications p ON c.publication_id=p.id "
                "WHERE p.code='s34' AND p.language=?", (lang_id,)).fetchall()
            conn.close()
            for (name,) in rows:
                m = re.match(r'(?:No\s+)?(\d+)[.\s]\s*(.*)', name)
                if m:
                    self.titles.append((int(m.group(1)), _fold(m.group(2))))
            if self.titles:
                self.source = 'corpus'
        if not self.titles:
            # Bundled fallback: a titles-only index shipped with the package,
            # so outline numbers resolve on machines without the corpus
            # (e.g. a laptop running the monthly export).
            self.titles = _bundled_titles(lang_id)
            if self.titles:
                self.source = 'bundled'
                click.echo(click.style(
                    'Info: resolving outline numbers from the bundled S-34 '
                    'title index (no corpus database found).', fg='blue'))

    def resolve(self, title: str) -> int:
        want = _fold(title)
        best = 0
        for num, corpus in self.titles:
            if corpus == want:
                return num
            if want and not best and (want in corpus or corpus in want):
                best = num
        return best


@click.command('midweek-program')
@click.option('--docx', 'docx_path', type=click.Path(exists=True, dir_okay=False),
              default=None,
              help="Hourglass 'Tout pwogram ansanm' .docx (auto-detected if omitted).")
@click.option('--csv-file', 'csv_filepath', type=click.Path(dir_okay=False),
              default=None, help='Output CSV path (default: auto-generated).')
def export_midweek_program(docx_path: Optional[str], csv_filepath: Optional[str]):
    """Export the midweek (LNTNF) program to the NWS import CSV."""
    docx_path = _resolve_docx(docx_path)
    meetings = _load_meetings(docx_path)

    rows = []
    for meeting in meetings:
        if meeting['date'].weekday() == 6:  # Sundays handled by public-talks
            continue
        week = _monday(meeting['date']).strftime('%Y/%m/%d')
        for part in parse_midweek(meeting):
            rows.append({
                'Date': week,
                'Person': part['person'],
                'PartType': part['part_type'],
                'Assignment': part['assignment'],
                'School': part['school'],
                'LanguageGroupID': 0,
            })

    if not rows:
        raise click.ClickException('No midweek meetings found in the document.')

    weeks = len({r['Date'] for r in rows})
    _write_csv(csv_filepath or _default_out('LNTNF_Pwogram'),
               ['Date', 'Person', 'PartType', 'Assignment', 'School',
                'LanguageGroupID'], rows,
               summary=f"{len(rows)} assignments across {weeks} week(s)")


@click.command('public-talks')
@click.option('--docx', 'docx_path', type=click.Path(exists=True, dir_okay=False),
              default=None,
              help="Hourglass 'Tout pwogram ansanm' .docx (auto-detected if omitted).")
@click.option('--csv-file', 'csv_filepath', type=click.Path(dir_okay=False),
              default=None, help='Output CSV path (default: auto-generated).')
@click.option('--s34-db', default=DEFAULT_S34_DB, show_default=True,
              help='jwlinker corpus DB for resolving outline numbers from titles.')
@click.option('--s34-language', default='51', show_default=True,
              help='MEPS language id for outline matching (51 = Haitian Creole).')
def export_public_talks(docx_path: Optional[str], csv_filepath: Optional[str],
                        s34_db: str, s34_language: str):
    """Export the weekend public-talk program to the NWS import CSV."""
    docx_path = _resolve_docx(docx_path)
    meetings = _load_meetings(docx_path)
    resolver = OutlineResolver(s34_db, s34_language)

    fieldnames = ['Date', 'Congregation', 'PublicSpeaker', 'OutlineNumber',
                  'OutlineName', 'Song', 'SpeakerConfirmed', 'Notes',
                  'LanguageGroupID', 'Chairman', 'WatchtowerReader',
                  'CustomWeekendAssignment1', 'CustomWeekendAssignment2',
                  'Hospitality']
    rows = []
    for meeting in meetings:
        if meeting['date'].weekday() != 6:
            continue
        talk = parse_weekend(meeting)
        if not talk:
            continue  # convention/assembly week — no talk to export
        number = resolver.resolve(talk['title'])
        rows.append({
            'Date': talk['date'].strftime('%Y/%m/%d'),
            'Congregation': talk['speaker_cong'],
            'PublicSpeaker': talk['speaker'],
            'OutlineNumber': number,
            'OutlineName': f"{number} - {talk['title']}" if number else talk['title'],
            'Song': '', 'SpeakerConfirmed': '', 'Notes': '',
            'LanguageGroupID': 0,
            'Chairman': talk['chairman'],
            'WatchtowerReader': talk['wt_reader'],
            'CustomWeekendAssignment1': '', 'CustomWeekendAssignment2': '',
            'Hospitality': '',
        })

    if not rows:
        raise click.ClickException('No public talks found in the document.')

    unresolved = [r for r in rows if not r['OutlineNumber']]
    if unresolved:
        click.echo(click.style(
            f"Warning: {len(unresolved)} talk title(s) not matched to an "
            f"S-34 outline number (exported with number 0):", fg='yellow'))
        for r in unresolved:
            click.echo(click.style(f"  • {r['Date']}  {r['OutlineName']}",
                                   fg='yellow'))
    _write_csv(csv_filepath or _default_out('Diskou_Piblik'), fieldnames, rows,
               summary=f"{len(rows)} talk(s)")


@click.command('organized')
@click.option('--docx', 'docx_paths', type=click.Path(exists=True, dir_okay=False),
              multiple=True,
              help="Hourglass 'Tout pwogram ansanm' .docx — repeatable; all "
                   "recent ones are auto-detected and merged if omitted.")
@click.option('--out', 'out_path', type=click.Path(dir_okay=False), default=None,
              help='Output JSON path (default: auto-generated).')
@click.option('--s34-db', default=DEFAULT_S34_DB, show_default=True,
              help='jwlinker corpus DB for resolving outline numbers from titles.')
@click.option('--s34-language', default='51', show_default=True,
              help='MEPS language id for outline matching (51 = Haitian Creole).')
@click.pass_context
def export_organized(ctx: click.Context, docx_paths,
                     out_path: Optional[str], s34_db: str, s34_language: str):
    """Export ONE unified JSON for Organized: Hourglass data + the program.

    Combines the latest Hourglass JSON export (publishers, privileges,
    reports, attendance, groups — passed through verbatim) with the meeting
    program parsed from the .docx (which the JSON does not contain) under a
    single "program" key. Organized's import_hourglass command consumes this
    file directly, so one file carries the complete congregation state.
    """
    import json as _json

    json_file_path = ctx.obj.get('json_file_path') if ctx.obj else None
    if not json_file_path:
        raise click.ClickException(
            'The unified export needs the Hourglass JSON — none was found. '
            'Pass it with the top-level --json-file option.')
    docx_paths = _resolve_docxs(docx_paths)
    resolver = OutlineResolver(s34_db, s34_language)

    with open(json_file_path, encoding='utf-8') as f:
        unified = _json.load(f)

    # Merge every document, keyed by week/date — a week present in two
    # exports keeps the version from the LATER export (docx_paths is oldest
    # first), so re-exports with corrections win over stale ones.
    weekend_by_week: dict[str, dict] = {}
    midweek_by_date: dict[str, dict] = {}
    for docx_path in docx_paths:
        meetings = split_meetings(docx_rows(docx_path))
        if not meetings:
            click.echo(click.style(
                f"Warning: no meetings found in '{docx_path}' — skipping.",
                fg="yellow"))
            continue
        for meeting in meetings:
            week_of = _monday(meeting['date']).strftime('%Y/%m/%d')
            if meeting['date'].weekday() == 6:
                talk = parse_weekend(meeting)
                if not talk:
                    continue  # convention/assembly week
                weekend_by_week[week_of] = {
                    'date': talk['date'].strftime('%Y/%m/%d'),
                    'week_of': week_of,
                    'title': talk['title'],
                    'outline_number': resolver.resolve(talk['title']),
                    'speaker': talk['speaker'],
                    'speaker_cong': talk['speaker_cong'],
                    'chairman': talk['chairman'],
                    'wt_reader': talk['wt_reader'],
                }
            else:
                parts = parse_midweek(meeting)
                if parts:
                    midweek_by_date[meeting['date'].strftime('%Y/%m/%d')] = {
                        'date': meeting['date'].strftime('%Y/%m/%d'),
                        'week_of': week_of,
                        'parts': parts,
                    }
    if not weekend_by_week and not midweek_by_date:
        raise click.ClickException(
            "No meetings found in any program document — are these the "
            "Hourglass 'all programs' exports?")
    weekend = sorted(weekend_by_week.values(), key=lambda t: t['week_of'])
    midweek = sorted(midweek_by_date.values(), key=lambda m: m['date'])

    # Surface every S-34 resolution failure loudly — an unresolved title
    # imports as a numberless talk, which every downstream surface (talk
    # prep, radar, schedules) silently skips. Fix the title at the source
    # (Hourglass) or set the talk directly in Organized.
    for t in weekend:
        if not t['outline_number']:
            click.echo(click.style(
                f"Warning: no S-34 outline number for {t['week_of']} "
                f"(speaker: {t['speaker'] or '?'}; title: "
                f"'{t['title'] or 'MISSING'}') — talk imports without a "
                f"number.", fg="yellow"))

    unified['program'] = {
        'generated_at': datetime.now().isoformat(timespec='seconds'),
        'source_docx': ', '.join(
            os.path.basename(p) for p in docx_paths),
        'weekend': weekend,
        'midweek': midweek,
    }

    if out_path is None:
        out_path = os.path.join(
            os.getcwd(), f"organized-unified_{datetime.now():%Y%m%d}.json")
    tmp = out_path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        _json.dump(unified, f, ensure_ascii=False)
    os.replace(tmp, out_path)
    click.echo(click.style(
        f"Unified JSON '{out_path}' created ({len(weekend)} weekend talk(s), "
        f"{len(midweek)} midweek meeting(s)).", fg="green"))


@click.command('all')
@click.option('--out-dir', type=click.Path(file_okay=False), default='.',
              show_default=True, help='Directory to write every artifact into.')
@click.option('--docx', 'docx_path', type=click.Path(exists=True, dir_okay=False),
              default=None,
              help="Hourglass 'Tout pwogram ansanm' .docx (auto-detected if omitted).")
@click.option('--s34-db', default=DEFAULT_S34_DB, show_default=True,
              help='jwlinker corpus DB for resolving outline numbers from titles.')
@click.option('--s34-language', default='51', show_default=True,
              help='MEPS language id for outline matching (51 = Haitian Creole).')
@click.pass_context
def export_all(ctx: click.Context, out_dir: str, docx_path: Optional[str],
               s34_db: str, s34_language: str):
    """Export everything possible in one run.

    Produces every artifact the available inputs allow — the NWS
    field-service CSV (needs the Hourglass JSON), the NWS midweek and
    public-talk program CSVs (need the docx), and the unified Organized JSON
    (needs both) — and reports what was skipped and why. `fsr doctor` shows
    the same availability without writing anything.
    """
    from fsr.reports.exports import export_csv_command

    os.makedirs(out_dir, exist_ok=True)
    stamp = f"{datetime.now():%Y%m%d}"
    have_json = bool(ctx.obj and ctx.obj.get('cong_data'))
    try:
        docx_found = _resolve_docx(docx_path)
    except click.ClickException:
        docx_found = None

    made, skipped = [], []

    def run(label, command, **kwargs):
        try:
            ctx.invoke(command, **kwargs)
            made.append(label)
        except click.ClickException as e:
            skipped.append((label, str(e.message)))

    if have_json:
        run('field-service', export_csv_command,
            csv_filepath=os.path.join(
                out_dir, f"NWScheduler_field_service_{stamp}.csv"))
    else:
        skipped.append(('field-service', 'no Hourglass JSON found'))

    if docx_found:
        run('midweek-program', export_midweek_program,
            docx_path=docx_found,
            csv_filepath=os.path.join(
                out_dir, f"NWScheduler_LNTNF_Pwogram_{stamp}.csv"))
        run('public-talks', export_public_talks,
            docx_path=docx_found,
            csv_filepath=os.path.join(
                out_dir, f"NWScheduler_Diskou_Piblik_{stamp}.csv"),
            s34_db=s34_db, s34_language=s34_language)
    else:
        skipped.append(('midweek-program', 'no program .docx found'))
        skipped.append(('public-talks', 'no program .docx found'))

    if have_json:
        # An explicit --docx pins the unified export to that one file;
        # otherwise let it auto-detect and MERGE every recent program docx
        # (Hourglass exports one month per file). A missing docx surfaces as
        # a skip via the ClickException, like the other artifacts.
        run('organized (unified JSON)', export_organized,
            docx_paths=(docx_path,) if docx_path else (),
            out_path=os.path.join(out_dir, f"organized-unified_{stamp}.json"),
            s34_db=s34_db, s34_language=s34_language)
    else:
        skipped.append(('organized (unified JSON)',
                        'needs the Hourglass JSON (and a program .docx)'))

    click.echo('')
    click.echo(click.style(
        f"Done: {len(made)} artifact(s) in {os.path.abspath(out_dir)}",
        fg='green', bold=True))
    for label, reason in skipped:
        click.echo(click.style(f"  skipped {label}: {reason}", fg='yellow'))
    if skipped:
        click.echo(click.style(
            "  ↳ run `fsr doctor` to see what is missing.", fg='yellow'))
