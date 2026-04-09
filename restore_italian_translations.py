#!/usr/bin/env python3
"""
Restaure les traductions italiennes valides depuis le backup
et ne marque fuzzy QUE les vrais textes anglais.
"""

import re
from collections import defaultdict

# Mots anglais (liste stricte pour éviter faux positifs)
ENGLISH_WORDS = {
    "the", "a", "an", "of", "to", "for", "with", "from", "by", "at", "in", "on",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "having",
    "will", "would", "could", "should", "can", "may", "must", "might",
    "you", "your", "yours", "he", "his", "him", "she", "her", "it", "its",
    "we", "our", "ours", "they", "their", "this", "that", "these", "those",
    "who", "whom", "which", "what", "where", "when", "why", "how",
    "not", "no", "yes",
    "click", "select", "submit", "delete", "manage", "upload", "download",
    "view", "show", "hide", "edit", "save", "cancel", "update", "create",
    "user", "users", "member", "members", "settings", "account", "password",
    "email", "phone", "address", "message", "messages",
    "error", "errors", "warning", "success", "loading", "please",
}

# Mots identiques en anglais et italien (à ignorer)
IDENTICAL_WORDS = {"no", "ok", "admin", "club", "euro", "sport", "video"}

def is_definitely_english(text):
    """Détecte si un texte est VRAIMENT en anglais (stricte)."""
    if not text or len(text.strip()) < 5:
        return False

    # Patterns anglais très spécifiques
    english_patterns = [
        r'\bthe\s+\w+',
        r'\ba\s+\w+',
        r'\byou\s+(are|have|can|will|should|must)',
        r'\bis\s+(a|the|not)',
        r'\bare\s+(a|the|not)',
        r'\bhas\s+been\b',
        r'\bhave\s+been\b',
        r'\bwill\s+be\b',
        r'\bclick\s+(here|on|to)',
        r'\bplease\s+\w+',
        r'\bthis\s+is\b',
        r'\bthat\s+is\b',
        r'\bto\s+the\b',
        r'\bof\s+the\b',
        r'\bfor\s+the\b',
        r'\bin\s+the\b',
        r'\bon\s+the\b',
    ]

    text_lower = text.lower()

    # Si correspond à un pattern anglais typique → anglais
    if any(re.search(pattern, text_lower) for pattern in english_patterns):
        return True

    # Compter les mots anglais
    words = re.findall(r'\b[a-zA-Z]+\b', text_lower)
    if not words or len(words) < 3:
        return False

    # Retirer les mots identiques
    words = [w for w in words if w not in IDENTICAL_WORDS and len(w) > 2]

    if not words:
        return False

    english_count = sum(1 for w in words if w in ENGLISH_WORDS)
    ratio = english_count / len(words)

    # Seuil strict : au moins 50% de mots anglais
    return ratio >= 0.5

def extract_translations(po_file):
    """Extrait toutes les traductions d'un fichier PO."""
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    translations = {}
    current_msgid = ''
    current_msgstr = ''
    in_msgid = False
    in_msgstr = False

    for line in lines:
        line_stripped = line.strip()

        if line_stripped.startswith('msgid '):
            if current_msgid and current_msgstr:
                translations[current_msgid] = current_msgstr

            current_msgid = ''
            current_msgstr = ''
            in_msgid = True
            in_msgstr = False

            match = re.match(r'msgid "(.*)"', line_stripped)
            if match:
                current_msgid = match.group(1)

        elif line_stripped.startswith('"') and in_msgid:
            content = line_stripped[1:-1] if line_stripped.endswith('"') else line_stripped[1:]
            current_msgid += content

        elif line_stripped.startswith('msgstr ') and not line_stripped.startswith('msgstr['):
            in_msgid = False
            in_msgstr = True

            match = re.match(r'msgstr "(.*)"', line_stripped)
            if match:
                current_msgstr = match.group(1)

        elif line_stripped.startswith('"') and in_msgstr:
            content = line_stripped[1:-1] if line_stripped.endswith('"') else line_stripped[1:]
            current_msgstr += content

        elif line_stripped.startswith('msgid_plural') or line_stripped.startswith('msgstr['):
            in_msgid = False
            in_msgstr = False

    # Dernière entrée
    if current_msgid and current_msgstr:
        translations[current_msgid] = current_msgstr

    return translations

def main():
    current_file = 'locale/it/LC_MESSAGES/django.po'
    backup_file = 'locale/it/LC_MESSAGES/django.po.backup_20251206'

    print("Extraction des traductions italiennes du backup...")
    backup_translations = extract_translations(backup_file)
    print(f"  - {len(backup_translations)} traductions trouvées dans le backup")

    print("\nLecture du fichier actuel...")
    with open(current_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    result_lines = []
    stats = {
        'restored': 0,
        'kept_english': 0,
        'marked_fuzzy': 0,
    }

    i = 0
    while i < len(lines):
        line = lines[i]

        # Collecter commentaires
        comments = []
        while i < len(lines) and lines[i].startswith('#'):
            # Ne pas garder les vieux flags fuzzy
            if not lines[i].startswith('#, fuzzy') and ', fuzzy' not in lines[i]:
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

                    # Vérifier si le msgstr actuel est anglais
                    if msgstr_text.strip() and is_definitely_english(msgstr_text):
                        # Chercher dans le backup
                        if msgid_text in backup_translations:
                            backup_msgstr = backup_translations[msgid_text]

                            # Vérifier que le backup n'est PAS anglais
                            if backup_msgstr.strip() and not is_definitely_english(backup_msgstr):
                                # Restaurer la traduction du backup
                                msgstr_lines = [f'msgstr "{backup_msgstr}"\n']
                                stats['restored'] += 1
                            else:
                                # Le backup est aussi en anglais, marquer fuzzy
                                comments.append('#, fuzzy\n')
                                stats['marked_fuzzy'] += 1
                                stats['kept_english'] += 1
                        else:
                            # Pas de backup, marquer fuzzy
                            comments.append('#, fuzzy\n')
                            stats['marked_fuzzy'] += 1
                            stats['kept_english'] += 1

            # Écrire l'entrée
            result_lines.extend(comments)
            result_lines.extend(msgid_lines)
            result_lines.extend(msgid_plural_lines)
            result_lines.extend(msgstr_lines)
            continue

        result_lines.append(lines[i])
        i += 1

    # Sauvegarder
    with open(current_file, 'w', encoding='utf-8') as f:
        f.writelines(result_lines)

    print("\n=== RESTAURATION TERMINEE ===")
    print(f"Traductions italiennes restaurees depuis backup : {stats['restored']}")
    print(f"Textes anglais conserves (pas de traduction IT valide) : {stats['kept_english']}")
    print(f"Entrees marquees fuzzy pour revision : {stats['marked_fuzzy']}")
    print(f"\nTotal de traductions anglaises a traduire : {stats['kept_english']}")

if __name__ == '__main__':
    main()
