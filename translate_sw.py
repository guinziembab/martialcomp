#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translate all untranslated French entries in Swahili PO file.
Loads translations from sw_translations.json and applies them.
"""
import polib
import json
import os
import sys

def main():
    po_path = os.path.join(os.path.dirname(__file__), 'locale', 'sw', 'LC_MESSAGES', 'django.po')
    translations_path = os.path.join(os.path.dirname(__file__), 'sw_translations.json')

    # Load translations dictionary
    print(f"Loading translations from {translations_path}...")
    with open(translations_path, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    print(f"Loaded {len(translations)} translations.")

    # Open PO file
    print(f"Opening PO file: {po_path}")
    po = polib.pofile(po_path)

    total = len(po)
    untranslated_before = len(po.untranslated_entries())
    print(f"Total entries: {total}")
    print(f"Untranslated before: {untranslated_before}")

    # Build a mojibake-to-clean mapping for fuzzy matching
    # Some msgid values in the PO file have mojibake (double-encoded UTF-8)
    # e.g., "Ã©" instead of "é". Try to decode them and match with clean keys.
    def try_fix_mojibake(text):
        """Try to decode mojibake (double-encoded UTF-8) text."""
        try:
            return text.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            return None

    # Apply translations
    applied = 0
    missing = 0
    missing_list = []
    for entry in po.untranslated_entries():
        if entry.msgid in translations:
            entry.msgstr = translations[entry.msgid]
            applied += 1
        else:
            # Try mojibake fix: decode the garbled msgid and look up the clean version
            cleaned = try_fix_mojibake(entry.msgid)
            if cleaned and cleaned in translations:
                entry.msgstr = translations[cleaned]
                applied += 1
            else:
                missing += 1
                if len(missing_list) < 20:
                    missing_list.append(entry.msgid[:80])

    # Save
    print(f"\nApplied {applied} translations.")
    print(f"Missing translations: {missing}")
    if missing_list:
        print("First missing entries:")
        for m in missing_list:
            print(f"  - {m}")

    po.save(po_path)
    print(f"\nSaved to {po_path}")

    # Verify
    po2 = polib.pofile(po_path)
    untranslated_after = len(po2.untranslated_entries())
    translated_after = len(po2.translated_entries())
    print(f"\nAfter translation:")
    print(f"  Translated: {translated_after}")
    print(f"  Untranslated: {untranslated_after}")
    print(f"  Reduction: {untranslated_before - untranslated_after} entries translated")

if __name__ == '__main__':
    main()
