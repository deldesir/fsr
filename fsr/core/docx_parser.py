"""Parser for the Hourglass "Tout pwogram ansanm" (all programs) .docx export.

Hourglass's JSON export carries publishers and reports but NOT the meeting
program — the program only leaves Hourglass as a Word document of structured
tables, one per meeting. This module parses that document with the standard
library only (a .docx is a zip of XML): table rows become cell lists, with
<w:br/> and paragraph boundaries preserved as newlines inside cells (Hourglass
separates a person's name from their role, and a student from their assistant,
with soft line breaks).

Layout facts this parser relies on (stable across Hourglass versions):
  - A meeting starts with a date header row: "Vandredi, 10 Jiyè 2026" (Creole
    weekday + day + month + year), second cell "Reyinyon Lasemèn" (midweek) or
    "Reyinyon nan wikenn" (weekend).
  - Midweek two-hall rows carry a header "Sal segondè | Sal prensipal"; in
    part rows the auxiliary-class cell comes FIRST, main hall second.
  - Numbered parts: 1 = Treasures talk, 2 = Spiritual Gems, "Lekti Labib" =
    Bible reading; parts in the "Byen prepare w..." section = Apply yourself
    (student on the first line of a cell, assistant on the second); parts in
    "Lavi kretyen" = Living as Christians; "Etid biblik" = CBS, with the
    conductor and reader separated by ' · '.
  - "(Priyè)" marks prayers (first = opening, last = closing); "Prezidan"
    marks the chairman; "Konseye" the auxiliary-classroom counselor.
  - Convention/assembly weeks have no "Diskou piblik" section and naturally
    produce no program rows.
"""

import html
import re
import zipfile
from datetime import date
from typing import List, Optional

# Haitian Creole month names as Hourglass prints them.
CREOLE_MONTHS = {
    'janvye': 1, 'fevriye': 2, 'mas': 3, 'avril': 4, 'me': 5, 'jen': 6,
    'jiyè': 7, 'jiye': 7, 'out': 8, 'septanm': 9, 'oktòb': 10, 'oktob': 10,
    'novanm': 11, 'desanm': 12,
}

_TIME_RE = re.compile(r'^\d{1,2}:\d{2}\s*(AM|PM)?$', re.I)
_DURATION_RE = re.compile(r'\s*\((\d+)\s*(?:min\.?|mn)\)\s*$')
_NUMBERED_RE = re.compile(r'^(\d+)\.\s*')


