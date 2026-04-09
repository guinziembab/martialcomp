#!/usr/bin/env python
"""
Script pour normaliser et synchroniser tous les fichiers PO.
Utilise FR comme référence absolue et s'assure que toutes les langues ont exactement les mêmes msgid.
"""

import os
import re
from collections import OrderedDict


def parse_po_file(po_file_path):
    """Parse a PO file and return header + entries."""
    with open(po_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split header and entries
    # Header is the first msgid "" block
    header_match = re.search(r'^(.*?msgid ""\nmsgstr ".*?")\n\n', content, re.DOTALL)
    if header_match:
        header = header_match.group(1)
        rest = content[header_match.end():]
    else:
        header = ""
        rest = content

    # Parse entries
    entries = OrderedDict()

    # Split by empty lines (entry separator)
    blocks = re.split(r'\n\n+', rest)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract comments
        comments = []
        lines = block.split('\n')
        non_comment_start = 0
        for i, line in enumerate(lines):
            if line.startswith('#'):
                comments.append(line)
            else:
                non_comment_start = i
                break

        # Rejoin non-comment lines
        entry_text = '\n'.join(lines[non_comment_start:])

        # Extract msgid
        msgid_match = re.search(r'msgid\s+"((?:[^"\\]|\\.)*)"\s*(?:\n"((?:[^"\\]|\\.)*)")*', entry_text)
        if not msgid_match:
            continue

        # Get full msgid (may be multiline)
        msgid = msgid_match.group(1)
        # Check for continuation
        msgid_full_match = re.search(r'msgid\s+("(?:[^"\\]|\\.)*"(?:\s*\n\s*"(?:[^"\\]|\\.)*")*)', entry_text)
        if msgid_full_match:
            msgid_raw = msgid_full_match.group(1)
            # Remove quotes and join
            parts = re.findall(r'"((?:[^"\\]|\\.)*)"', msgid_raw)
            msgid = ''.join(parts)

        if not msgid:  # Skip empty msgid (header duplicate)
            continue

        # Extract msgstr
        msgstr_match = re.search(r'msgstr\s+("(?:[^"\\]|\\.)*"(?:\s*\n\s*"(?:[^"\\]|\\.)*")*)', entry_text)
        if msgstr_match:
            msgstr_raw = msgstr_match.group(1)
            parts = re.findall(r'"((?:[^"\\]|\\.)*)"', msgstr_raw)
            msgstr = ''.join(parts)
        else:
            msgstr = ""

        entries[msgid] = {
            'msgstr': msgstr,
            'comments': '\n'.join(comments),
            'raw': block
        }

    return header, entries


def write_po_file(po_file_path, header, entries, language_name=""):
    """Write a PO file with header and entries."""
    with open(po_file_path, 'w', encoding='utf-8', newline='\n') as f:
        # Write header
        f.write(header)
        f.write('\n\n')

        # Write entries
        for msgid, data in entries.items():
            # Write comments if any
            if data.get('comments'):
                f.write(data['comments'])
                f.write('\n')

            # Escape msgid for writing
            escaped_msgid = msgid.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            escaped_msgstr = data['msgstr'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

            f.write(f'msgid "{escaped_msgid}"\n')
            f.write(f'msgstr "{escaped_msgstr}"\n')
            f.write('\n')


def sync_po_with_reference(ref_entries, target_entries):
    """Sync target entries with reference, keeping existing translations."""
    synced = OrderedDict()

    for msgid, ref_data in ref_entries.items():
        if msgid in target_entries:
            # Keep existing translation
            synced[msgid] = {
                'msgstr': target_entries[msgid]['msgstr'],
                'comments': ref_data.get('comments', '')
            }
        else:
            # Add missing entry with empty msgstr
            synced[msgid] = {
                'msgstr': '',
                'comments': ref_data.get('comments', '')
            }

    return synced


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locale_dir = os.path.join(base_dir, 'locale')

    # Load reference (French)
    fr_po_path = os.path.join(locale_dir, 'fr', 'LC_MESSAGES', 'django.po')
    print(f"Loading reference (FR): {fr_po_path}")
    fr_header, fr_entries = parse_po_file(fr_po_path)
    print(f"  Found {len(fr_entries)} entries")

    # Languages to sync
    languages = ['en', 'am', 'ar', 'de', 'es', 'hi', 'it', 'ja', 'ko', 'no', 'pt', 'ru', 'sw', 'vi', 'yo', 'zh', 'zu']

    for lang in languages:
        po_path = os.path.join(locale_dir, lang, 'LC_MESSAGES', 'django.po')
        if not os.path.exists(po_path):
            print(f"  {lang}: File not found, skipping")
            continue

        print(f"\nProcessing {lang}...")
        target_header, target_entries = parse_po_file(po_path)
        print(f"  Found {len(target_entries)} entries")

        # Sync with reference
        synced_entries = sync_po_with_reference(fr_entries, target_entries)
        print(f"  Synced to {len(synced_entries)} entries")

        # Count translations
        translated = sum(1 for e in synced_entries.values() if e['msgstr'])
        print(f"  Translations: {translated}/{len(synced_entries)} ({100*translated//len(synced_entries)}%)")

        # Write back
        write_po_file(po_path, target_header, synced_entries, lang)
        print(f"  Written to {po_path}")

    print(f"\n=== DONE ===")
    print("All PO files synchronized with FR reference")
    print("Run 'python manage.py compilemessages' to compile the .mo files")


if __name__ == '__main__':
    main()
