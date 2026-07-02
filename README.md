# fsr — Congregation Data Toolkit

**fsr** turns the two artifacts Hourglass can export — the JSON data export and
the *Tout pwogram ansanm* program document — into every file your downstream
tools need: import-ready CSVs for **New World Scheduler** and a single unified
JSON for **Organized**'s full server-side import.

```
                         ┌──────────────────────────────────────────────┐
  hourglass-export.json ─┤  fsr export all                              │─ NWScheduler_field_service.csv
                         │                                              │─ NWScheduler_LNTNF_Pwogram.csv
  Tout pwogram *.docx ───┤  (or any individual export below)            │─ NWScheduler_Diskou_Piblik.csv
                         └──────────────────────────────────────────────┘─ organized-unified.json
```

## Quick start

```bash
pip install .                 # or: pip install -e '.[dev]' for development

fsr doctor                    # what can fsr see, and which exports are possible?
fsr export all                # produce everything the available inputs allow
```

`fsr export all` (alias: `fsr x a`) is the whole monthly run: drop the latest
Hourglass exports where fsr can find them, run it, done. Anything that cannot
be produced is skipped with the reason printed.

## Inputs & discovery

fsr auto-detects its inputs — newest match wins — in the **current directory**,
your **Downloads** folder, and **`/library/hourglass`**:

| Input | Expected name | Carries |
|---|---|---|
| Hourglass JSON export | `hourglass-export*.json` | publishers, privileges, service reports, attendance, groups |
| Hourglass program document | `Tout pwogram*.docx` | the meeting program (midweek & weekend) — **not present in the JSON** |

Explicit paths always win: `--json-file` (top level) and `--docx` (per command).
Run `fsr doctor` at any time to see exactly what would be used, how fresh it
is, and what that makes possible.

## Exports

### `fsr export all [--out-dir DIR]`

Everything below, in one run, into one directory. Skips (and says why) any
artifact whose input is missing.

### `fsr export field-service` — NWS field service CSV

`Date,FirstName,LastName,SharedInMinistry,BibleStudies,AP,Hours,Credit,Remarks`
— one row per publisher per reported month, ready for New World Scheduler's
field-service import. Requires the JSON. (See
[Activity determination](#activity-determination) for how `SharedInMinistry`
is derived.)

### `fsr export midweek-program` — NWS midweek (LNTNF) CSV

`Date,Person,PartType,Assignment,School,LanguageGroupID` — the full midweek
program: chairman, auxiliary-classroom counselor, prayers, Treasures talk,
Spiritual Gems, Bible reading per hall, Apply-yourself parts with students
*and* assistants (`Patnè:`) per hall, Living-as-Christians parts, CBS
conductor + reader. Dated by the week's Monday; persons as
`Firstname Lastname`; schools `1` (main hall) / `2` (auxiliary class).
Requires the docx.

### `fsr export public-talks` — NWS weekend program CSV

The full 14-column NWS weekend format (`Date,Congregation,PublicSpeaker,
OutlineNumber,OutlineName,…,Chairman,WatchtowerReader,…`), dated by the Sunday
itself. The document prints only talk **titles**; fsr resolves the S-34
outline **number** against a jwlinker corpus database (`--s34-db`, default
`/library/jwlinker/jw_library.db`; `--s34-language`, default `51` = Haitian
Creole). Unresolvable titles export with number `0` and a per-title warning —
the same convention NWS itself uses. Requires the docx.

### `fsr export organized` — unified JSON for Organized

One file carrying the **complete congregation state**: the Hourglass JSON
passed through verbatim, plus a `program` key with the weekend talks (resolved
outline numbers, speaker + congregation, chairman, Watchtower reader) and the
full midweek part list parsed from the docx. Organized's `import_hourglass`
command consumes it directly — persons, reports, attendance, groups and both
meeting programs from a single import. Requires both inputs.

**Format conventions (all CSVs):** UTF-8 with BOM, atomic writes
(temp-file + rename), byte-format compatible with New World Scheduler's own
exports. Convention/assembly weeks are skipped automatically.

## Command reference

```
fsr [--json-file FILE] [--json-type TYPE] COMMAND
```

| Command | Aliases | Purpose |
|---|---|---|
| `export all` | `x a` | every possible artifact, one run |
| `export field-service` | `x fs` | NWS field-service CSV |
| `export midweek-program` | `x mw`, `x lntnf` | NWS midweek program CSV |
| `export public-talks` | `x pt`, `x talks`, `x diskou` | NWS weekend program CSV |
| `export organized` | `x org`, `x unified` | unified JSON for Organized |
| `doctor` | `dr`, `check` | show detected inputs & possible exports |
| `summary monthly-activity` | `sum …` | terminal activity report (see below) |

Any **unambiguous prefix** also works (`fsr x pub`); ambiguous prefixes fail
with the candidate list. `fsr --version` prints the version.

### Shell completion

```bash
# bash (~/.bashrc)
eval "$(_FSR_COMPLETE=bash_source fsr)"
# zsh: _FSR_COMPLETE=zsh_source   fish: _FSR_COMPLETE=fish_source fsr | source
```

## Terminal reports

`fsr summary monthly-activity --month YYYY-MM` prints a per-category activity
summary (publishers, auxiliary/regular/special pioneers: report counts, hours,
Bible studies) to the terminal. It shares the
[activity-determination rules](#activity-determination) with the
field-service export.

## Data reference

<details>
<summary><strong>Hourglass JSON structure</strong></summary>

fsr expects these top-level keys:

* `congregation` — general congregation info (loaded, not currently consumed).
* `publishers` — list of `{id, firstname, lastname, …}`.
* `reports` — list of monthly service reports:
  `{user: {id}, year, month, pioneer, studies, minutes, credithours, remarks,
  has_reported_field_service}`.

Additional keys (`privileges`, `attendance`, `fsGroups`, `monthlyTotals`,
`notPublishers`, `addresses`) pass through untouched into the unified
Organized JSON, which imports them fully.

</details>

<details>
<summary id="activity-determination"><strong>Activity determination</strong></summary>

Whether a report counts as shared ministry (`SharedInMinistry` in the CSV,
inclusion in summary totals) follows one rule set:

1. `has_reported_field_service: false` — definitive **no**: hours/studies/
   credit export empty, `AP` is `False`, aggregations exclude the report;
   remarks are preserved.
2. `has_reported_field_service: true` — definitive **yes**: fields populate
   from their values.
3. Flag `null`/absent — **inferred**: shared if the report has positive
   `minutes` or positive `studies`.

</details>

## Development

```bash
pip install -e '.[dev]'
pytest tests/
```

Requires Python ≥ 3.10. Packaging is `pyproject.toml`-only (PEP 621).

## License

[GPL-3.0-or-later](LICENSE)
