#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analyse du fichier PO français pour détecter les problèmes de caractères"""

import re

def analyze_po_file():
    with open('locale/fr/LC_MESSAGES/django.po', 'r', encoding='utf-8') as f:
        content = f.read()

    problems = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Détecter les msgstr
        if line.startswith('msgstr "'):
            # Extraire le texte complet (peut être sur plusieurs lignes)
            text = ""
            match = re.match(r'msgstr "(.*)"', line)
            if match:
                text = match.group(1)

            # Vérifier les lignes de continuation
            j = i + 1
            while j < len(lines) and lines[j].startswith('"'):
                cont_match = re.match(r'"(.*)"', lines[j])
                if cont_match:
                    text += cont_match.group(1)
                j += 1

            if text:
                # 1. Encodage corrompu (caractères mojibake)
                mojibake_patterns = [
                    (r'Ã©', 'é'),
                    (r'Ã¨', 'è'),
                    (r'Ã ', 'à'),
                    (r'Ã¢', 'â'),
                    (r'Ãª', 'ê'),
                    (r'Ã®', 'î'),
                    (r'Ã´', 'ô'),
                    (r'Ã»', 'û'),
                    (r'Ã§', 'ç'),
                    (r'Ã¹', 'ù'),
                    (r'â€™', "'"),
                    (r'â€"', '—'),
                    (r'â€œ', '"'),
                    (r'â€', '"'),
                    (r'Â', ''),
                    (r'Ã', ''),
                ]

                for pattern, replacement in mojibake_patterns:
                    if pattern in text:
                        problems.append((i+1, 'Mojibake', pattern, text[:100]))
                        break

                # 2. Texte en anglais dans msgstr français
                english_indicators = [
                    r'\bthe\b', r'\bis\b', r'\bare\b', r'\bwas\b', r'\bwere\b',
                    r'\bhave\b', r'\bhas\b', r'\bhad\b', r'\bwill\b', r'\bwould\b',
                    r'\bcan\b', r'\bcould\b', r'\bshould\b', r'\bmust\b',
                    r'\bthis\b', r'\bthat\b', r'\bthese\b', r'\bthose\b',
                    r'\byour\b', r'\byou\b', r'\bplease\b', r'\bclick\b',
                    r'\bsave\b', r'\bdelete\b', r'\bedit\b', r'\badd\b',
                    r'\bsuccessfully\b', r'\berror\b', r'\bfailed\b',
                    r'\benter\b', r'\bselect\b', r'\bchoose\b',
                ]

                text_lower = text.lower()
                for eng_pattern in english_indicators:
                    if re.search(eng_pattern, text_lower) and len(text) > 10:
                        # Vérifier que ce n'est pas un faux positif
                        if not any(fr in text_lower for fr in ['française', 'anglais', 'the ', "l'the"]):
                            problems.append((i+1, 'Anglais', eng_pattern, text[:100]))
                            break

                # 3. Caractères de contrôle ou invisibles problématiques
                if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text):
                    problems.append((i+1, 'Caractère contrôle', '', text[:100]))

                # 4. Double espaces
                if '  ' in text and 'msgid' not in lines[i-1] if i > 0 else True:
                    pass  # Acceptable dans certains cas

        i += 1

    return problems

if __name__ == '__main__':
    problems = analyze_po_file()
    print(f"Problèmes détectés: {len(problems)}")
    print("=" * 80)

    # Grouper par type
    by_type = {}
    for p in problems:
        ptype = p[1]
        if ptype not in by_type:
            by_type[ptype] = []
        by_type[ptype].append(p)

    for ptype, items in by_type.items():
        print(f"\n{ptype}: {len(items)} occurrences")
        print("-" * 40)
        for item in items[:20]:
            print(f"  Ligne {item[0]}: {item[3][:70]}...")
