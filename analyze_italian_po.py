#!/usr/bin/env python3
"""
Analyse complète du fichier PO italien pour détecter tous les textes en anglais.
"""

import re
from collections import defaultdict

# Mots anglais communs (liste étendue)
ENGLISH_INDICATORS = {
    # Articles
    "the", "a", "an",
    # Prépositions communes
    "of", "to", "for", "with", "from", "by", "at", "in", "on", "about",
    # Verbes être/avoir
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "having",
    # Verbes modaux
    "will", "would", "could", "should", "can", "may", "must", "might",
    # Pronoms
    "you", "your", "yours", "he", "his", "him", "she", "her", "it", "its",
    "we", "our", "they", "their", "this", "that", "these", "those",
    # Questions
    "who", "what", "where", "when", "why", "how", "which",
    # Négation
    "not", "no", "none",
    # Verbes courants qui n'existent pas en italien
    "click", "select", "submit", "delete", "manage", "upload", "download",
    "view", "show", "hide", "edit", "save", "cancel", "update",
    # Noms courants anglais différents de l'italien
    "user", "users", "member", "members", "settings", "account", "password",
    "email", "phone", "address", "status", "message", "messages",
    "error", "errors", "warning", "success", "loading",
    # Termes techniques
    "tenant", "tenants", "audit", "violation", "violations", "detected",
    "security", "critical", "holding", "component", "components",
}

# Mots qui sont identiques en anglais et italien (à ignorer)
IDENTICAL_WORDS = {
    "no", "ok", "status", "admin", "club", "bonus", "martial",
    "standard", "performance", "video", "hotel", "euro",
}

def is_english(text):
    """Détermine si un texte est probablement en anglais."""
    if not text or len(text.strip()) < 3:
        return False, []

    # Ignorer si c'est juste des variables/nombres
    if re.match(r'^[\d\s\-\+\*\/\=\%\{\}\(\)\[\]\.,:;!?]+$', text):
        return False, []

    # Compter les variables (à ignorer dans le calcul)
    var_count = text.count('%') + text.count('{')

    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    if not words or len(words) - var_count < 2:
        return False, []

    # Retirer les mots identiques
    words = [w for w in words if w not in IDENTICAL_WORDS]

    if not words:
        return False, []

    # Détecter les mots anglais
    english_words = [w for w in words if w in ENGLISH_INDICATORS and len(w) > 1]

    # Calculer le ratio
    ratio = len(english_words) / len(words) if words else 0

    # Patterns anglais typiques
    english_patterns = [
        r'\bthe\s+\w+',
        r'\byou\s+(are|have|can|must|should)',
        r'\bis\s+(not|a|the)',
        r'\bhas\s+been\b',
        r'\bhave\s+been\b',
        r'\bwill\s+be\b',
        r'\bclick\s+(here|on|to)',
        r'\bplease\s+\w+',
    ]

    has_english_pattern = any(re.search(pattern, text.lower()) for pattern in english_patterns)

    if ratio > 0.3 or has_english_pattern:
        return True, english_words[:10]

    return False, []

