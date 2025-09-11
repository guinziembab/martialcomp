#!/usr/bin/env python3
"""
Remove invisible Unicode bidi control characters from .po files.
Targets: LRM, RLM, LRE, RLE, PDF, LRO, RLO, LRI, RLI, FSI, PDI.
Usage:
  python3 scripts/clean_bidi_controls.py locale/pt/LC_MESSAGES/django.po
  python3 scripts/clean_bidi_controls.py --glob "locale/*/LC_MESSAGES/*.po"
"""
import argparse
import glob as pyglob
import polib
from typing import List

BIDI_CHARS = {
    "\u200e",  # LRM
    "\u200f",  # RLM
    "\u202a",  # LRE
    "\u202b",  # RLE
    "\u202c",  # PDF
    "\u202d",  # LRO
    "\u202e",  # RLO
    "\u2066",  # LRI
    "\u2067",  # RLI
    "\u2068",  # FSI
    "\u2069",  # PDI
}

TRANSTABLE = str.maketrans({c: "" for c in BIDI_CHARS})

def strip_bidi(s: str) -> str:
    return s.translate(TRANSTABLE)

def clean_file(path: str) -> int:
    po = polib.pofile(path)
    changed = 0
    # header
    if po.metadata:
        new_meta = {k: strip_bidi(v) for k, v in po.metadata.items()}
        if new_meta != po.metadata:
            po.metadata = new_meta
            changed += 1
    for entry in po:
        orig = (entry.msgid, entry.msgstr, tuple(sorted(entry.flags)))
        entry.msgid = strip_bidi(entry.msgid)
        if entry.msgid_plural:
            entry.msgid_plural = strip_bidi(entry.msgid_plural)
        if entry.msgstr:
            entry.msgstr = strip_bidi(entry.msgstr)
        if entry.msgstr_plural:
            for k in list(entry.msgstr_plural.keys()):
                entry.msgstr_plural[k] = strip_bidi(entry.msgstr_plural[k])
        if entry.tcomment:
            entry.tcomment = strip_bidi(entry.tcomment)
        if entry.comment:
            entry.comment = strip_bidi(entry.comment)
        now = (entry.msgid, entry.msgstr, tuple(sorted(entry.flags)))
        if now != orig:
            changed += 1
    if changed:
        po.save(path)
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--glob", dest="glob")
    args = ap.parse_args()
    files: List[str] = []
    if args.glob:
        files.extend(pyglob.glob(args.glob))
    files.extend(args.files)
    files = [f for f in files if f.endswith(".po")]
    if not files:
        print("No .po files provided")
        return
    total = 0
    for f in files:
        c = clean_file(f)
        print(f"{f}: cleaned {c} entries")
        total += c
    print(f"TOTAL cleaned: {total}")

if __name__ == "__main__":
    main()
