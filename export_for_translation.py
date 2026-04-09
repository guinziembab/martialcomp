#!/usr/bin/env python3
"""
Exporte les textes à traduire dans un format simple pour traduction externe.
"""

import re
import csv

def is_english(text):
    """Détecte si un texte est en anglais."""
    if not text or len(text.strip()) < 5:
        return False

    english_patterns = [
        r'\bthe\s+\w+', r'\ba\s+\w+', r'\byou\s+(are|have|can)',
        r'\bis\s+(a|the|not)', r'\bhas\s+been\b', r'\bclick\s+',
    ]

    return any(re.search(pattern, text.lower()) for pattern in english_patterns)

def export_to_csv():
    """Exporte les textes anglais vers CSV pour traduction."""
    po_file = 'locale/it/LC_MESSAGES/django.po'

    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    to_translate = []
    current_msgid = ''
    current_msgstr = ''
    line_num = 0

    for i, line in enumerate(lines, 1):
        if line.startswith('msgid "'):
            match = re.match(r'msgid "(.*)"', line)
            if match:
                current_msgid = match.group(1)
                line_num = i

        elif line.startswith('msgstr "'):
            match = re.match(r'msgstr "(.*)"', line)
            if match:
                current_msgstr = match.group(1)

                if current_msgstr.strip() and is_english(current_msgstr):
                    to_translate.append({
                        'line': line_num,
                        'french': current_msgid,
                        'english': current_msgstr,
                        'italian': ''  # À remplir
                    })

    # Exporter en CSV
    csv_file = 'traductions_a_faire_IT.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['line', 'french', 'english', 'italian'])
        writer.writeheader()
        writer.writerows(to_translate)

    print(f"Export termine : {csv_file}")
    print(f"  {len(to_translate)} textes a traduire")
    print("\nVous pouvez maintenant :")
    print("1. Ouvrir le CSV dans Excel/Google Sheets")
    print("2. Copier la colonne 'french' dans Google Translate FR->IT")
    print("3. Coller le resultat dans la colonne 'italian'")
    print("4. Sauvegarder le CSV")
    print("5. Lancer import_translations.py pour reimporter")

    return to_translate

def import_from_csv():
    """Importe les traductions depuis le CSV."""
    csv_file = 'traductions_a_faire_IT.csv'
    po_file = 'locale/it/LC_MESSAGES/django.po'

    # Lire les traductions
    translations = {}
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['italian'].strip():
                translations[row['french']] = row['italian']

    print(f"Importation de {len(translations)} traductions...")

    # Modifier le PO
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    updated = 0
    i = 0

    while i < len(lines):
        if lines[i].startswith('msgid "'):
            # Collecter msgid
            msgid_text = ''
            match = re.match(r'msgid "(.*)"', lines[i])
            if match:
                msgid_text = match.group(1)

            # Écrire msgid
            result_lines.append(lines[i])
            i += 1

            # Lignes continuation msgid
            while i < len(lines) and lines[i].startswith('"'):
                result_lines.append(lines[i])
                content = lines[i].strip()[1:-1] if lines[i].strip().endswith('"') else lines[i].strip()[1:]
                msgid_text += content
                i += 1

            # msgstr
            if i < len(lines) and lines[i].startswith('msgstr "'):
                if msgid_text in translations:
                    # Remplacer par la traduction
                    result_lines.append(f'msgstr "{translations[msgid_text]}"\n')
                    updated += 1
                    i += 1
                    # Sauter les lignes de continuation
                    while i < len(lines) and lines[i].startswith('"'):
                        i += 1
                else:
                    result_lines.append(lines[i])
                    i += 1
            else:
                if i < len(lines):
                    result_lines.append(lines[i])
                i += 1
        else:
            result_lines.append(lines[i])
            i += 1

    # Sauvegarder
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print(f"Importation terminee : {updated} traductions ajoutees")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'import':
        import_from_csv()
    else:
        export_to_csv()
