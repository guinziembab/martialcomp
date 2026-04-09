#!/usr/bin/env python3
"""
Traduction automatique des entrées anglaises FR→IT avec DeepL API.
Nécessite: pip install deepl
"""

import re
import time

try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False
    print("DeepL non installé. Installez avec: pip install deepl")

# Clé API DeepL
DEEPL_API_KEY = "a9f775a0-fe09-4711-bef3-1a860bbfa60e:fx"

def is_english(text):
    """Détecte si un texte est en anglais."""
    if not text or len(text.strip()) < 5:
        return False

    english_patterns = [
        r'\bthe\s+\w+',
        r'\ba\s+\w+',
        r'\byou\s+(are|have|can|will)',
        r'\bis\s+(a|the|not)',
        r'\bhas\s+been\b',
        r'\bclick\s+(here|on|to)',
        r'\bplease\s+\w+',
    ]

    return any(re.search(pattern, text.lower()) for pattern in english_patterns)

def translate_po_with_deepl(api_key):
    """Traduit toutes les entrées anglaises avec DeepL."""
    if not DEEPL_AVAILABLE:
        print("Erreur: deepl n'est pas installé")
        return

    translator = deepl.Translator(api_key)
    po_file = 'locale/it/LC_MESSAGES/django.po'

    print("Lecture du fichier PO...")
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    stats = {
        'total': 0,
        'translated': 0,
        'errors': 0,
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Collecter commentaires
        comments = []
        while i < len(lines) and lines[i].startswith('#'):
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
                msgid_text = match.group(1)
            i += 1

            while i < len(lines) and lines[i].startswith('"'):
                msgid_lines.append(lines[i])
                content = lines[i].strip()[1:-1] if lines[i].strip().endswith('"') else lines[i].strip()[1:]
                msgid_text += content
                i += 1

            # msgid_plural
            msgid_plural_lines = []
            while i < len(lines) and lines[i].startswith('msgid_plural'):
                msgid_plural_lines.append(lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_plural_lines.append(lines[i])
                    i += 1

            # msgstr
            msgstr_lines = []
            msgstr_text = ''

            if i < len(lines) and lines[i].startswith('msgstr'):
                if lines[i].startswith('msgstr['):
                    # Pluriel - garder tel quel
                    while i < len(lines) and (lines[i].startswith('msgstr[') or lines[i].startswith('"')):
                        msgstr_lines.append(lines[i])
                        i += 1
                else:
                    # msgstr simple
                    match = re.match(r'msgstr "(.*)"', lines[i])
                    if match:
                        msgstr_text = match.group(1)
                    msgstr_lines.append(lines[i])
                    i += 1

                    while i < len(lines) and lines[i].startswith('"'):
                        content = lines[i].strip()[1:-1] if lines[i].strip().endswith('"') else lines[i].strip()[1:]
                        msgstr_text += content
                        msgstr_lines.append(lines[i])
                        i += 1

                    # Traduire si anglais
                    if msgstr_text.strip() and is_english(msgstr_text):
                        stats['total'] += 1

                        try:
                            # Traduire FR → IT via msgid (source française)
                            result = translator.translate_text(
                                msgid_text,
                                source_lang="FR",
                                target_lang="IT"
                            )
                            italian_text = result.text

                            # Remplacer msgstr
                            msgstr_lines = [f'msgstr "{italian_text}"\n']
                            stats['translated'] += 1

                            # Retirer fuzzy si présent
                            comments = [c for c in comments if '#, fuzzy' not in c and ', fuzzy' not in c]

                            if stats['translated'] % 10 == 0:
                                print(f"  Traduites: {stats['translated']}/{stats['total']}")

                            # Pause pour éviter rate limiting
                            time.sleep(0.1)

                        except Exception as e:
                            print(f"  Erreur traduction: {str(e)[:50]}")
                            stats['errors'] += 1

            # Écrire l'entrée
            result_lines.extend(comments)
            result_lines.extend(msgid_lines)
            result_lines.extend(msgid_plural_lines)
            result_lines.extend(msgstr_lines)
            continue

        result_lines.append(lines[i])
        i += 1

    # Sauvegarder
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print("\n=== TRADUCTION DEEPL TERMINEE ===")
    print(f"Entrees anglaises trouvees : {stats['total']}")
    print(f"Traduites avec succes : {stats['translated']}")
    print(f"Erreurs : {stats['errors']}")

def main():
    if DEEPL_API_KEY == "VOTRE_CLE_API_ICI":
        print("=" * 60)
        print("CONFIGURATION REQUISE")
        print("=" * 60)
        print("\n1. Obtenez une cle API DeepL gratuite :")
        print("   https://www.deepl.com/pro#developer")
        print("\n2. Installez la bibliotheque DeepL :")
        print("   pip install deepl")
        print("\n3. Modifiez ce script et remplacez DEEPL_API_KEY")
        print("\n4. Relancez le script")
        print("\n" + "=" * 60)
        return

    translate_po_with_deepl(DEEPL_API_KEY)

if __name__ == '__main__':
    main()
