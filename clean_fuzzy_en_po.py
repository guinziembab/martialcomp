#!/usr/bin/env python3
"""
Script pour nettoyer les flags fuzzy dans le fichier PO anglais.
Les traductions fuzzy avec un msgstr non-vide sont validées.
"""

import re

def clean_fuzzy_flags(filepath):
    """Nettoie les flags fuzzy qui ont une traduction valide."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result_lines = []
    fuzzy_removed = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Détection d'une entrée fuzzy
        if line.startswith('#, fuzzy'):
            # Regarder en avant pour voir s'il y a une traduction valide
            j = i + 1

            # Passer les commentaires
            while j < len(lines) and lines[j].startswith('#'):
                j += 1

            # Trouver le msgid
            msgid_content = ""
            if j < len(lines) and lines[j].startswith('msgid '):
                if lines[j] == 'msgid ""':
                    # msgid multiligne
                    j += 1
                    while j < len(lines) and lines[j].startswith('"'):
                        msgid_content += lines[j][1:-1]
                        j += 1
                else:
                    msgid_content = lines[j][7:-1]
                    j += 1

            # Passer msgid_plural si présent
            if j < len(lines) and lines[j].startswith('msgid_plural'):
                while j < len(lines) and not lines[j].startswith('msgstr'):
                    j += 1

            # Vérifier le msgstr
            msgstr_content = ""
            if j < len(lines):
                if lines[j].startswith('msgstr['):
                    # Pluriel - vérifier msgstr[0] et msgstr[1]
                    has_valid_plural = True
                    while j < len(lines) and lines[j].startswith('msgstr['):
                        if 'msgstr[' in lines[j]:
                            match = re.match(r'msgstr\[\d+\] "(.*)"', lines[j])
                            if match:
                                plural_str = match.group(1)
                            else:
                                plural_str = ""
                            j += 1
                            # Lignes de continuation
                            while j < len(lines) and lines[j].startswith('"'):
                                plural_str += lines[j][1:-1]
                                j += 1
                            if not plural_str.strip():
                                has_valid_plural = False
                    if has_valid_plural:
                        # Enlever le flag fuzzy et garder les autres flags
                        if line == '#, fuzzy':
                            # On ne garde pas cette ligne
                            fuzzy_removed += 1
                        else:
                            # Il y a d'autres flags, enlever juste fuzzy
                            new_flags = line.replace('fuzzy, ', '').replace(', fuzzy', '').replace('fuzzy', '')
                            if new_flags.strip() and new_flags != '#, ':
                                result_lines.append(new_flags)
                            fuzzy_removed += 1
                        i += 1
                        continue

                elif lines[j].startswith('msgstr "'):
                    # Simple msgstr
                    match = re.match(r'msgstr "(.*)"', lines[j])
                    if match:
                        msgstr_content = match.group(1)
                    j += 1
                    # Lignes de continuation
                    while j < len(lines) and lines[j].startswith('"'):
                        msgstr_content += lines[j][1:-1]
                        j += 1

                elif lines[j] == 'msgstr ""':
                    j += 1
                    # Vérifier si c'est un msgstr multiligne ou vide
                    if j < len(lines) and lines[j].startswith('"'):
                        while j < len(lines) and lines[j].startswith('"'):
                            msgstr_content += lines[j][1:-1]
                            j += 1

            # Si on a une traduction non-vide, enlever le flag fuzzy
            if msgstr_content.strip():
                # Enlever le flag fuzzy
                if line == '#, fuzzy':
                    # On ne garde pas cette ligne
                    fuzzy_removed += 1
                else:
                    # Il y a d'autres flags (ex: #, fuzzy, python-format), enlever juste fuzzy
                    new_flags = line.replace('fuzzy, ', '').replace(', fuzzy', '').replace('fuzzy', '')
                    if new_flags.strip() and new_flags != '#, ':
                        result_lines.append(new_flags)
                    fuzzy_removed += 1
                i += 1
                continue

        result_lines.append(line)
        i += 1

    print(f"  Flags fuzzy supprimés: {fuzzy_removed}")

    return '\n'.join(result_lines)


def main():
    po_file = 'locale/en/LC_MESSAGES/django.po'

    print(f"Nettoyage des flags fuzzy dans {po_file}...")

    result = clean_fuzzy_flags(po_file)

    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Fichier mis à jour.")


if __name__ == '__main__':
    main()
