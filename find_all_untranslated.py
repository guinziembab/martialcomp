#!/usr/bin/env python3
"""
Recherche exhaustive des chaînes trans manquantes
"""

import re
from pathlib import Path

def extract_trans_strings(template_path):
    """Extrait toutes les chaînes trans d'un template"""
    strings = set()
    try:
        with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Pattern pour trans "..."
            matches = re.findall(r'{%\s*trans\s+"([^"]+)"\s*%}', content)
            strings.update(matches)
            
            # Pattern pour trans '...'
            matches = re.findall(r"{%\s*trans\s+'([^']+)'\s*%}", content)
            strings.update(matches)
            
    except Exception as e:
        pass
    
    return strings

def check_translation_exists(msgid, po_file_path):
    """Vérifie si une traduction existe dans un fichier .po"""
    try:
        with open(po_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            pattern = f'msgid "{re.escape(msgid)}"'
            return pattern in content
    except:
        return False

# Analyser le dashboard club
dashboard_file = Path('apps/competitions/templates/competitions/dashboard/club.html')
po_file = Path('locale/en/LC_MESSAGES/django.po')

print("="*70)
print("  ANALYSE DES CHAÎNES TRANS MANQUANTES EN ANGLAIS")
print("="*70)
print()

if dashboard_file.exists():
    trans_strings = extract_trans_strings(dashboard_file)
    print(f"Chaînes trans trouvées: {len(trans_strings)}")
    print()
    
    missing = []
    for string in sorted(trans_strings):
        if not check_translation_exists(string, po_file):
            missing.append(string)
    
    if missing:
        print(f"TRADUCTIONS MANQUANTES: {len(missing)}")
        print("-" * 70)
        for i, s in enumerate(missing, 1):
            display = s[:65] + "..." if len(s) > 65 else s
            print(f"{i:3d}. {display}")
    else:
        print("Toutes les chaînes sont traduites!")
    
    print()
    print("="*70)
    print(f"Total: {len(trans_strings)} chaînes, {len(missing)} manquantes")
    print("="*70)

else:
    print("Fichier dashboard non trouvé")
