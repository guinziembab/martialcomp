#!/usr/bin/env python3
"""
Script d'Analyse des Chaînes Non Traduites
==========================================
Analyse tous les templates pour trouver les textes en dur
"""

import re
import os
from pathlib import Path
from collections import defaultdict

def find_untranslated_strings(template_path):
    """Trouve les chaînes potentiellement non traduites dans un template"""
    untranslated = []
    
    with open(template_path, 'r', encoding='utf-8') as f:
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
                # Filtrer les textes significatifs (plus de 2 caractères, commence par majuscule)
                if len(text) > 2 and text[0].isupper() and not text.startswith('&'):
                    untranslated.append({
                        'text': text,
                        'line': line_num,
                        'line_content': line.strip()[:100]
                    })
        
        # Chercher aussi les attributs comme title="", placeholder=""
        attr_matches = re.findall(r'(title|placeholder|alt|aria-label)="([^"]{3,})"', content)
        for attr, text in attr_matches:
            if text[0].isupper() and '{% trans' not in content[:content.find(text)] or True:
                untranslated.append({
                    'text': text,
                    'line': 0,
                    'line_content': f'{attr}="{text}"'
                })
    
    return untranslated

def analyze_templates(base_path='apps/competitions/templates'):
    """Analyse tous les templates"""
    results = defaultdict(list)
    template_count = 0
    
    for template_file in Path(base_path).rglob('*.html'):
        template_count += 1
        untranslated = find_untranslated_strings(template_file)
        if untranslated:
            results[str(template_file)] = untranslated
    
    return results, template_count

if __name__ == '__main__':
    print("="*70)
    print("  ANALYSE DES CHAÎNES NON TRADUITES")
    print("="*70)
    print()
    
    results, total = analyze_templates()
    
    print(f"Templates analysés: {total}")
    print(f"Templates avec textes potentiellement non traduits: {len(results)}")
    print()
    
    # Top 10 des templates avec le plus de textes non traduits
    sorted_results = sorted(results.items(), key=lambda x: len(x[1]), reverse=True)
    
    print("Top 10 des templates à vérifier:")
    print("-" * 70)
    for i, (template, strings) in enumerate(sorted_results[:10], 1):
        print(f"{i}. {template}")
        print(f"   Chaînes trouvées: {len(strings)}")
        # Afficher les 3 premières
        for s in strings[:3]:
            print(f"   - \"{s['text'][:50]}...\"" if len(s['text']) > 50 else f"   - \"{s['text']}\"")
        print()
    
    # Statistiques
    total_strings = sum(len(v) for v in results.values())
    print("="*70)
    print(f"Total de chaînes potentiellement non traduites: {total_strings}")
    print("="*70)