def _fold(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize('NFKD', s or '')
    return ''.join(c for c in s if not unicodedata.combining(c)).casefold().strip()


def docx_rows(path) -> List[List[str]]:
    """Table rows as cell-text lists; soft breaks kept as newlines in cells."""
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    rows = []
    for tr in re.findall(r'<w:tr[ >].*?</w:tr>', xml, re.S):
        cells = []
        for tc in re.findall(r'<w:tc[ >].*?</w:tc>', tr, re.S):
            text = re.sub(r'<w:br/>', '\n', tc)
            text = re.sub(r'</w:p>', '\n', text)
            text = html.unescape(re.sub(r'<[^>]+>', '', text))
            cells.append(text.strip())
        if any(cells):
            rows.append(cells)
    return rows


def parse_meeting_date(line: str) -> Optional[date]:
    """'Dimanch, 12 Jiyè 2026' -> date(2026, 7, 12), else None."""
    m = re.search(r',\s*(\d{1,2})\s+(\S+)\s+(\d{4})', line or '')
    if not m:
        return None
    month = CREOLE_MONTHS.get(_fold(m.group(2)))
    if not month:
        return None
    return date(int(m.group(3)), month, int(m.group(1)))


def first_last(name: str) -> str:
    """'Mondésir, Blondel' -> 'Blondel Mondésir' (NWS person format)."""
    name = (name or '').strip()
    if ',' in name:
        last, first = name.split(',', 1)
        return f"{first.strip()} {last.strip()}"
    return name


def strip_duration(title: str) -> str:
    return _DURATION_RE.sub('', title or '').strip()


def split_meetings(rows):
    """Group rows into [{'date': date, 'rows': [...]}] on date-header rows."""
    meetings = []
    for cells in rows:
        d = parse_meeting_date(cells[0]) if cells else None
        if d:
            meetings.append({'date': d, 'rows': []})
        elif meetings:
            meetings[-1]['rows'].append(cells)
    return meetings


def _person_lines(cell: str) -> List[str]:
    return [line.strip() for line in (cell or '').split('\n') if line.strip()]


def parse_midweek(meeting) -> List[dict]:
    """One midweek meeting -> NWS rows: {person, part_type, assignment, school}.

    Order and constant strings mirror what New World Scheduler itself exports.
    """
    out = []
    section = None
    apply_idx = living_idx = 0
    prayers = []  # (name) in document order; first=opening, last=closing

    def add(person, part_type, assignment, school=1):
        if person:
            out.append({'person': first_last(person), 'part_type': part_type,
                        'assignment': assignment, 'school': school})

    for cells in meeting['rows']:
        first = cells[0] if cells else ''

        if not _TIME_RE.match(first):
            joined = ' '.join(cells)
            f = _fold(joined)
            if f.startswith(_fold('Trezò espirityèl')):
                section = 'tgw'
            elif f.startswith(_fold('Byen prepare')):
                section = 'apply'
            elif f.startswith(_fold('Lavi kretyen')):
                section = 'living'
            # anything else (support lists, hall header) is not a part row
            continue

        body = [c for c in cells[1:]]
        if not body:
            continue
        title = body[0]
        name_cells = [c for c in body[1:] if c.strip()]

        # Songs carry the prayers.
        if _fold(title).startswith(_fold('Kantik')):
            for cell in name_cells:
                for line in _person_lines(cell):
                    if '(Priyè)' in line or '(priyè)' in _fold(line):
                        prayers.append(re.sub(r'\s*\(.*?\)\s*$', '', line))
            continue

        # Chairman / auxiliary counselor row.
        if _fold(title).startswith(_fold('Pawòl entwodiksyon')):
            for cell in name_cells:
                lines = _person_lines(cell)
                if len(lines) >= 2:
                    name, role = lines[0], _fold(lines[1])
                    if 'prezidan' in role:
                        add(name, 'Chairman', 'Prezidan', 1)
                    elif 'konseye' in role:
                        add(name, 'AuxiliaryClassroomCounselor',
                            'Konseye Sal Segondè', 2)
            continue

        if _fold(title).startswith(_fold('Pawòl pou fini')):
            continue  # chairman's concluding words — not a scheduled NWS part

        clean = strip_duration(title)
        num_match = _NUMBERED_RE.match(clean)
        num = int(num_match.group(1)) if num_match else None

        # Congregation Bible Study (conductor · reader).
        if 'etid biblik' in _fold(clean):
            names = _person_lines(name_cells[0])[0] if name_cells else ''
            parts = [n.strip() for n in names.split('·')]
            add(parts[0] if parts else '', 'CBS', clean, 1)
            if len(parts) > 1:
                reader_label = f"{num}. EBK Lektè" if num else 'EBK Lektè'
                add(parts[1], 'CBSReader', reader_label, 1)
            continue

        # Two-hall rows: auxiliary cell first, main hall second.
        halls = []  # (school, cell)
        if len(name_cells) >= 2:
            halls = [(1, name_cells[-1]), (2, name_cells[0])]
        elif name_cells:
            halls = [(1, name_cells[0])]

        if section == 'tgw' or (section is None and num):
            part_type = {1: 'TreasuresTalk', 2: 'SpiritualGems'}.get(num)
            if 'lekti labib' in _fold(clean):
                part_type = 'BibleReading'
            if not part_type:
                continue
            for school, cell in halls:
                lines = _person_lines(cell)
                if lines:
                    add(lines[0], part_type, clean, school)

        elif section == 'apply':
            apply_idx += 1
            for school, cell in halls:
                lines = _person_lines(cell)
                if lines:
                    add(lines[0], f'Apply{apply_idx}', clean, school)
                if len(lines) > 1:
                    add(lines[1], f'Apply{apply_idx}Assistant',
                        f"Patnè: {clean}", school)

        elif section == 'living':
            living_idx += 1
            for school, cell in halls:
                lines = _person_lines(cell)
                if lines:
                    add(lines[0], f'Living{living_idx}', clean, school)

    result = []
    if prayers:
        result.append({'person': first_last(prayers[0]),
                       'part_type': 'OpeningPrayer',
                       'assignment': 'Priyè kòmansman', 'school': 1})
    if len(prayers) > 1:
        result.append({'person': first_last(prayers[-1]),
                       'part_type': 'ClosingPrayer',
                       'assignment': 'Priyè Final', 'school': 1})
    # Chairman/counselor first, like NWS's own export ordering.
    chair = [r for r in out if r['part_type'] in
             ('Chairman', 'AuxiliaryClassroomCounselor')]
    rest = [r for r in out if r not in chair]
    return chair + result + rest


def parse_weekend(meeting) -> Optional[dict]:
    """One weekend meeting -> public-talk info, or None (convention weeks)."""
    info = {'date': meeting['date'], 'title': '', 'speaker': '',
            'speaker_cong': '', 'chairman': '', 'wt_reader': ''}
    in_talk = False
    found = False

    for cells in meeting['rows']:
        first = cells[0] if cells else ''
        if not _TIME_RE.match(first):
            if 'diskou piblik' in _fold(' '.join(cells)):
                in_talk = True
            continue

        body = [c for c in cells[1:] if c.strip()]
        if not body:
            continue
        title = body[0]

        if _fold(title).startswith(_fold('Kantik')):
            for cell in body[1:]:
                for line in _person_lines(cell):
                    if 'prezidan' in _fold(line):
                        info['chairman'] = first_last(
                            re.sub(r'\s*\(.*?\)\s*$', '', line))
            continue

        if in_talk:
            info['title'] = strip_duration(title)
            if len(body) > 1:
                m = re.match(r'(.+?)\s*\(([^)]*)\)\s*$', body[1].strip())
                info['speaker'] = first_last(
                    (m.group(1) if m else body[1]).strip())
                info['speaker_cong'] = (m.group(2) if m else '').strip()
            in_talk = False
            found = True
            continue

        # Watchtower study row: 'conductor · reader'.
        if _DURATION_RE.search(title) and len(body) > 1 and '·' in body[1]:
            parts = [n.strip() for n in body[1].split('·')]
            if len(parts) > 1:
                info['wt_reader'] = first_last(parts[1])

    return info if found else None
