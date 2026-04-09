#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour aligner les fichiers PO (italien, allemand) avec le fichier PO francais.
- Ajoute les chaines manquantes
- Conserve les traductions existantes
- Genere un rapport des chaines non traduites
"""

import re
import sys
from collections import OrderedDict
from datetime import datetime
import shutil
import os


def extract_po_entries(filepath):
    """Extrait toutes les entrees msgid/msgstr d'un fichier PO."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = OrderedDict()
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith('msgid "'):
            msgid = ""
            match = re.match(r'msgid "(.*)"', line)
            if match:
                msgid = match.group(1)

            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"'):
                if lines[j].strip().startswith('msgstr'):
                    break
                cont_match = re.match(r'\s*"(.*)"', lines[j])
                if cont_match:
                    msgid += cont_match.group(1)
                j += 1

            if j < len(lines) and lines[j].strip().startswith('msgstr "'):
                msgstr = ""
                msgstr_match = re.match(r'msgstr "(.*)"', lines[j].strip())
                if msgstr_match:
                    msgstr = msgstr_match.group(1)

                k = j + 1
                while k < len(lines) and lines[k].strip().startswith('"'):
                    cont_match = re.match(r'\s*"(.*)"', lines[k])
                    if cont_match:
                        msgstr += cont_match.group(1)
                    k += 1

                if msgid:
                    entries[msgid] = msgstr

                i = k
                continue

        i += 1

    return entries


def get_language_info(lang_code):
    """Retourne les informations de langue."""
    info = {
        'it': {'name': 'Italian', 'team': 'Italian', 'plural': 'nplurals=2; plural=(n != 1);'},
        'de': {'name': 'German', 'team': 'German', 'plural': 'nplurals=2; plural=(n != 1);'},
        'es': {'name': 'Spanish', 'team': 'Spanish', 'plural': 'nplurals=2; plural=(n != 1);'},
        'pt': {'name': 'Portuguese', 'team': 'Portuguese', 'plural': 'nplurals=2; plural=(n != 1);'},
        'ja': {'name': 'Japanese', 'team': 'Japanese', 'plural': 'nplurals=1; plural=0;'},
        'ko': {'name': 'Korean', 'team': 'Korean', 'plural': 'nplurals=1; plural=0;'},
        'zh': {'name': 'Chinese', 'team': 'Chinese', 'plural': 'nplurals=1; plural=0;'},
        'ar': {'name': 'Arabic', 'team': 'Arabic', 'plural': 'nplurals=6; plural=(n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5);'},
        'ru': {'name': 'Russian', 'team': 'Russian', 'plural': 'nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);'},
    }
    return info.get(lang_code, {'name': lang_code.upper(), 'team': lang_code.upper(), 'plural': 'nplurals=2; plural=(n != 1);'})


