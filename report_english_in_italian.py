#!/usr/bin/env python3
"""
Génère un rapport des traductions anglaises dans le fichier PO italien.
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
        return False, 0

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words:
        return False, 0

    english_count = sum(1 for w in words if w in ENGLISH_WORDS and len(w) > 2)
    ratio = english_count / len(words) if words else 0

    return ratio > 0.4, ratio

def main():
    po_file = 'locale/it/LC_MESSAGES/django.po'

    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse entries
    pattern = r'msgid "(.*?)"\nmsgstr "(.*?)"'

    english_entries = []
    line_num = 1

    for line in content.split('\n'):
        if line.startswith('msgstr "') and not line.startswith('msgstr ""'):
            msgstr = line[8:-1]
            is_eng, ratio = is_likely_english(msgstr)
            if is_eng:
                english_entries.append({
                    'line': line_num,
                    'text': msgstr[:80],
                    'ratio': ratio
                })
        line_num += 1

    # Write report
    report_file = 'rapport_traductions_anglaises_IT.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("RAPPORT: Traductions anglaises dans le fichier PO italien\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total détecté: {len(english_entries)} entrées\n\n")
        f.write("-" * 80 + "\n")

        for entry in english_entries[:100]:  # Limiter à 100 premiers
            f.write(f"Ligne {entry['line']}: {entry['text']}...\n")

        if len(english_entries) > 100:
            f.write(f"\n... et {len(english_entries) - 100} autres\n")

    print(f"Rapport généré: {report_file}")
    print(f"Total: {len(english_entries)} traductions anglaises détectées")

if __name__ == '__main__':
    main()
