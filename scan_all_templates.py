#!/usr/bin/env python3
"""
Scan complet de tous les templates
"""

import re
from pathlib import Path

def extract_all_trans(base_path='apps'):
    """Extrait toutes les chaines trans"""
    all_strings = set()
    template_count = 0
    
    for template in Path(base_path).rglob('*.html'):
        template_count += 1
        try:
            with open(template, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                matches = re.findall(r'{%\s*trans\s+"([^"]+)"\s*%}', content)
                all_strings.update(matches)
                matches = re.findall(r"{%\s*trans\s+'([^']+)'\s*%}", content)
                all_strings.update(matches)
        except:
            pass
    
    return all_strings, template_count

def check_in_po(strings, po_file='locale/en/LC_MESSAGES/django.po'):
    """Verifie quelles chaines manquent"""
    try:
        with open(po_file, 'r', encoding='utf-8', errors='ignore') as f:
            po_content = f.read()
    except:
        return list(strings)
    
    missing = []
    for s in sorted(strings):
        if f'msgid "{s}"' not in po_content:
            missing.append(s)
    
    return missing

print("="*70)
print("  SCAN COMPLET DE TOUS LES TEMPLATES")
print("="*70)
print()

all_strings, template_count = extract_all_trans()

print(f"Templates analyses: {template_count}")
print(f"Chaines trans uniques: {len(all_strings)}")
print()

missing = check_in_po(all_strings)

print(f"Traductions manquantes: {len(missing)}")
print()

if missing:
    print("50 premieres:")
    print("-" * 70)
    for i, s in enumerate(missing[:50], 1):
        display = s[:60] + "..." if len(s) > 60 else s
        print(f"{i:3d}. {display}")
    
    if len(missing) > 50:
        print(f"\n... et {len(missing) - 50} autres")

# Sauvegarder
with open('missing_translations_full.txt', 'w', encoding='utf-8') as f:
    for s in sorted(missing):
        f.write(f"{s}\n")

print()
print("="*70)
print(f"Total: {len(all_strings)} chaines, {len(missing)} manquantes")
print("="*70)
print()
print("Liste complete: missing_translations_full.txt")
