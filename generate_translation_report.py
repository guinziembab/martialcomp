#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un rapport détaillé des chaînes non traduites avec catégorisation
"""

import json
from pathlib import Path
from collections import defaultdict
import re

PROJECT_ROOT = Path(__file__).parent
REPORT_FILE = PROJECT_ROOT / "untranslated_strings_report.json"
OUTPUT_REPORT = PROJECT_ROOT / "RAPPORT_ANALYSE_TRADUCTIONS.md"

def detect_encoding_issues(text):
    """Détecte les problèmes d'encodage courants"""
    issues = []
    
    # Problèmes d'encodage courants
    encoding_map = {
        'Ã‰': 'É',
        'Ã©': 'é',
        'Ã¨': 'è',
        'Ãª': 'ê',
        'Ã«': 'ë',
        'Ã ': 'à',
        'Ã¢': 'â',
        'Ã§': 'ç',
        'Ã´': 'ô',
        'Ã¹': 'ù',
        'Ã»': 'û',
        'Ã¯': 'ï',
        'Ã®': 'î',
        'Ã°': 'ð',
        'Ã±': 'ñ',
        'ÃŽ': 'Î',
        'Ã': 'À',
        'Ã¿': 'ÿ',
        'â‚¬': '€',
        'â€"': '—',
        'â€"': '–',
        'â€˜': ''',
        'â€™': ''',
        'â€œ': '"',
        'â€': '"',
        'Ã‚': 'Â',
        'Ã‹': 'Ë',
        'Ã‹': 'Ë',
    }
    
    for wrong, correct in encoding_map.items():
        if wrong in text:
            issues.append(f"'{wrong}' devrait être '{correct}'")
    
    return issues

def is_english_text(text):
    """Détecte si le texte est en anglais"""
    # Mots anglais courants
    english_words = [
        'you', 'are', 'not', 'this', 'that', 'the', 'a', 'an', 'is', 'was',
        'were', 'have', 'has', 'had', 'been', 'been', 'for', 'with', 'from',
        'successfully', 'error', 'saved', 'submitted', 'registered', 'assigned',
        'judge', 'performance', 'competition', 'scoring', 'configuration',
        'missing', 'required', 'data', 'found', 'open', 'completed', 'started',
        'unable', 'disqualified', 'cancelled', 'created', 'updated', 'settings',
        'criteria', 'criterion', 'all', 'please', 'complete', 'before'
    ]
    
    text_lower = text.lower()
    english_count = sum(1 for word in english_words if word in text_lower)
    
    # Si plus de 2 mots anglais sont trouvés, c'est probablement de l'anglais
    return english_count >= 2

def categorize_strings(missing_strings):
    """Catégorise les chaînes manquantes"""
    categories = {
        'encoding_issues': [],  # Problèmes d'encodage (Ã‰ au lieu de É)
        'english_strings': [],  # Chaînes en anglais non traduites
        'new_french_strings': [],  # Nouvelles chaînes françaises
        'duplicates': [],  # Doublons détectés
        'other': []  # Autres
    }
    
    seen_strings = set()
    
    for string, locations in missing_strings.items():
        # Vérifier les doublons
        if string in seen_strings:
            categories['duplicates'].append({
                'string': string,
                'locations': locations
            })
            continue
        
        seen_strings.add(string)
        
        # Détecter les problèmes d'encodage
        encoding_issues = detect_encoding_issues(string)
        if encoding_issues:
            categories['encoding_issues'].append({
                'string': string,
                'issues': encoding_issues,
                'locations': locations
            })
            continue
        
        # Détecter les chaînes en anglais
        if is_english_text(string):
            categories['english_strings'].append({
                'string': string,
                'locations': locations
            })
            continue
        
        # Autres chaînes françaises
        categories['new_french_strings'].append({
            'string': string,
            'locations': locations
        })
    
    return categories