def align_po_file(lang_code, fr_entries):
    """Aligne un fichier PO avec le fichier PO francais."""

    po_path = f'locale/{lang_code}/LC_MESSAGES/django.po'

    if not os.path.exists(po_path):
        print(f"  [!] Fichier non trouve: {po_path}")
        return None

    lang_info = get_language_info(lang_code)

    print(f"\n{'='*60}")
    print(f"ALIGNEMENT DU FICHIER PO {lang_info['name'].upper()}")
    print(f"{'='*60}")

    # Backup
    backup_name = f'locale/{lang_code}/LC_MESSAGES/django.po.backup_align_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy(po_path, backup_name)
    print(f"Backup cree: {backup_name}")

    # Charger le fichier cible
    print(f"Chargement de {po_path}...")
    target_entries = extract_po_entries(po_path)

    print(f"  - PO francais: {len(fr_entries)} entrees")
    print(f"  - PO {lang_info['name']}: {len(target_entries)} entrees")

    # Construire le nouveau fichier PO
    new_entries = OrderedDict()
    added_count = 0
    kept_count = 0
    untranslated = []

    for msgid in fr_entries:
        if msgid in target_entries:
            # Conserver la traduction existante
            msgstr = target_entries[msgid]
            new_entries[msgid] = msgstr
            kept_count += 1

            # Verifier si traduit
            if not msgstr or msgstr == msgid:
                untranslated.append((msgid, msgstr))
        else:
            # Nouvelle entree - msgstr vide
            new_entries[msgid] = ""
            added_count += 1
            untranslated.append((msgid, ""))

    print(f"\nResultats:")
    print(f"  - Traductions conservees: {kept_count}")
    print(f"  - Nouvelles entrees ajoutees: {added_count}")
    print(f"  - Chaines non traduites: {len(untranslated)}")

    # Generer le nouveau fichier PO
    header = f'''#
msgid ""
msgstr ""
"Project-Id-Version: martialcomp\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-12-11 10:00+0100\\n"
"PO-Revision-Date: 2025-12-11 10:00+0100\\n"
"Last-Translator: System\\n"
"Language-Team: {lang_info['team']}\\n"
"Language: {lang_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: {lang_info['plural']}\\n"

'''

    output_lines = [header]

    for msgid, msgstr in new_entries.items():
        # Echapper les guillemets et backslashes
        escaped_msgid = msgid.replace('\\', '\\\\').replace('"', '\\"')
        escaped_msgstr = msgstr.replace('\\', '\\\\').replace('"', '\\"')

        output_lines.append(f'msgid "{escaped_msgid}"')
        output_lines.append(f'msgstr "{escaped_msgstr}"')
        output_lines.append('')

    # Ecrire le fichier
    with open(po_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"Fichier sauvegarde: {po_path}")

    # Generer le rapport des chaines non traduites
    report_path = f'{lang_code}_untranslated_report.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# RAPPORT DES CHAINES NON TRADUITES - PO {lang_info['name'].upper()}\n")
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# Total: {len(untranslated)} chaines\n")
        f.write("=" * 70 + "\n\n")

        for i, (msgid, msgstr) in enumerate(untranslated, 1):
            status = "VIDE" if not msgstr else "NON TRADUIT"
            f.write(f"# {i}. [{status}]\n")
            f.write(f'msgid "{msgid}"\n')
            f.write(f'msgstr "{msgstr}"\n\n')

    print(f"Rapport sauvegarde: {report_path}")

    return {
        'lang': lang_code,
        'name': lang_info['name'],
        'total': len(new_entries),
        'added': added_count,
        'kept': kept_count,
        'untranslated': len(untranslated)
    }


def main():
    """Fonction principale."""

    print("="*60)
    print("ALIGNEMENT DES FICHIERS PO AVEC LE FRANCAIS")
    print("="*60)

    # Charger le fichier francais de reference
    print("\nChargement du fichier PO francais de reference...")
    fr_entries = extract_po_entries('locale/fr/LC_MESSAGES/django.po')
    print(f"  - {len(fr_entries)} entrees chargees")

    # Langues a aligner
    languages = ['it', 'de']

    if len(sys.argv) > 1:
        languages = sys.argv[1:]

    results = []

    for lang in languages:
        result = align_po_file(lang, fr_entries)
        if result:
            results.append(result)

    # Resume final
    print("\n" + "="*60)
    print("RESUME FINAL")
    print("="*60)

    for r in results:
        translated_pct = ((r['total'] - r['untranslated']) / r['total'] * 100) if r['total'] > 0 else 0
        print(f"\n{r['name']}:")
        print(f"  - Total entrees: {r['total']}")
        print(f"  - Nouvelles ajoutees: {r['added']}")
        print(f"  - Conservees: {r['kept']}")
        print(f"  - A traduire: {r['untranslated']}")
        print(f"  - Pourcentage traduit: {translated_pct:.1f}%")

    print("\n" + "="*60)
    print("Pour compiler les traductions:")
    for lang in languages:
        print(f"  python manage.py compilemessages -l {lang}")
    print("="*60)


if __name__ == '__main__':
    main()
