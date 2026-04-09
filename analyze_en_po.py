#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analyse du fichier PO anglais par rapport au fichier PO français.
- Compare les msgid des deux fichiers
- Identifie les chaînes manquantes dans le PO anglais
- Identifie les chaînes non traduites (msgstr vide ou identique au msgid)
"""

import re
from collections import OrderedDict

def extract_po_entries(filepath):
    """Extrait toutes les entrées msgid/msgstr d'un fichier PO."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = OrderedDict()

    # Pattern pour extraire les entrées
    # Gère les msgstr sur plusieurs lignes
    pattern = r'msgid\s+"((?:[^"\\]|\\.)*)"\s*(?:"((?:[^"\\]|\\.)*)"\s*)*msgstr\s+"((?:[^"\\]|\\.)*)"\s*(?:"((?:[^"\\]|\\.)*)"\s*)*'

    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Chercher msgid
        if line.startswith('msgid "'):
            msgid = ""
            # Extraire le msgid (peut être sur plusieurs lignes)
            match = re.match(r'msgid "(.*)"', line)
            if match:
                msgid = match.group(1)

            # Vérifier les lignes de continuation
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"') and not lines[j].strip().startswith('msgstr'):
                cont_match = re.match(r'\s*"(.*)"', lines[j])
                if cont_match:
                    msgid += cont_match.group(1)
                j += 1

            # Chercher msgstr
            if j < len(lines) and lines[j].strip().startswith('msgstr "'):
                msgstr = ""
                msgstr_match = re.match(r'msgstr "(.*)"', lines[j].strip())
                if msgstr_match:
                    msgstr = msgstr_match.group(1)

                # Vérifier les lignes de continuation du msgstr
                k = j + 1
                while k < len(lines) and lines[k].strip().startswith('"'):
                    cont_match = re.match(r'\s*"(.*)"', lines[k])
                    if cont_match:
                        msgstr += cont_match.group(1)
                    k += 1

                if msgid:  # Ignorer l'entrée vide d'en-tête
                    entries[msgid] = msgstr

                i = k
                continue

        i += 1

    return entries

def analyze_po_files():
    """Analyse et compare les fichiers PO français et anglais."""

    print("Chargement des fichiers PO...")

    # Charger les deux fichiers
    fr_entries = extract_po_entries('locale/fr/LC_MESSAGES/django.po')
    en_entries = extract_po_entries('locale/en/LC_MESSAGES/django.po')

    print(f"\nFichier PO français: {len(fr_entries)} entrées")
    print(f"Fichier PO anglais: {len(en_entries)} entrées")

    # Trouver les chaînes manquantes dans le PO anglais
    missing_in_en = []
    for msgid in fr_entries:
        if msgid not in en_entries:
            missing_in_en.append(msgid)

    # Trouver les chaînes non traduites dans le PO anglais
    # (msgstr vide ou identique au msgid français)
    untranslated = []
    for msgid, msgstr in en_entries.items():
        if not msgstr or msgstr == msgid:
            untranslated.append((msgid, msgstr))

    # Trouver les chaînes en anglais qui ne sont pas dans le français
    extra_in_en = []
    for msgid in en_entries:
        if msgid not in fr_entries:
            extra_in_en.append(msgid)

    # Rapport
    print("\n" + "=" * 80)
    print("RAPPORT D'ANALYSE - PO ANGLAIS vs PO FRANÇAIS")
    print("=" * 80)

    print(f"\nSTATISTIQUES:")
    print(f"   - Entrees dans le PO francais: {len(fr_entries)}")
    print(f"   - Entrees dans le PO anglais: {len(en_entries)}")
    print(f"   - Chaines manquantes dans le PO anglais: {len(missing_in_en)}")
    print(f"   - Chaines non traduites dans le PO anglais: {len(untranslated)}")
    print(f"   - Chaines supplementaires dans le PO anglais: {len(extra_in_en)}")

    # Écrire les chaînes manquantes dans un fichier
    if missing_in_en:
        print(f"\n[X] CHAINES MANQUANTES DANS LE PO ANGLAIS ({len(missing_in_en)}):")
        print("-" * 60)

        with open('missing_en_translations.txt', 'w', encoding='utf-8') as f:
            f.write("# Chaînes manquantes dans le PO anglais\n")
            f.write(f"# Total: {len(missing_in_en)} chaînes\n\n")

            for i, msgid in enumerate(missing_in_en[:50], 1):
                print(f"   {i}. {msgid[:70]}{'...' if len(msgid) > 70 else ''}")
                f.write(f'msgid "{msgid}"\n')
                f.write(f'msgstr ""\n\n')

            if len(missing_in_en) > 50:
                print(f"   ... et {len(missing_in_en) - 50} autres")
                for msgid in missing_in_en[50:]:
                    f.write(f'msgid "{msgid}"\n')
                    f.write(f'msgstr ""\n\n')

        print("\n   -> Liste complete sauvegardee: missing_en_translations.txt")

    # Écrire les chaînes non traduites
    if untranslated:
        print(f"\n[!] CHAINES NON TRADUITES ({len(untranslated)}):")
        print("-" * 60)

        with open('untranslated_en_strings.txt', 'w', encoding='utf-8') as f:
            f.write("# Chaînes non traduites dans le PO anglais\n")
            f.write(f"# Total: {len(untranslated)} chaînes\n\n")

            for i, (msgid, msgstr) in enumerate(untranslated[:30], 1):
                status = "VIDE" if not msgstr else "NON TRADUIT"
                print(f"   {i}. [{status}] {msgid[:60]}{'...' if len(msgid) > 60 else ''}")
                f.write(f'# {status}\n')
                f.write(f'msgid "{msgid}"\n')
                f.write(f'msgstr "{msgstr}"\n\n')

            if len(untranslated) > 30:
                print(f"   ... et {len(untranslated) - 30} autres")
                for msgid, msgstr in untranslated[30:]:
                    status = "VIDE" if not msgstr else "NON TRADUIT"
                    f.write(f'# {status}\n')
                    f.write(f'msgid "{msgid}"\n')
                    f.write(f'msgstr "{msgstr}"\n\n')

        print("\n   -> Liste complete sauvegardee: untranslated_en_strings.txt")

    print("\n" + "=" * 80)

    return {
        'fr_count': len(fr_entries),
        'en_count': len(en_entries),
        'missing': missing_in_en,
        'untranslated': untranslated,
        'extra': extra_in_en
    }

if __name__ == '__main__':
    results = analyze_po_files()