def analyze_po_file():
    """Analyse le fichier PO italien."""
    po_file = 'locale/it/LC_MESSAGES/django.po'

    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    stats = {
        'total_entries': 0,
        'translated': 0,
        'empty': 0,
        'english': 0,
        'italian': 0,
        'fuzzy': 0,
    }

    english_entries = []
    current_entry = {
        'line_num': 0,
        'msgid': '',
        'msgstr': '',
        'is_fuzzy': False,
    }

    in_msgid = False
    in_msgstr = False

    for i, line in enumerate(lines, 1):
        line = line.strip()

        # Détecter fuzzy
        if line.startswith('#, fuzzy') or ', fuzzy' in line:
            current_entry['is_fuzzy'] = True
            stats['fuzzy'] += 1

        # Détecter msgid
        if line.startswith('msgid '):
            if current_entry['msgstr']:
                # Analyser l'entrée précédente
                stats['total_entries'] += 1

                if not current_entry['msgstr']:
                    stats['empty'] += 1
                elif is_english(current_entry['msgstr'])[0]:
                    stats['english'] += 1
                    eng, words = is_english(current_entry['msgstr'])
                    english_entries.append({
                        'line': current_entry['line_num'],
                        'msgid': current_entry['msgid'][:80],
                        'msgstr': current_entry['msgstr'][:80],
                        'words': words,
                        'fuzzy': current_entry['is_fuzzy'],
                    })
                else:
                    stats['translated'] += 1
                    stats['italian'] += 1

            # Nouvelle entrée
            current_entry = {
                'line_num': i,
                'msgid': '',
                'msgstr': '',
                'is_fuzzy': False,
            }
            in_msgid = True
            in_msgstr = False

            # Extraire msgid
            match = re.match(r'msgid "(.*)"', line)
            if match:
                current_entry['msgid'] = match.group(1)

        elif line.startswith('msgstr ') and not line.startswith('msgstr['):
            in_msgid = False
            in_msgstr = True

            # Extraire msgstr
            match = re.match(r'msgstr "(.*)"', line)
            if match:
                current_entry['msgstr'] = match.group(1)

        elif line.startswith('"') and (in_msgid or in_msgstr):
            # Ligne de continuation
            content = line[1:-1] if line.endswith('"') else line[1:]
            if in_msgid:
                current_entry['msgid'] += content
            elif in_msgstr:
                current_entry['msgstr'] += content

    # Dernière entrée
    if current_entry['msgstr']:
        stats['total_entries'] += 1
        if is_english(current_entry['msgstr'])[0]:
            stats['english'] += 1
            eng, words = is_english(current_entry['msgstr'])
            english_entries.append({
                'line': current_entry['line_num'],
                'msgid': current_entry['msgid'][:80],
                'msgstr': current_entry['msgstr'][:80],
                'words': words,
                'fuzzy': current_entry['is_fuzzy'],
            })
        else:
            stats['italian'] += 1

    # Générer le rapport
    report = []
    report.append("=" * 100)
    report.append("ANALYSE COMPLÈTE DU FICHIER PO ITALIEN")
    report.append("=" * 100)
    report.append("")
    report.append(f"Total d'entrées analysées : {stats['total_entries']}")
    report.append(f"Entrées traduites en italien : {stats['italian']} ({stats['italian']/stats['total_entries']*100:.1f}%)")
    report.append(f"Entrées en ANGLAIS (à traduire) : {stats['english']} ({stats['english']/stats['total_entries']*100:.1f}%)")
    report.append(f"Entrées vides (non traduites) : {stats['empty']}")
    report.append(f"Entrées marquées fuzzy : {stats['fuzzy']}")
    report.append("")
    report.append("=" * 100)
    report.append("LISTE DES TRADUCTIONS EN ANGLAIS À CORRIGER")
    report.append("=" * 100)
    report.append("")

    # Grouper par fuzzy/non-fuzzy
    fuzzy_entries = [e for e in english_entries if e['fuzzy']]
    non_fuzzy_entries = [e for e in english_entries if not e['fuzzy']]

    report.append(f"--- ENTRÉES EN ANGLAIS MARQUÉES FUZZY ({len(fuzzy_entries)}) ---")
    report.append("")
    for entry in fuzzy_entries[:50]:
        report.append(f"Ligne {entry['line']}:")
        report.append(f"  FR: {entry['msgid']}")
        report.append(f"  EN: {entry['msgstr']}")
        report.append(f"  Mots anglais détectés: {', '.join(entry['words'][:5])}")
        report.append("")

    if len(fuzzy_entries) > 50:
        report.append(f"... et {len(fuzzy_entries) - 50} autres entrées fuzzy en anglais")
        report.append("")

    report.append("")
    report.append(f"--- ENTRÉES EN ANGLAIS NON MARQUÉES FUZZY ({len(non_fuzzy_entries)}) ---")
    report.append("(Ces entrées sont les plus problématiques car elles ne sont pas signalées)")
    report.append("")
    for entry in non_fuzzy_entries[:100]:
        report.append(f"Ligne {entry['line']}:")
        report.append(f"  FR: {entry['msgid']}")
        report.append(f"  EN: {entry['msgstr']}")
        report.append(f"  Mots anglais: {', '.join(entry['words'][:5])}")
        report.append("")

    if len(non_fuzzy_entries) > 100:
        report.append(f"... et {len(non_fuzzy_entries) - 100} autres entrées non-fuzzy en anglais")

    # Sauvegarder le rapport
    report_file = 'RAPPORT_COMPLET_ITALIEN_PO.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print('\n'.join(report[:30]))
    print(f"\nRapport complet sauvegardé dans: {report_file}")

    return stats, english_entries

if __name__ == '__main__':
    stats, entries = analyze_po_file()
