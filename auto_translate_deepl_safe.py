#!/usr/bin/env python3
"""
Traduction automatique sécurisée avec DeepL - Échappe correctement les guillemets.
"""

import re
import time

try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

DEEPL_API_KEY = "a9f775a0-fe09-4711-bef3-1a860bbfa60e:fx"


def is_english(text):
    """Détecte si un texte est en anglais."""
    if not text or len(text.strip()) < 5:
        return False
    patterns = [
        r'\bthe\s+\w+', r'\byou\s+(are|have|can)',
        r'\bis\s+(a|the|not)', r'\bhas\s+been\b',
    ]
    return any(re.search(p, text.lower()) for p in patterns)


def escape_for_po(text):
    """Échappe un texte pour le format PO."""
    # Remplacer les guillemets typographiques par des apostrophes
    text = text.replace('"', "'")
    text = text.replace('"', "'")
    text = text.replace('„', "'")
    text = text.replace('«', "'")
    text = text.replace('»', "'")
    # Échapper les backslashes et les guillemets droits
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    return text


def main():
    if not DEEPL_AVAILABLE:
        print("Erreur: pip install deepl")
        return

    translator = deepl.Translator(DEEPL_API_KEY)
    po_file = 'locale/it/LC_MESSAGES/django.po'

    print("Lecture du fichier PO...")
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    stats = {'total': 0, 'translated': 0, 'errors': 0}

    i = 0
    while i < len(lines):
        # Commentaires
        comments = []
        while i < len(lines) and lines[i].startswith('#'):
            if '#, fuzzy' not in lines[i]:
                comments.append(lines[i])
            i += 1

        if i >= len(lines):
            result_lines.extend(comments)
            break

        # msgid
        if lines[i].startswith('msgid '):
            msgid_lines = [lines[i]]
            msgid_text = ''
            match = re.match(r'msgid "(.*)"', lines[i])
            if match:
                msgid_text = match.group(1).replace('\\n', '\n').replace('\\"', '"')
            i += 1

            while i < len(lines) and lines[i].startswith('"'):
                msgid_lines.append(lines[i])
                content = lines[i].strip()[1:-1]
                msgid_text += content.replace('\\n', '\n').replace('\\"', '"')
                i += 1

            # msgid_plural
            while i < len(lines) and lines[i].startswith('msgid_plural'):
                msgid_lines.append(lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_lines.append(lines[i])
                    i += 1

            # msgstr
            msgstr_lines = []
            if i < len(lines) and lines[i].startswith('msgstr'):
                if lines[i].startswith('msgstr['):
                    # Pluriel
                    while i < len(lines) and (
                        lines[i].startswith('msgstr[') or lines[i].startswith('"')
                    ):
                        msgstr_lines.append(lines[i])
                        i += 1
                else:
                    # Simple
                    msgstr_text = ''
                    match = re.match(r'msgstr "(.*)"', lines[i])
                    if match:
                        msgstr_text = match.group(1).replace('\\n', '\n')
                    original_line = lines[i]
                    i += 1

                    while i < len(lines) and lines[i].startswith('"'):
                        content = lines[i].strip()[1:-1]
                        msgstr_text += content.replace('\\n', '\n')
                        i += 1

                    # Traduire si anglais
                    if msgstr_text.strip() and is_english(msgstr_text):
                        stats['total'] += 1
                        try:
                            result = translator.translate_text(
                                msgid_text, source_lang="FR", target_lang="IT"
                            )
                            italian = escape_for_po(result.text)

                            # Préserver les \n du msgid
                            if msgid_text.endswith('\n'):
                                if not italian.endswith('\\n'):
                                    italian += '\\n'

                            msgstr_lines = [f'msgstr "{italian}"\n']
                            stats['translated'] += 1

                            if stats['translated'] % 10 == 0:
                                print(f"  Traduites: {stats['translated']}")

                            time.sleep(0.1)

                        except Exception as e:
                            print(f"  Erreur: {str(e)[:50]}")
                            stats['errors'] += 1
                            msgstr_lines = [original_line]
                    else:
                        # Garder tel quel
                        msgstr_lines = [original_line]
                        j = i - 1
                        while j >= 0 and lines[j].startswith('"'):
                            msgstr_lines.insert(0, lines[j])
                            j -= 1

            # Écrire l'entrée
            result_lines.extend(comments)
            result_lines.extend(msgid_lines)
            result_lines.extend(msgstr_lines)
            continue

        result_lines.append(lines[i])
        i += 1

    # Sauvegarder
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print("\n=== TRADUCTION TERMINEE ===")
    print(f"Trouvees : {stats['total']}")
    print(f"Traduites: {stats['translated']}")
    print(f"Erreurs  : {stats['errors']}")


if __name__ == '__main__':
    main()
