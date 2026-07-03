#!/usr/bin/env python3
"""Regenerate fsr's bundled S-34 title index from a jwlinker corpus.

The bundled index (fsr/data/s34_titles.json) is what resolves docx talk
titles to outline numbers on machines WITHOUT the corpus database (e.g.
the operator's laptop). It must be regenerated whenever the corpus gains
a new S-34 revision, then committed so `git pull && pip install .`
carries it everywhere fsr runs.

Usage:
    python tools/gen_s34_index.py [--db /library/jwlinker/jw_library.db]
"""

import argparse
import json
import re
import sqlite3
from pathlib import Path

LANGS = ("0", "3", "51")  # English, French, Haitian Creole
NAME_RE = re.compile(r"(?:No\s+)?(\d+)[.\s]\s*(.*)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="/library/jwlinker/jw_library.db")
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    titles: dict[str, dict[str, str]] = {}
    for lang in LANGS:
        rows = conn.execute(
            """SELECT t.name FROM Topics t
               JOIN Categories c ON t.category_id = c.id
               JOIN Publications p ON c.publication_id = p.id
               WHERE p.code = 's34' AND p.language = ?""",
            (lang,),
        ).fetchall()
        per_lang: dict[str, str] = {}
        for (name,) in rows:
            m = NAME_RE.match(name or "")
            if m and m.group(2).strip():
                per_lang.setdefault(m.group(1), m.group(2).strip())
        if not per_lang:
            raise SystemExit(f"no s34 titles for language {lang} in {args.db}")
        titles[lang] = dict(sorted(per_lang.items(), key=lambda kv: int(kv[0])))

    out = Path(__file__).resolve().parent.parent / "fsr" / "data" / "s34_titles.json"
    payload = {
        "note": (
            "S-34 outline titles per MEPS language id; generated from a "
            "jwlinker corpus. Used as fallback when no --s34-db is available."
        ),
        "publication": "s34",
        "titles": titles,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    counts = {k: len(v) for k, v in titles.items()}
    print(f"wrote {out} — {counts}")


if __name__ == "__main__":
    main()
