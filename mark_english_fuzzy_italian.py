#!/usr/bin/env python3
"""
Marque les traductions anglaises comme fuzzy dans le fichier PO italien.
Utilise une approche de parsing ligne par ligne plus robuste.
"""

import re

ENGLISH_WORDS = {
    "the", "a", "an", "of", "to", "for", "with", "from", "by", "at", "in", "on",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "do", "does", "did",
    "will", "would", "could", "should", "can", "may", "must",
    "you", "your", "he", "his", "she", "her", "it", "its",
    "we", "our", "they", "their", "this", "that", "these", "those",
    "who", "which", "what",
    "add", "delete", "edit", "save", "cancel", "create", "update", "view",
    "show", "hide", "search", "filter", "select", "submit", "confirm",
    "upload", "download", "import", "export", "click", "enter", "change",
    "remove", "manage", "configure",
    "name", "date", "time", "user", "member", "team", "list", "form",
    "field", "button", "page", "file", "error", "warning", "success",
    "message", "notification", "settings", "profile", "account", "password",
    "status", "type", "category", "competition", "participant", "result",
    "score", "point", "match", "winner", "referee", "judge",
    "new", "old", "active", "available", "valid", "required", "public",
    "open", "closed", "pending", "completed", "approved", "enabled",
    "all", "none", "other", "please", "welcome", "yes", "no", "back", "home",
    "help", "login", "logout", "loading", "successfully", "failed",
    "audit", "tenant", "security", "violation", "detected", "global",
    "details", "critical", "problem",
}

def is_likely_english(text):
    if not text or len(text.strip()) < 5:
        return False

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words or len(words) < 2:
        return False

    english_count = sum(1 for w in words if w in ENGLISH_WORDS and len(w) > 2)
    ratio = english_count / len(words) if words else 0

    return ratio > 0.4


def main():
    po_file = 'locale/it/LC_MESSAGES/django.po'

    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result = []
    marked_count = 0
    i = 0

    while i < len(lines):
        line = lines[i]

        # Chercher les lignes msgstr
        if line.startswith('msgstr "') and not line.startswith('msgstr ""'):
            # Extraire le contenu
            msgstr = line[8:-2] if line.endswith('"\n') else line[8:-1]

            if is_likely_english(msgstr):
                # Remonter pour trouver où insérer le fuzzy
                # Chercher le début de l'entrée (commentaires ou msgid)
                insert_pos = len(result)

                # Remonter jusqu'au début de l'entrée
                while insert_pos > 0:
                    prev = result[insert_pos - 1]
                    if prev.startswith('#') or prev.startswith('msgid'):
                        insert_pos -= 1
                    else:
                        break

                # Vérifier si fuzzy n'est pas déjà présent
                has_fuzzy = False
                for j in range(insert_pos, len(result)):
                    if '#, fuzzy' in result[j] or ', fuzzy' in result[j]:
                        has_fuzzy = True
                        break
                    if result[j].startswith('msgid'):
                        break

                if not has_fuzzy:
                    # Trouver où insérer le flag
                    flag_inserted = False
                    for j in range(insert_pos, len(result)):
                        if result[j].startswith('#,'):
                            # Ajouter fuzzy aux flags existants
                            result[j] = result[j].rstrip('\n')
                            if not result[j].endswith(','):
                                result[j] = '#, fuzzy,' + result[j][2:]
                            else:
                                result[j] = '#, fuzzy,' + result[j][2:]
                            result[j] += '\n'
                            flag_inserted = True
                            break
                        if result[j].startswith('msgid'):
                            break

                    if not flag_inserted:
                        # Insérer avant msgid
                        for j in range(insert_pos, len(result)):
                            if result[j].startswith('msgid'):
                                result.insert(j, '#, fuzzy\n')
                                break

                    marked_count += 1

        result.append(line)
        i += 1

    # Écrire le résultat
    with open(po_file, 'w', encoding='utf-8') as f:
        f.writelines(result)

    print(f"Entrées marquées fuzzy: {marked_count}")


if __name__ == '__main__':
    main()
