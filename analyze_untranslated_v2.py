#!/usr/bin/env python3
"""
Script d'Analyse des Chaînes Non Traduites - Version 2
"""

import re
import os
from pathlib import Path
from collections import defaultdict

def find_untranslated_strings(template_path):
    """Trouve les chaînes potentiellement non traduites"""
    untranslated = []
    
    try:
        with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Ignorer les lignes avec des balises Django
                if '{%' in line or '{{' in line or '<!--' in line:
                    continue
                
                # Chercher du texte entre > et <
                matches = re.findall(r'>([^<{]+)<', line)
                for match in matches:
                    text = match.strip()
                    # Filtrer les textes significatifs
                    if len(text) > 2 and text[0].isupper():
                        untranslated.append(text)
    except Exception as e:
        pass
    
    return list(set(untranslated))  # Unique

def analyze_templates(base_path='apps/competitions/templates'):
    """Analyse tous les templates"""
    results = defaultdict(list)
    template_count = 0
    all_strings = set()
    
    for template_file in Path(base_path).rglob('*.html'):
        template_count += 1
        untranslated = find_untranslated_strings(template_file)
        if untranslated:
            results[str(template_file)] = untranslated
            all_strings.update(untranslated)
    
    return results, template_count, all_strings

if __name__ == '__main__':
    print("="*70)
    print("  ANALYSE DES CHAÎNES NON TRADUITES")
    print("="*70)
    print()
    
    results, total, all_strings = analyze_templates()
    
    print(f"Templates analysés: {total}")
    print(f"Templates avec textes: {len(results)}")
    print(f"Chaînes uniques trouvées: {len(all_strings)}")
    print()
    
    # Top strings
    print("Exemples de chaînes trouvées:")
    print("-" * 70)
    for i, s in enumerate(sorted(all_strings)[:20], 1):
        display = s[:60] + "..." if len(s) > 60 else s
        print(f"{i}. {display}")
    
    print()
    print("="*70)
    print(f"Total: {len(all_strings)} chaînes à vérifier")
    print("="*70)
