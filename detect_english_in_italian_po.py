#!/usr/bin/env python3
"""
Script pour détecter et marquer les traductions anglaises dans le fichier PO italien.
Les entrées avec des traductions anglaises seront marquées avec #, fuzzy et un commentaire.
"""

import re

# Mots anglais courants qui ne devraient pas être dans une traduction italienne
ENGLISH_WORDS = {
    # Articles et prépositions
    "the", "a", "an", "of", "to", "for", "with", "from", "by", "at", "in", "on",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "having",
    "do", "does", "did", "doing",
    "will", "would", "could", "should", "can", "may", "might", "must",

    # Pronoms
    "you", "your", "yours", "yourself",
    "he", "his", "him", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "we", "our", "ours", "ourselves",
    "they", "their", "theirs", "themselves",
    "this", "that", "these", "those",
    "who", "whom", "whose", "which", "what",

    # Verbes courants
    "add", "added", "adding",
    "delete", "deleted", "deleting", "deletion",
    "edit", "edited", "editing",
    "save", "saved", "saving",
    "cancel", "cancelled", "cancelling",
    "create", "created", "creating", "creation",
    "update", "updated", "updating",
    "view", "viewed", "viewing",
    "show", "showed", "showing", "shown",
    "hide", "hidden", "hiding",
    "search", "searched", "searching",
    "filter", "filtered", "filtering",
    "select", "selected", "selecting", "selection",
    "submit", "submitted", "submitting",
    "confirm", "confirmed", "confirming", "confirmation",
    "validate", "validated", "validating", "validation",
    "upload", "uploaded", "uploading",
    "download", "downloaded", "downloading",
    "import", "imported", "importing",
    "export", "exported", "exporting",
    "click", "clicked", "clicking",
    "enter", "entered", "entering",
    "choose", "chose", "chosen", "choosing",
    "change", "changed", "changing",
    "remove", "removed", "removing",
    "manage", "managed", "managing", "management",
    "configure", "configured", "configuring", "configuration",

    # Noms courants
    "name", "names",
    "date", "dates",
    "time", "times",
    "user", "users",
    "member", "members",
    "team", "teams",
    "group", "groups",
    "list", "lists",
    "table", "tables",
    "form", "forms",
    "field", "fields",
    "button", "buttons",
    "page", "pages",
    "file", "files",
    "document", "documents",
    "image", "images",
    "photo", "photos",
    "error", "errors",
    "warning", "warnings",
    "success",
    "message", "messages",
    "notification", "notifications",
    "alert", "alerts",
    "settings",
    "options",
    "preferences",
    "profile",
    "account",
    "password",
    "email",
    "phone",
    "address",
    "city",
    "country",
    "status",
    "type", "types",
    "category", "categories",
    "competition", "competitions",
    "participant", "participants",
    "result", "results",
    "score", "scores",
    "point", "points",
    "match", "matches",
    "round", "rounds",
    "winner", "winners",
    "loser", "losers",
    "referee", "referees",
    "judge", "judges",
    "coach", "coaches",
    "training",
    "schedule",
    "calendar",
    "event", "events",
    "registration", "registrations",
    "payment", "payments",
    "invoice", "invoices",
    "receipt", "receipts",
    "amount",
    "total",
    "price",
    "discount",

    # Adjectifs courants
    "new", "old",
    "active", "inactive",
    "available", "unavailable",
    "valid", "invalid",
    "required", "optional",
    "public", "private",
    "open", "closed",
    "pending", "completed", "cancelled",
    "approved", "rejected",
    "enabled", "disabled",
    "visible", "hidden",
    "selected", "unselected",
    "current", "previous", "next",
    "first", "last",
    "all", "none", "some", "any",
    "other", "another",

    # Phrases courantes
    "please", "thank",
    "welcome",
    "hello", "goodbye",
    "yes", "no",
    "ok", "okay",
    "back", "forward",
    "home",
    "help",
    "about",
    "contact",
    "login", "logout",
    "sign", "signin", "signout", "signup",
    "register", "registered",
    "forgot",
    "remember",
    "loading",
    "processing",
    "successfully",
    "failed",
    "not found",
    "access denied",
    "unauthorized",
    "forbidden",

    # Termes techniques
    "audit", "audits", "audited",
    "tenant", "tenants",
    "security",
    "violation", "violations",
    "detected",
    "global",
    "specific",
    "component", "components",
    "holding",
    "details",
    "critical",
    "problem",
    "issue", "issues",
}

