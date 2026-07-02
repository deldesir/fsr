# fsr — Congregation Data Toolkit

**fsr** is a command-line toolkit for congregation data managed in
[Hourglass](https://hourglass-app.com). It reads the two artifacts Hourglass
exports — the JSON data export and the *Tout pwogram ansanm* program
document — and produces import-ready files for **New World Scheduler** and
**Organized**, as well as on-screen activity reports.

```
                         ┌──────────────────────────────────┐
  hourglass-export.json ─┤                                  ├─ NWScheduler_field_service.csv
                         │            fsr export            ├─ NWScheduler_LNTNF_Pwogram.csv
  Tout pwogram *.docx ───┤                                  ├─ NWScheduler_Diskou_Piblik.csv
                         └──────────────────────────────────┘─ organized-unified.json
```

## Installation

```bash
pip install .                # regular use
pip install -e '.[dev]'      # development (editable, with test dependencies)
```

Requires Python ≥ 3.10.

## Quick start

```bash
fsr doctor        # show which input files fsr detects and which exports are possible
fsr export all    # produce every artifact the available inputs allow
```

Artifacts that cannot be produced are skipped, with the reason printed.

## Inputs and discovery

fsr auto-detects its input files — newest match wins — in the current
directory, the user's Downloads folder, and `/library/hourglass`:

| Input | Expected name | Contents |
|---|---|---|
| Hourglass JSON export | `hourglass-export*.json` | publishers, privileges, service reports, attendance, groups |
| Hourglass program document | `Tout pwogram*.docx` | the meeting program (midweek and weekend), which is not part of the JSON export |

Explicit paths take precedence: `--json-file` (top level) and `--docx`
(per command). `fsr doctor` reports what would be used and how recent it is.

## Commands

### Exports

| Command | Requires | Output |
|---|---|---|
| `fsr export all [--out-dir DIR]` | any | every artifact below, in one run |
| `fsr export field-service` | JSON | New World Scheduler field-service CSV |
| `fsr export midweek-program` | docx | New World Scheduler midweek (LNTNF) program CSV |
| `fsr export public-talks` | docx | New World Scheduler weekend program CSV |
| `fsr export organized` | both | unified JSON for Organized's full import |

**`field-service`** — `Date,FirstName,LastName,SharedInMinistry,BibleStudies,
AP,Hours,Credit,Remarks`; one row per publisher per reported month. See
[Activity determination](#data-reference) for how `SharedInMinistry` is
derived.

**`midweek-program`** — `Date,Person,PartType,Assignment,School,
LanguageGroupID`; the complete midweek program: chairman,
auxiliary-classroom counselor, prayers, Treasures talk, Spiritual Gems, Bible
reading per hall, Apply-yourself parts with students and assistants
(`Patnè:`) per hall, Living-as-Christians parts, and CBS conductor + reader.
Dated by the week's Monday; persons as `Firstname Lastname`; school `1` is
the main hall, `2` the auxiliary class.

**`public-talks`** — the 14-column New World Scheduler weekend format
(`Date,Congregation,PublicSpeaker,OutlineNumber,OutlineName,…,Chairman,
WatchtowerReader,…`), dated by the Sunday. The document prints only talk
titles; the S-34 outline number is resolved against a jwlinker corpus
database when one is available (`--s34-db`, default
`/library/jwlinker/jw_library.db`; `--s34-language`, default `51` = Haitian
Creole). Titles that cannot be resolved export with number `0` and a
per-title warning.

**`organized`** — a single JSON carrying the complete congregation state: the
Hourglass export passed through verbatim, plus a `program` key with the
weekend talks (resolved outline numbers, speaker and congregation, chairman,
Watchtower reader) and the full midweek part list. Organized's
`import_hourglass` command consumes this file directly.

All CSVs are written UTF-8 with BOM and atomically (temporary file + rename),
matching New World Scheduler's own export conventions. Convention and
assembly weeks carry no program and are skipped.

### Reports

**`fsr summary monthly-activity --month YYYY-MM`** — a per-category activity
summary for one month, printed to the terminal: report counts, hours, and
Bible studies for publishers and for auxiliary, regular, and special
pioneers, plus congregation Bible-study totals. Uses the same
activity-determination rules as the field-service export.

### Diagnostics

**`fsr doctor`** — shows the detected JSON and docx (with age), whether the
S-34 corpus database is available for outline resolution, whether the working
directory is writable, and which exports are consequently possible. Each gap
comes with a suggested fix.

### Aliases and prefixes

Every command accepts explicit aliases and any unambiguous prefix; ambiguous
prefixes fail with the list of candidates. Canonical names are always shown
in help and usage output.

| Canonical | Aliases |
|---|---|
| `export` | `x`, `exp` |
| `export field-service` | `fs` |
| `export midweek-program` | `mw`, `lntnf` |
| `export public-talks` | `pt`, `talks`, `diskou` |
| `export organized` | `org`, `unified` |
| `export all` | `a` |
| `summary` | `sum` |
| `doctor` | `dr`, `check` |

`fsr --version` prints the installed version.

### Shell completion

```bash
# bash (~/.bashrc)
eval "$(_FSR_COMPLETE=bash_source fsr)"
# zsh: _FSR_COMPLETE=zsh_source   fish: _FSR_COMPLETE=fish_source fsr | source
```

## Data reference

<details>
<summary><strong>Hourglass JSON structure</strong></summary>

fsr expects these top-level keys:

* `congregation` — general congregation information (loaded, not currently
  consumed by any command).
* `publishers` — list of `{id, firstname, lastname, …}`.
* `reports` — list of monthly service reports:
  `{user: {id}, year, month, pioneer, studies, minutes, credithours, remarks,
  has_reported_field_service}`.

Additional keys (`privileges`, `attendance`, `fsGroups`, `monthlyTotals`,
`notPublishers`, `addresses`) pass through untouched into the unified
Organized JSON, which imports them fully.

</details>

<details>
<summary><strong>Activity determination</strong></summary>

Whether a report counts as shared ministry (`SharedInMinistry` in the
field-service CSV, inclusion in summary totals) follows one rule set:

1. `has_reported_field_service: false` — definitive **no**: hours, studies,
   and credit export empty, `AP` is `False`, and aggregations exclude the
   report; remarks are preserved.
2. `has_reported_field_service: true` — definitive **yes**: fields populate
   from their values.
3. Flag `null` or absent — **inferred**: shared if the report has positive
   `minutes` or positive `studies`.

</details>

## Development

```bash
pip install -e '.[dev]'
pytest tests/
```

Packaging is defined solely in `pyproject.toml` (PEP 621).

## License

[GPL-3.0-or-later](LICENSE)
