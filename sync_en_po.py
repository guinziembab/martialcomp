#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Synchronise le fichier PO anglais avec le fichier PO francais.
- Ajoute les chaines manquantes
- Conserve les traductions existantes
- Genere un rapport des chaines non traduites
"""

import re
from collections import OrderedDict
from datetime import datetime
import shutil


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


def get_po_header(filepath):
    """Extrait l'en-tete du fichier PO."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Trouver la fin de l'en-tete (premiere entree msgid non vide)
    lines = content.split('\n')
    header_end = 0

    for i, line in enumerate(lines):
        if line.startswith('msgid "') and i > 0:
            match = re.match(r'msgid "(.*)"', line)
            if match and match.group(1):
                header_end = i
                break

    return '\n'.join(lines[:header_end])


def sync_po_files():
    """Synchronise le PO anglais avec le PO francais."""

    print("=" * 70)
    print("SYNCHRONISATION DU FICHIER PO ANGLAIS")
    print("=" * 70)

    # Backup
    backup_name = f'locale/en/LC_MESSAGES/django.po.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy('locale/en/LC_MESSAGES/django.po', backup_name)
    print(f"\nBackup cree: {backup_name}")

    # Charger les fichiers
    print("\nChargement des fichiers...")
    fr_entries = extract_po_entries('locale/fr/LC_MESSAGES/django.po')
    en_entries = extract_po_entries('locale/en/LC_MESSAGES/django.po')

    print(f"  - PO francais: {len(fr_entries)} entrees")
    print(f"  - PO anglais: {len(en_entries)} entrees")

    # Construire le nouveau fichier PO anglais
    new_entries = OrderedDict()
    added_count = 0
    kept_count = 0
    untranslated = []

    for msgid in fr_entries:
        if msgid in en_entries:
            # Conserver la traduction existante
            msgstr = en_entries[msgid]
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
    header = '''#
msgid ""
msgstr ""
"Project-Id-Version: martialcomp\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-12-11 10:00+0100\\n"
"PO-Revision-Date: 2025-12-11 10:00+0100\\n"
"Last-Translator: System\\n"
"Language-Team: English\\n"
"Language: en\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

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
    with open('locale/en/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

    print(f"\nFichier sauvegarde: locale/en/LC_MESSAGES/django.po")

    # Generer le rapport des chaines non traduites
    print("\n" + "=" * 70)
    print(f"CHAINES NON TRADUITES ({len(untranslated)})")
    print("=" * 70)

    with open('en_untranslated_report.txt', 'w', encoding='utf-8') as f:
        f.write("# RAPPORT DES CHAINES NON TRADUITES - PO ANGLAIS\n")
        f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"# Total: {len(untranslated)} chaines\n")
        f.write("=" * 70 + "\n\n")

        for i, (msgid, msgstr) in enumerate(untranslated, 1):
            status = "VIDE" if not msgstr else "NON TRADUIT"
            f.write(f"# {i}. [{status}]\n")
            f.write(f'msgid "{msgid}"\n')
            f.write(f'msgstr "{msgstr}"\n\n')

            if i <= 50:
                truncated = msgid[:60] + "..." if len(msgid) > 60 else msgid
                print(f"  {i}. [{status}] {truncated}")

        if len(untranslated) > 50:
            print(f"  ... et {len(untranslated) - 50} autres")

    print(f"\nRapport sauvegarde: en_untranslated_report.txt")

    return {
        'total': len(new_entries),
        'added': added_count,
        'kept': kept_count,
        'untranslated': len(untranslated)
    }


if __name__ == '__main__':
    results = sync_po_files()
    print("\n" + "=" * 70)
    print("SYNCHRONISATION TERMINEE")
    print("=" * 70)
    print(f"Total entrees: {results['total']}")
    print(f"Nouvelles: {results['added']}")
    print(f"Conservees: {results['kept']}")
    print(f"A traduire: {results['untranslated']}")
