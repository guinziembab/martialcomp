#!/usr/bin/env python
"""
Script pour aligner tous les fichiers PO avec le fichier de référence FR.
Crée des backups avant modification.
"""
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# Liste des langues à traiter (exclure les dossiers de backup)
LANGUAGES = ['am', 'ar', 'de', 'en', 'es', 'fr', 'hi', 'it', 'ja', 'ko', 'no', 'pt', 'ru', 'sw', 'vi', 'yo', 'zh', 'zu']

TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')


def parse_po_file(filepath):
    """Parse un fichier PO et retourne un dictionnaire msgid -> msgstr."""
    entries = {}
    current_msgid = None
    current_msgstr = None
    current_comments = []
    in_msgid = False
    in_msgstr = False

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"  ERROR reading {filepath}: {e}")
        return entries

    for line in lines:
        line = line.rstrip('\n\r')

        # Comments
        if line.startswith('#'):
            if current_msgid is None:
                current_comments.append(line)
            continue

        # Empty line - save current entry
        if not line.strip():
            if current_msgid is not None and current_msgstr is not None:
                entries[current_msgid] = {
                    'msgstr': current_msgstr,
                    'comments': current_comments
                }
            current_msgid = None
            current_msgstr = None
            current_comments = []
            in_msgid = False
            in_msgstr = False
            continue

        # msgid
        if line.startswith('msgid '):
            in_msgid = True
            in_msgstr = False
            match = re.match(r'msgid\s+"(.*)"', line)
            if match:
                current_msgid = match.group(1)
            else:
                current_msgid = ""
            continue

        # msgstr
        if line.startswith('msgstr '):
            in_msgid = False
            in_msgstr = True
            match = re.match(r'msgstr\s+"(.*)"', line)
            if match:
                current_msgstr = match.group(1)
            else:
                current_msgstr = ""
            continue

        # Continuation line
        if line.startswith('"') and line.endswith('"'):
            content = line[1:-1]
            if in_msgid and current_msgid is not None:
                current_msgid += content
            elif in_msgstr and current_msgstr is not None:
                current_msgstr += content

    # Save last entry
    if current_msgid is not None and current_msgstr is not None:
        entries[current_msgid] = {
            'msgstr': current_msgstr,
            'comments': current_comments
        }

    return entries


def get_po_header(filepath):
    """Extract PO file header."""
    header_lines = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            in_header = True
            for line in f:
                if in_header:
                    if line.startswith('msgid ""') or line.startswith('#'):
                        header_lines.append(line.rstrip())
                    elif line.startswith('msgstr ""'):
                        header_lines.append(line.rstrip())
                    elif line.startswith('"') and 'msgid' not in ''.join(header_lines[-5:]):
                        header_lines.append(line.rstrip())
                    elif line.strip() == '':
                        header_lines.append('')
                        # Check if we're past the header
                        if len(header_lines) > 10:
                            break
                    else:
                        break
    except:
        pass
    return header_lines


def escape_po_string(s):
    """Escape special characters for PO file."""
    if s is None:
        return ""
    s = s.replace('\\', '\\\\')
    s = s.replace('"', '\\"')
    return s


def write_aligned_po(filepath, reference_entries, target_entries, lang):
    """Write aligned PO file with all entries from reference."""
    # Get header from target or create minimal one
    header = get_po_header(filepath) if os.path.exists(filepath) else []

    if not header:
        header = [
            '# Translation file for MartialComp',
            f'# Language: {lang}',
            '#',
            'msgid ""',
            'msgstr ""',
            '"Content-Type: text/plain; charset=UTF-8\\n"',
            '"Content-Transfer-Encoding: 8bit\\n"',
            ''
        ]

    with open(filepath, 'w', encoding='utf-8') as f:
        # Write header
        for line in header:
            f.write(line + '\n')
        f.write('\n')

        # Write all entries from reference
        for msgid, ref_data in reference_entries.items():
            if not msgid:  # Skip empty msgid (header)
                continue

            # Get translation from target if exists
            if msgid in target_entries and target_entries[msgid]['msgstr']:
                msgstr = target_entries[msgid]['msgstr']
            else:
                # Use empty string for missing translations
                msgstr = ""

            # Write entry
            f.write(f'msgid "{escape_po_string(msgid)}"\n')
            f.write(f'msgstr "{escape_po_string(msgstr)}"\n')
            f.write('\n')


def main():
    base_dir = Path('.')
    locale_dir = base_dir / 'locale'

    print("=" * 80)
    print("ALIGNEMENT DES FICHIERS PO")
    print(f"Timestamp: {TIMESTAMP}")
    print("=" * 80)

    # Load reference (FR)
    fr_po = locale_dir / 'fr' / 'LC_MESSAGES' / 'django.po'
    if not fr_po.exists():
        print(f"ERROR: Reference file not found: {fr_po}")
        return

    print(f"\n1. Chargement de la référence FR: {fr_po}")
    fr_entries = parse_po_file(fr_po)
    print(f"   Entrées FR: {len(fr_entries)}")

    # Backup all PO files
    print(f"\n2. Création des backups...")
    for lang in LANGUAGES:
        po_file = locale_dir / lang / 'LC_MESSAGES' / 'django.po'
        if po_file.exists():
            backup_file = po_file.parent / f'django.po.backup_align_{TIMESTAMP}'
            try:
                shutil.copy2(po_file, backup_file)
                print(f"   Backup: {lang} -> {backup_file.name}")
            except Exception as e:
                print(f"   ERROR backup {lang}: {e}")

    # Align all PO files
    print(f"\n3. Alignement des fichiers PO...")
    stats = {}

    for lang in LANGUAGES:
        if lang == 'fr':
            continue  # Skip reference

        po_file = locale_dir / lang / 'LC_MESSAGES' / 'django.po'

        if not po_file.exists():
            print(f"   {lang}: SKIP (file not found)")
            continue

        # Parse target
        target_entries = parse_po_file(po_file)

        # Count translations
        translated = sum(1 for k, v in target_entries.items() if v['msgstr'] and k)
        missing = len(fr_entries) - translated

        # Write aligned file
        write_aligned_po(po_file, fr_entries, target_entries, lang)

        stats[lang] = {
            'total': len(fr_entries),
            'translated': translated,
            'missing': missing
        }
        print(f"   {lang}: {translated}/{len(fr_entries)} traduits ({missing} manquants)")

    # Summary
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    print(f"\nRéférence (FR): {len(fr_entries)} entrées")
    print("\nStatut par langue:")
    for lang, s in sorted(stats.items()):
        pct = (s['translated'] / s['total'] * 100) if s['total'] > 0 else 0
        print(f"  {lang}: {s['translated']}/{s['total']} ({pct:.1f}%) - {s['missing']} manquants")

    print("\n" + "=" * 80)
    print("TERMINÉ!")
    print("=" * 80)
    print("\nPour compiler les fichiers, exécutez:")
    print("  python manage.py compilemessages")


if __name__ == '__main__':
    main()
