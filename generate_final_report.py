#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genere un rapport final sur l'etat des traductions.
"""

import os
import re
from collections import OrderedDict
from datetime import datetime


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


def get_language_name(lang_code):
    """Retourne le nom de la langue."""
    names = {
        'fr': 'Francais',
        'en': 'Anglais',
        'de': 'Allemand',
        'es': 'Espagnol',
        'it': 'Italien',
        'pt': 'Portugais',
        'ja': 'Japonais',
        'zh': 'Chinois',
        'ko': 'Coreen',
        'ar': 'Arabe',
        'ru': 'Russe',
        'vi': 'Vietnamien',
        'hi': 'Hindi',
        'sw': 'Swahili',
        'no': 'Norvegien',
        'am': 'Amharique',
        'yo': 'Yoruba',
        'zu': 'Zulu',
    }
    return names.get(lang_code, lang_code.upper())


def main():
    """Fonction principale."""

    languages = ['fr', 'en', 'de', 'es', 'it', 'pt', 'ja', 'zh', 'ko', 'ar', 'ru', 'vi', 'hi', 'sw', 'no', 'am', 'yo', 'zu']

    results = []

    for lang in languages:
        po_path = f'locale/{lang}/LC_MESSAGES/django.po'
        mo_path = f'locale/{lang}/LC_MESSAGES/django.mo'

        if not os.path.exists(po_path):
            continue

        entries = extract_po_entries(po_path)

        total = len(entries)
        translated = 0
        untranslated = 0
        empty = 0

        for msgid, msgstr in entries.items():
            # Pour le francais, msgstr = msgid est normal (langue source)
            if lang == 'fr':
                if msgstr:
                    translated += 1
                else:
                    empty += 1
            else:
                if msgstr and msgstr != msgid:
                    translated += 1
                elif not msgstr:
                    empty += 1
                else:
                    untranslated += 1

        mo_exists = os.path.exists(mo_path)
        percentage = (translated / total * 100) if total > 0 else 0

        results.append({
            'lang': lang,
            'name': get_language_name(lang),
            'total': total,
            'translated': translated,
            'untranslated': untranslated,
            'empty': empty,
            'percentage': percentage,
            'compiled': mo_exists
        })

    # Affichage du rapport
    print("=" * 80)
    print("RAPPORT FINAL DES TRADUCTIONS - MARTIALCOMP")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    print("\n{:<12} {:<15} {:>8} {:>10} {:>10} {:>10} {:>10}".format(
        "CODE", "LANGUE", "TOTAL", "TRADUIT", "NON TRAD", "VIDE", "%"
    ))
    print("-" * 80)

    for r in results:
        status = "[OK]" if r['compiled'] else "[X]"
        bar = "#" * int(r['percentage'] / 5) + "." * (20 - int(r['percentage'] / 5))
        print("{:<12} {:<15} {:>8} {:>10} {:>10} {:>10} {:>8.1f}% {}".format(
            r['lang'],
            r['name'],
            r['total'],
            r['translated'],
            r['untranslated'],
            r['empty'],
            r['percentage'],
            status
        ))

    print("-" * 80)

    # Stats globales
    total_entries = sum(r['total'] for r in results)
    total_translated = sum(r['translated'] for r in results)
    avg_percentage = sum(r['percentage'] for r in results) / len(results) if results else 0
    all_compiled = all(r['compiled'] for r in results)

    print(f"\nSTATISTIQUES GLOBALES:")
    print(f"  - Nombre de langues: {len(results)}")
    print(f"  - Total entrees (toutes langues): {total_entries}")
    print(f"  - Total traduit (toutes langues): {total_translated}")
    print(f"  - Pourcentage moyen: {avg_percentage:.1f}%")
    print(f"  - Tous compiles: {'OUI' if all_compiled else 'NON'}")

    # Categories
    print("\nCATEGORIES:")
    excellent = [r for r in results if r['percentage'] >= 90]
    good = [r for r in results if 50 <= r['percentage'] < 90]
    needs_work = [r for r in results if r['percentage'] < 50]

    print(f"  - Excellent (>90%): {len(excellent)} langues")
    for r in excellent:
        print(f"      {r['name']}: {r['percentage']:.1f}%")

    print(f"  - Bon (50-90%): {len(good)} langues")
    for r in good:
        print(f"      {r['name']}: {r['percentage']:.1f}%")

    print(f"  - A ameliorer (<50%): {len(needs_work)} langues")
    for r in needs_work:
        print(f"      {r['name']}: {r['percentage']:.1f}%")

    print("\n" + "=" * 80)

    # Sauvegarder le rapport
    report_path = 'RAPPORT_TRADUCTIONS_FINAL.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RAPPORT FINAL DES TRADUCTIONS - MARTIALCOMP\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 80 + "\n\n")

        f.write("{:<12} {:<15} {:>8} {:>10} {:>10} {:>10} {:>10}\n".format(
            "CODE", "LANGUE", "TOTAL", "TRADUIT", "NON TRAD", "VIDE", "%"
        ))
        f.write("-" * 80 + "\n")

        for r in results:
            status = "[OK]" if r['compiled'] else "[X]"
            f.write("{:<12} {:<15} {:>8} {:>10} {:>10} {:>10} {:>8.1f}% {}\n".format(
                r['lang'],
                r['name'],
                r['total'],
                r['translated'],
                r['untranslated'],
                r['empty'],
                r['percentage'],
                status
            ))

        f.write("-" * 80 + "\n\n")
        f.write(f"STATISTIQUES GLOBALES:\n")
        f.write(f"  - Nombre de langues: {len(results)}\n")
        f.write(f"  - Total entrees (toutes langues): {total_entries}\n")
        f.write(f"  - Total traduit (toutes langues): {total_translated}\n")
        f.write(f"  - Pourcentage moyen: {avg_percentage:.1f}%\n")
        f.write(f"  - Tous compiles: {'OUI' if all_compiled else 'NON'}\n")

    print(f"Rapport sauvegarde: {report_path}")


if __name__ == '__main__':
    main()
