#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fusion des fichiers PO allemand DEV et PRODUCTION.
Conserve toutes les traductions existantes.
"""

import re
from collections import OrderedDict


def extract_entries(filepath):
    """Extrait les entrees msgid/msgstr d'un fichier PO."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = OrderedDict()
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('msgid "') and line != 'msgid ""':
            msgid = ''
            match = re.match(r'msgid "(.*)"', line)
            if match:
                msgid = match.group(1)

            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"'):
                if lines[j].strip().startswith('msgstr'):
                    break
                cont = re.match(r'\s*"(.*)"', lines[j])
                if cont:
                    msgid += cont.group(1)
                j += 1

            if j < len(lines) and lines[j].strip().startswith('msgstr "'):
                msgstr = ''
                match = re.match(r'msgstr "(.*)"', lines[j].strip())
                if match:
                    msgstr = match.group(1)

                k = j + 1
                while k < len(lines) and lines[k].strip().startswith('"'):
                    cont = re.match(r'\s*"(.*)"', lines[k])
                    if cont:
                        msgstr += cont.group(1)
                    k += 1

                if msgid:
                    entries[msgid] = msgstr

                i = k
                continue
        i += 1

    return entries


def main():
    print("=" * 70)
    print("FUSION DES PO ALLEMAND (DEV + PRODUCTION)")
    print("=" * 70)

    print("\n1. Extraction des entrees...")
    dev_entries = extract_entries('locale/de/LC_MESSAGES/django.po')
    prod_entries = extract_entries('locale/de/LC_MESSAGES/django_production.po')

    print(f"   DEV: {len(dev_entries)} entrees")
    print(f"   PROD: {len(prod_entries)} entrees")

    # Fusionner: prendre DEV comme base, enrichir avec PROD
    print("\n2. Fusion des traductions...")
    merged = OrderedDict()
    prod_used = 0
    dev_kept = 0
    no_translation = 0

    for msgid, msgstr in dev_entries.items():
        # Priorite 1: Production a une traduction valide
        if msgid in prod_entries and prod_entries[msgid] and prod_entries[msgid] != msgid:
            merged[msgid] = prod_entries[msgid]
            prod_used += 1
        # Priorite 2: DEV a une traduction valide
        elif msgstr and msgstr != msgid:
            merged[msgid] = msgstr
            dev_kept += 1
        # Pas de traduction
        else:
            merged[msgid] = msgstr if msgstr else ""
            no_translation += 1

    # Ajouter les entrees de PROD qui ne sont pas dans DEV
    added_from_prod = 0
    for msgid, msgstr in prod_entries.items():
        if msgid not in merged:
            merged[msgid] = msgstr
            added_from_prod += 1

    print(f"   Traductions de PROD utilisees: {prod_used}")
    print(f"   Traductions de DEV conservees: {dev_kept}")
    print(f"   Sans traduction: {no_translation}")
    print(f"   Entrees ajoutees de PROD: {added_from_prod}")
    print(f"   Total fusionne: {len(merged)}")

    # Stats finales
    translated = sum(1 for m, t in merged.items() if t and t != m)
    empty = sum(1 for m, t in merged.items() if not t)
    untranslated = len(merged) - translated - empty

    print(f"\n3. Statistiques finales:")
    print(f"   Traduites: {translated} ({translated/len(merged)*100:.1f}%)")
    print(f"   Non traduites (msgstr=msgid): {untranslated}")
    print(f"   Vides: {empty}")

    # Ecrire le fichier fusionne
    print("\n4. Ecriture du fichier fusionne...")

    header = '''#
msgid ""
msgstr ""
"Project-Id-Version: martialcomp\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-12-11 23:00+0100\\n"
"PO-Revision-Date: 2025-12-11 23:00+0100\\n"
"Last-Translator: System\\n"
"Language-Team: German\\n"
"Language: de\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

'''

    output = [header]
    for msgid, msgstr in merged.items():
        # Echapper les caracteres speciaux
        esc_id = msgid.replace('\\', '\\\\').replace('"', '\\"')
        esc_str = msgstr.replace('\\', '\\\\').replace('"', '\\"') if msgstr else ''
        output.append(f'msgid "{esc_id}"')
        output.append(f'msgstr "{esc_str}"')
        output.append('')

    # Sauvegarder le fichier fusionne
    with open('locale/de/LC_MESSAGES/django_merged.po', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))

    print(f"   Sauvegarde: locale/de/LC_MESSAGES/django_merged.po")

    # Remplacer le fichier DEV par le fichier fusionne
    print("\n5. Remplacement du fichier DEV...")
    import shutil
    shutil.copy('locale/de/LC_MESSAGES/django.po', 'locale/de/LC_MESSAGES/django.po.backup_before_merge')
    shutil.copy('locale/de/LC_MESSAGES/django_merged.po', 'locale/de/LC_MESSAGES/django.po')
    print("   Backup: locale/de/LC_MESSAGES/django.po.backup_before_merge")
    print("   Nouveau: locale/de/LC_MESSAGES/django.po")

    print("\n" + "=" * 70)
    print(f"FUSION TERMINEE - {translated} traductions conservees")
    print("=" * 70)


if __name__ == '__main__':
    main()