# Phrases anglaises complètes à détecter
ENGLISH_PHRASES = [
    "are you sure",
    "click here",
    "please wait",
    "no results",
    "no data",
    "not found",
    "access denied",
    "permission denied",
    "successfully",
    "has been",
    "have been",
    "will be",
    "would be",
    "could be",
    "should be",
    "must be",
    "can be",
    "may be",
    "might be",
    "there is",
    "there are",
    "this is",
    "that is",
    "it is",
    "you are",
    "we are",
    "they are",
    "do you",
    "did you",
    "would you",
    "could you",
    "can you",
    "please select",
    "please enter",
    "please provide",
    "please confirm",
    "please wait",
    "loading...",
    "processing...",
    "of the",
    "for the",
    "in the",
    "on the",
    "at the",
    "to the",
    "from the",
    "with the",
    "by the",
    "security audit",
    "violations found",
    "violations detected",
    "type of audit",
    "all components",
    "specific tenant",
]


def is_likely_english(text):
    """Vérifie si un texte est probablement en anglais."""
    if not text or not text.strip():
        return False, []

    # Ignorer les textes très courts (moins de 3 caractères)
    if len(text.strip()) < 3:
        return False, []

    # Ignorer les textes qui sont juste des nombres, symboles ou variables
    if re.match(r'^[\d\s\-\+\*\/\=\%\{\}\(\)\[\]\.,:;!?]+$', text):
        return False, []

    # Ignorer les textes qui contiennent principalement des variables Python
    if text.count('%') > 2 or text.count('{') > 2:
        return False, []

    text_lower = text.lower()
    found_english = []

    # Vérifier les phrases anglaises
    for phrase in ENGLISH_PHRASES:
        if phrase in text_lower:
            found_english.append(f"phrase: '{phrase}'")

    # Compter les mots anglais
    words = re.findall(r'\b[a-zA-Z]+\b', text_lower)
    if not words:
        return False, []

    english_words_found = []
    for word in words:
        if word in ENGLISH_WORDS and len(word) > 2:
            english_words_found.append(word)

    # Si plus de 40% des mots sont anglais, c'est probablement de l'anglais
    english_ratio = len(english_words_found) / len(words) if words else 0

    if english_ratio > 0.4 or len(found_english) > 0:
        if english_words_found:
            unique_words = list(set(english_words_found))[:5]
            found_english.append(f"mots: {', '.join(unique_words)}")
        return True, found_english

    return False, []


