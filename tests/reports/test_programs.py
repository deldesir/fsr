"""Tests for the docx-driven meeting-program exports."""

import csv
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from click.testing import CliRunner

from fsr.cli import cli as fsr_cli
from fsr.core.docx_parser import (
    docx_rows, first_last, parse_meeting_date, parse_midweek, parse_weekend,
    split_meetings,
)

_DOC_TMPL = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:tbl>{rows}</w:tbl></w:body></w:document>"""


def _tr(*cells):
    tcs = []
    for cell in cells:
        # '\n' inside a cell becomes a soft line break, as Hourglass writes.
        runs = '<w:r><w:br/><w:t xml:space="preserve">'.join(
            c for c in cell.split('\n'))
        tcs.append(
            f'<w:tc><w:p><w:r><w:t xml:space="preserve">{runs}</w:t></w:r>'
            f'</w:p></w:tc>')
    return f"<w:tr>{''.join(tcs)}</w:tr>"


def _write_docx(path, rows_xml):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('word/document.xml', _DOC_TMPL.format(rows=rows_xml))


def _sample_rows():
    return ''.join([
        # ── Midweek (Friday) ─────────────────────────────────────────
        _tr('Vandredi, 10 Jiyè 2026', 'Reyinyon Lasemèn'),
        _tr('', 'Sal segondè', 'Sal prensipal'),
        _tr('5:00 PM', 'Kantik 123 — Chante', 'Doe, Jane (Priyè)'),
        _tr('5:05 PM', 'Pawòl entwodiksyon',
            'Smith, Al\nKonseye (1ye klas la)', 'Jones, Bob\nPrezidan'),
        _tr('Trezò espirityèl nan pawòl Bondye a (JEREMI 13-15)'),
        _tr('5:06 PM', '1. Premye pati (10 min.)', 'One, Speaker'),
        _tr('5:16 PM', '2. Trezò espirityèl (10 min.)', 'Two, Gems'),
        _tr('5:26 PM', '3. Lekti Labib (4 min.)', 'Aux, Reader', 'Main, Reader'),
        _tr('Byen prepare w pou travay predikasyon an'),
        _tr('5:31 PM', '4. Konvèsasyon (3 min.)',
            'AuxStudent, Ann\nAuxAssist, Amy', 'MainStudent, May\nMainAssist, Mia'),
        _tr('Lavi kretyen'),
        _tr('5:46 PM', 'Kantik 49 — Lòt chante'),
        _tr('5:52 PM', '5. Bezwen lokal (15 min.)', 'Local, Larry'),
        _tr('6:17 PM', '6. Etid biblik kongregasyon an (30 min.)',
            'Conduct, Carl · Read, Rita'),
        _tr('6:47 PM', 'Pawòl pou fini (3 min.)', 'Jones, Bob'),
        _tr('6:50 PM', 'Kantik 61 — Dènye chante', 'Close, Cal (Priyè)'),
        # ── Weekend (Sunday) ─────────────────────────────────────────
        _tr('Dimanch, 12 Jiyè 2026', 'Reyinyon nan wikenn'),
        _tr('10:15 AM', 'Kantik', 'Chair, Chuck (Prezidan)'),
        _tr('Diskou piblik'),
        _tr('10:20 AM', 'Tit diskou a (30 min.)', 'Speaker, Sam (ELSEWHERE)'),
        _tr('Kondiktè Toudegad'),
        _tr('10:55 AM', 'Etid Toudegad (60 min.)', 'Wt, Cond · Wt, Reader'),
        # ── Convention week: no Diskou piblik section ────────────────
        _tr('Dimanch, 2 Out 2026', 'Reyinyon nan wikenn'),
        _tr('Asanble rejyonal'),
    ])


class TestDocxParser(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.docx = Path(self.tmp.name) / 'Tout pwogram test.docx'
        _write_docx(self.docx, _sample_rows())

    def tearDown(self):
        self.tmp.cleanup()

    def test_helpers(self):
        self.assertEqual(first_last('Mondésir, Blondel'), 'Blondel Mondésir')
        self.assertEqual(str(parse_meeting_date('Dimanch, 12 Jiyè 2026')),
                         '2026-07-12')

    def test_meetings_split(self):
        meetings = split_meetings(docx_rows(self.docx))
        self.assertEqual([str(m['date']) for m in meetings],
                         ['2026-07-10', '2026-07-12', '2026-08-02'])

    def test_midweek_parts(self):
        meetings = split_meetings(docx_rows(self.docx))
        rows = parse_midweek(meetings[0])
        by_type = {r['part_type']: r for r in rows}

        self.assertEqual(by_type['Chairman']['person'], 'Bob Jones')
        self.assertEqual(by_type['AuxiliaryClassroomCounselor']['school'], 2)
        self.assertEqual(by_type['OpeningPrayer']['person'], 'Jane Doe')
        self.assertEqual(by_type['ClosingPrayer']['person'], 'Cal Close')
        self.assertEqual(by_type['TreasuresTalk']['person'], 'Speaker One')
        self.assertEqual(by_type['SpiritualGems']['assignment'],
                         '2. Trezò espirityèl')
        readings = [r for r in rows if r['part_type'] == 'BibleReading']
        self.assertEqual({(r['person'], r['school']) for r in readings},
                         {('Reader Main', 1), ('Reader Aux', 2)})
        applies = [r for r in rows if r['part_type'].startswith('Apply1')]
        self.assertEqual(len(applies), 4)  # student+assistant per hall
        assistants = [r for r in applies if 'Assistant' in r['part_type']]
        self.assertTrue(all(r['assignment'].startswith('Patnè: ')
                            for r in assistants))
        self.assertEqual(by_type['Living1']['person'], 'Larry Local')
        self.assertEqual(by_type['CBS']['person'], 'Carl Conduct')
        self.assertEqual(by_type['CBSReader']['person'], 'Rita Read')
        # Concluding words are the chairman's, not a scheduled part.
        self.assertNotIn('ConcludingComments', by_type)

    def test_weekend_talk(self):
        meetings = split_meetings(docx_rows(self.docx))
        talk = parse_weekend(meetings[1])
        self.assertEqual(talk['title'], 'Tit diskou a')
        self.assertEqual(talk['speaker'], 'Sam Speaker')
        self.assertEqual(talk['speaker_cong'], 'ELSEWHERE')
        self.assertEqual(talk['chairman'], 'Chuck Chair')
        self.assertEqual(talk['wt_reader'], 'Reader Wt')

    def test_convention_week_skipped(self):
        meetings = split_meetings(docx_rows(self.docx))
        self.assertIsNone(parse_weekend(meetings[2]))


class TestProgramExportCommands(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()

    def _invoke(self, tmpdir, command, out_name):
        docx = Path(tmpdir) / 'Tout pwogram test.docx'
        _write_docx(docx, _sample_rows())
        out = Path(tmpdir) / out_name
        result = self.runner.invoke(fsr_cli, [
            'export', command, '--docx', str(docx), '--csv-file', str(out)])
        self.assertEqual(result.exit_code, 0, result.output)
        with open(out, encoding='utf-8-sig') as f:
            return list(csv.DictReader(f))

    def test_midweek_program_csv(self):
        with TemporaryDirectory() as tmpdir:
            rows = self._invoke(tmpdir, 'midweek-program', 'mw.csv')
        # Dated by the week's Monday.
        self.assertTrue(all(r['Date'] == '2026/07/06' for r in rows))
        self.assertTrue(all(r['LanguageGroupID'] == '0' for r in rows))
        chairman = next(r for r in rows if r['PartType'] == 'Chairman')
        self.assertEqual(chairman['Person'], 'Bob Jones')

    def test_public_talks_csv(self):
        with TemporaryDirectory() as tmpdir:
            rows = self._invoke(tmpdir, 'public-talks', 'pt.csv')
        # Only the real Sunday; the convention week produces no row.
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['Date'], '2026/07/12')  # the Sunday itself
        self.assertEqual(row['PublicSpeaker'], 'Sam Speaker')
        self.assertEqual(row['Congregation'], 'ELSEWHERE')
        self.assertEqual(row['Chairman'], 'Chuck Chair')
        self.assertEqual(row['WatchtowerReader'], 'Reader Wt')
        # No corpus DB in tests: number 0, bare title.
        self.assertEqual(row['OutlineNumber'], '0')
        self.assertEqual(row['OutlineName'], 'Tit diskou a')


if __name__ == '__main__':
    unittest.main()