def generate_markdown_report():
    """Génère un rapport Markdown détaillé"""
    
    if not REPORT_FILE.exists():
        print(f"❌ Fichier de rapport non trouvé: {REPORT_FILE}")
        return
    
    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    missing_strings = data.get('missing_strings', {})
    
    # Catégoriser
    categories = categorize_strings(missing_strings)
    
    # Générer le rapport Markdown
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# 📊 RAPPORT D'ANALYSE DES TRADUCTIONS\n\n")
        f.write("**Date:** " + str(Path(__file__).stat().st_mtime) + "\n\n")
        f.write("---\n\n")
        
        # Résumé
        f.write("## 📈 RÉSUMÉ\n\n")
        f.write(f"- **Total chaînes dans le PO:** {data['total_po_strings']}\n")
        f.write(f"- **Total chaînes dans le code:** {data['total_code_strings']}\n")
        f.write(f"- **Chaînes manquantes:** {data['missing_count']}\n\n")
        
        f.write("### 📋 Catégorisation\n\n")
        f.write(f"- **Problèmes d'encodage:** {len(categories['encoding_issues'])}\n")
        f.write(f"- **Chaînes en anglais:** {len(categories['english_strings'])}\n")
        f.write(f"- **Nouvelles chaînes françaises:** {len(categories['new_french_strings'])}\n")
        f.write(f"- **Doublons:** {len(categories['duplicates'])}\n")
        f.write(f"- **Autres:** {len(categories['other'])}\n\n")
        
        f.write("---\n\n")
        
        # Problèmes d'encodage
        if categories['encoding_issues']:
            f.write("## ⚠️ PROBLÈMES D'ENCODAGE\n\n")
            f.write(f"**Total:** {len(categories['encoding_issues'])}\n\n")
            
            by_file = defaultdict(list)
            for item in categories['encoding_issues']:
                for loc in item['locations']:
                    by_file[loc['file']].append({
                        'string': item['string'],
                        'line': loc['line'],
                        'issues': item['issues']
                    })
            
            for file_path, items in sorted(by_file.items()):
                f.write(f"### 📄 {file_path}\n\n")
                for item in sorted(items, key=lambda x: x['line']):
                    f.write(f"**Ligne {item['line']}:**\n")
                    f.write(f"- Chaîne: `{item['string']}`\n")
                    f.write(f"- Problèmes détectés:\n")
                    for issue in item['issues']:
                        f.write(f"  - {issue}\n")
                    f.write("\n")
            
            f.write("---\n\n")
        
        # Chaînes en anglais
        if categories['english_strings']:
            f.write("## 🇬🇧 CHAÎNES EN ANGLAIS NON TRADUITES\n\n")
            f.write(f"**Total:** {len(categories['english_strings'])}\n\n")
            f.write("> ⚠️ **Action requise:** Ces chaînes doivent être traduites en français.\n\n")
            
            by_file = defaultdict(list)
            for item in categories['english_strings']:
                for loc in item['locations']:
                    by_file[loc['file']].append({
                        'string': item['string'],
                        'line': loc['line']
                    })
            
            for file_path, items in sorted(by_file.items()):
                f.write(f"### 📄 {file_path}\n\n")
                for item in sorted(items, key=lambda x: x['line']):
                    f.write(f"- **Ligne {item['line']}:** `{item['string']}`\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        # Nouvelles chaînes françaises
        if categories['new_french_strings']:
            f.write("## 🇫🇷 NOUVELLES CHAÎNES FRANÇAISES\n\n")
            f.write(f"**Total:** {len(categories['new_french_strings'])}\n\n")
            f.write("> ✅ **Action requise:** Ajouter ces chaînes au fichier PO.\n\n")
            
            by_file = defaultdict(list)
            for item in categories['new_french_strings']:
                for loc in item['locations']:
                    by_file[loc['file']].append({
                        'string': item['string'],
                        'line': loc['line']
                    })
            
            for file_path, items in sorted(by_file.items()):
                f.write(f"### 📄 {file_path}\n\n")
                for item in sorted(items, key=lambda x: x['line']):
                    display_string = item['string'].replace('\n', '\\n').replace('\t', '\\t')
                    if len(display_string) > 150:
                        display_string = display_string[:150] + "..."
                    f.write(f"- **Ligne {item['line']}:** `{display_string}`\n")
                f.write("\n")
            
            f.write("---\n\n")
        
        # Doublons
        if categories['duplicates']:
            f.write("## 🔄 DOUBLONS DÉTECTÉS\n\n")
            f.write(f"**Total:** {len(categories['duplicates'])}\n\n")
            for item in categories['duplicates'][:20]:  # Limiter à 20
                f.write(f"- `{item['string']}`\n")
                for loc in item['locations'][:3]:  # Limiter à 3 locations
                    f.write(f"  - {loc['file']}:{loc['line']}\n")
                if len(item['locations']) > 3:
                    f.write(f"  - ... et {len(item['locations']) - 3} autres\n")
            if len(categories['duplicates']) > 20:
                f.write(f"\n... et {len(categories['duplicates']) - 20} autres doublons\n")
            f.write("\n---\n\n")
        
        # Statistiques par fichier
        f.write("## 📊 STATISTIQUES PAR FICHIER\n\n")
        by_file = defaultdict(int)
        for string, locations in missing_strings.items():
            for loc in locations:
                by_file[loc['file']] += 1
        
        f.write("| Fichier | Nombre de chaînes manquantes |\n")
        f.write("|---------|---------------------------|\n")
        for file_path, count in sorted(by_file.items(), key=lambda x: -x[1])[:30]:
            f.write(f"| `{file_path}` | {count} |\n")
        
        if len(by_file) > 30:
            f.write(f"\n... et {len(by_file) - 30} autres fichiers\n")
        
        f.write("\n---\n\n")
        f.write("## 📝 RECOMMANDATIONS\n\n")
        f.write("1. **Problèmes d'encodage:** Corriger les chaînes avec des problèmes d'encodage dans le code source.\n")
        f.write("2. **Chaînes en anglais:** Traduire toutes les chaînes en anglais en français.\n")
        f.write("3. **Nouvelles chaînes:** Ajouter toutes les nouvelles chaînes françaises au fichier PO.\n")
        f.write("4. **Doublons:** Vérifier et supprimer les doublons éventuels.\n")
        f.write("5. **Exécuter `python3 manage.py makemessages -l fr` pour mettre à jour le fichier PO.\n")
        f.write("6. **Compiler les traductions:** `python3 manage.py compilemessages`\n")
    
    print(f"✅ Rapport Markdown généré: {OUTPUT_REPORT}")
    print(f"\n📊 Statistiques:")
    print(f"   - Problèmes d'encodage: {len(categories['encoding_issues'])}")
    print(f"   - Chaînes en anglais: {len(categories['english_strings'])}")
    print(f"   - Nouvelles chaînes françaises: {len(categories['new_french_strings'])}")
    print(f"   - Doublons: {len(categories['duplicates'])}")

if __name__ == "__main__":
    generate_markdown_report()
