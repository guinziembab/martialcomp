#!/usr/bin/env python
"""
Script pour synchroniser tous les fichiers PO avec le fichier de référence français.
Ajoute les msgid manquants aux fichiers PO incomplets.
"""

import os
import re

def extract_msgids_from_po(po_file_path):
    """Extract all msgid entries from a PO file."""
    msgids = {}

    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern to match msgid/msgstr pairs (including multiline)
    pattern = r'((?:#[^\n]*\n)*)(msgid\s+"([^"]*(?:"[\n\r]+\s*"[^"]*)*)"\s*\nmsgstr\s+"([^"]*(?:"[\n\r]+\s*"[^"]*)*)")'

    # Simpler approach - line by line
    lines = content.split('\n')
    current_msgid = None
    current_msgstr = None
    current_comments = []
    in_msgid = False
    in_msgstr = False

    for i, line in enumerate(lines):
        # Skip header
        if i < 20 and 'Project-Id-Version' in line:
            continue

        if line.startswith('#'):
            if current_msgid is None:
                current_comments.append(line)
            continue

        if line.startswith('msgid "'):
            in_msgid = True
            in_msgstr = False
            current_msgid = line[7:-1]  # Remove 'msgid "' and trailing '"'
        elif line.startswith('msgstr "'):
            in_msgid = False
            in_msgstr = True
            current_msgstr = line[8:-1]  # Remove 'msgstr "' and trailing '"'
        elif line.startswith('"') and in_msgid:
            current_msgid += line[1:-1]
        elif line.startswith('"') and in_msgstr:
            current_msgstr += line[1:-1]
        elif line.strip() == '' and current_msgid is not None:
            if current_msgid:  # Skip empty msgid (header)
                msgids[current_msgid] = {
                    'msgstr': current_msgstr or '',
                    'comments': '\n'.join(current_comments)
                }
            current_msgid = None
            current_msgstr = None
            current_comments = []
            in_msgid = False
            in_msgstr = False

    # Don't forget the last entry
    if current_msgid:
        msgids[current_msgid] = {
            'msgstr': current_msgstr or '',
            'comments': '\n'.join(current_comments)
        }

    return msgids


def add_missing_msgids_to_po(po_file_path, reference_msgids, target_msgids):
    """Add missing msgid entries to a PO file."""
    missing = set(reference_msgids.keys()) - set(target_msgids.keys())

    if not missing:
        return 0

    # Read existing content
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Build new entries
    new_entries = []
    for msgid in sorted(missing):
        # Escape quotes in msgid
        escaped_msgid = msgid.replace('\\', '\\\\').replace('"', '\\"')
        entry = f'\nmsgid "{escaped_msgid}"\nmsgstr ""\n'
        new_entries.append(entry)

    # Append to file
    with open(po_file_path, 'a', encoding='utf-8') as f:
        f.write('\n# Missing translations added from reference (FR)\n')
        for entry in new_entries:
            f.write(entry)

    return len(new_entries)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, 'locale')

    # Reference file (French)
    fr_po_path = os.path.join(locale_dir, 'fr', 'LC_MESSAGES', 'django.po')
    print(f"Loading reference file (FR): {fr_po_path}")
    fr_msgids = extract_msgids_from_po(fr_po_path)
    print(f"  Found {len(fr_msgids)} msgid entries in FR")

    # Languages to sync
    languages = ['am', 'ar', 'de', 'en', 'es', 'hi', 'it', 'ja', 'ko', 'no', 'pt', 'ru', 'sw', 'vi', 'yo', 'zh', 'zu']

    total_added = 0
    for lang in languages:
        po_path = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
        if not os.path.exists(po_path):
            print(f"  {lang}: File not found, skipping")
            continue

        print(f"\nProcessing {lang}...")
        target_msgids = extract_msgids_from_po(po_path)
        print(f"  Found {len(target_msgids)} msgid entries")

        missing_count = len(set(fr_msgids.keys()) - set(target_msgids.keys()))
        if missing_count > 0:
            print(f"  Missing {missing_count} entries from reference")
            added = add_missing_msgids_to_po(po_path, fr_msgids, target_msgids)
            print(f"  Added {added} new entries")
            total_added += added
        else:
            print(f"  All entries present")

    print(f"\n=== DONE ===")
    print(f"Total entries added across all languages: {total_added}")
    print("Run 'python manage.py compilemessages' to compile the .mo files")


if __name__ == '__main__':
    main()