def process_po_file(filepath):
    """Traite le fichier PO pour marquer les traductions anglaises."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    result_lines = []

    english_found_count = 0
    entries_checked = 0

    i = 0
    while i < len(lines):
        line = lines[i]

        # Collecter les commentaires existants
        comments = []
        while i < len(lines) and lines[i].startswith('#'):
            comments.append(lines[i])
            i += 1

        if i >= len(lines):
            result_lines.extend(comments)
            break

        line = lines[i]

        # Détecter un msgid
        if line.startswith('msgid '):
            msgid_lines = [line]
            msgid_content = ""

            if line == 'msgid ""':
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_lines.append(lines[i])
                    msgid_content += lines[i][1:-1]
                    i += 1
            else:
                match = re.match(r'msgid "(.*)"', line)
                if match:
                    msgid_content = match.group(1)
                i += 1

            # Collecter msgid_plural si présent
            msgid_plural_lines = []
            while i < len(lines) and lines[i].startswith('msgid_plural'):
                msgid_plural_lines.append(lines[i])
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    msgid_plural_lines.append(lines[i])
                    i += 1

            # Collecter msgstr
            msgstr_lines = []
            msgstr_content = ""

            if i < len(lines) and lines[i].startswith('msgstr'):
                if lines[i].startswith('msgstr['):
                    # Pluriel
                    while i < len(lines) and (lines[i].startswith('msgstr[') or lines[i].startswith('"')):
                        if lines[i].startswith('msgstr['):
                            match = re.match(r'msgstr\[\d+\] "(.*)"', lines[i])
                            if match:
                                msgstr_content += match.group(1) + " "
                        elif lines[i].startswith('"'):
                            msgstr_content += lines[i][1:-1] + " "
                        msgstr_lines.append(lines[i])
                        i += 1
                else:
                    msgstr_lines.append(lines[i])
                    if lines[i] == 'msgstr ""':
                        i += 1
                        while i < len(lines) and lines[i].startswith('"'):
                            msgstr_content += lines[i][1:-1]
                            msgstr_lines.append(lines[i])
                            i += 1
                    else:
                        match = re.match(r'msgstr "(.*)"', lines[i])
                        if match:
                            msgstr_content = match.group(1)
                        i += 1

            entries_checked += 1

            # Vérifier si la traduction est en anglais
            is_english, reasons = is_likely_english(msgstr_content)

            # Ne pas marquer si le msgid est identique au msgstr (pas de traduction)
            if msgid_content.strip() == msgstr_content.strip():
                is_english = False

            if is_english and msgstr_content.strip():
                english_found_count += 1

                # Ajouter le marqueur fuzzy si pas déjà présent
                has_fuzzy = any('#, fuzzy' in c or ', fuzzy' in c for c in comments)

                if not has_fuzzy:
                    # Chercher s'il y a déjà une ligne de flags
                    flag_line_idx = None
                    for idx, c in enumerate(comments):
                        if c.startswith('#,'):
                            flag_line_idx = idx
                            break

                    if flag_line_idx is not None:
                        # Ajouter fuzzy aux flags existants
                        comments[flag_line_idx] = comments[flag_line_idx].replace('#,', '#, fuzzy,')
                    else:
                        # Ajouter une nouvelle ligne de flags
                        comments.append('#, fuzzy')

                # Ajouter un commentaire pour expliquer
                reason_str = "; ".join(reasons[:3]) if reasons else "détection automatique"
                comments.append(f'#. ATTENTION: Traduction en anglais détectée ({reason_str})')

            # Écrire l'entrée
            result_lines.extend(comments)
            result_lines.extend(msgid_lines)
            result_lines.extend(msgid_plural_lines)
            result_lines.extend(msgstr_lines)

            continue

        # Écrire les commentaires collectés
        result_lines.extend(comments)

        # Écrire la ligne courante si ce n'est pas un msgid
        if not line.startswith('msgid '):
            result_lines.append(line)
            i += 1

    print(f"  Entrées vérifiées: {entries_checked}")
    print(f"  Traductions anglaises détectées et marquées fuzzy: {english_found_count}")

    return '\n'.join(result_lines)


def main():
    po_file = 'locale/it/LC_MESSAGES/django.po'

    print(f"Analyse de {po_file} pour détecter les traductions anglaises...")

    result = process_po_file(po_file)

    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\nFichier mis à jour.")
    print("Les traductions anglaises sont maintenant marquées avec:")
    print("  - #, fuzzy (pour les signaler comme à revoir)")
    print("  - Un commentaire explicatif")
    print("\nVous pouvez les trouver facilement en cherchant 'ATTENTION: Traduction en anglais' dans le fichier.")


if __name__ == '__main__':
    main()
