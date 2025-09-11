#!/usr/bin/env python3
"""
Script d'audit complet des traductions MartialComp
Analyse tous les templates pour identifier le vrai pourcentage de traduction
"""

import os
import re
import glob
from pathlib import Path

def analyze_template_translations():
    """Analyse tous les templates pour détecter le texte français non traduit."""
    
    template_dirs = [
        'competitions/templates',
        'grades/templates', 
        'finances/templates',
        'shop/templates',
        'organizations/templates'
    ]
    
    results = {
        'total_files': 0,
        'total_french_text': 0,
        'translated_text': 0,
        'untranslated_files': [],
        'critical_missing': []
    }
    
    # Patterns pour détecter le texte français
    french_patterns = [
        r'[>"]([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ][a-zA-Zàáâãäåæçèéêëìíîïðñòóôõöùúûüýÿ\s]{10,})[<"]',  # Phrases françaises
        r'placeholder="([^"]*[àáâãäåæçèéêëìíîïðñòóôõöùúûüýÿ][^"]*)"',  # Placeholders français
        r'title="([^"]*[àáâãäåæçèéêëìíîïðñòóôõöùúûüýÿ][^"]*)"',  # Titles français
        r'content="([^"]*[àáâãäåæçèéêëìíîïðñòóôõöùúûüýÿ][^"]*)"',  # Meta content français
    ]
    
    # Mots-clés français courants à chercher
    french_keywords = [
        'Tableau de bord', 'Gestion', 'Compétitions', 'Pratiquants', 'Clubs',
        'Ajouter', 'Modifier', 'Supprimer', 'Rechercher', 'Filtrer',
        'Nom d\'utilisateur', 'Mot de passe', 'Se connecter', 'Déconnexion',
        'Fonctionnalités', 'Tarifs', 'Contact', 'À propos', 'Accueil'
    ]
    
    for template_dir in template_dirs:
        if os.path.exists(template_dir):
            html_files = glob.glob(f'{template_dir}/**/*.html', recursive=True)
            
            for file_path in html_files:
                results['total_files'] += 1
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Compter les textes français
                    french_matches = []
                    
                    # Recherche par patterns
                    for pattern in french_patterns:
                        matches = re.findall(pattern, content)
                        french_matches.extend(matches)
                    
                    # Recherche par mots-clés
                    for keyword in french_keywords:
                        if keyword in content and f'trans "{keyword}"' not in content:
                            french_matches.append(keyword)
                    
                    # Compter les traductions existantes
                    trans_count = len(re.findall(r'\{%\s*trans\s+', content))
                    translate_count = len(re.findall(r'\{%\s*translate\s+', content))
                    total_translations = trans_count + translate_count
                    
                    french_count = len(set(french_matches))  # Éviter les doublons
                    
                    if french_count > 0:
                        results['total_french_text'] += french_count
                        results['translated_text'] += min(total_translations, french_count)
                        
                        if total_translations < french_count:
                            results['untranslated_files'].append({
                                'file': file_path,
                                'french_count': french_count,
                                'translated_count': total_translations,
                                'coverage': (total_translations / french_count * 100) if french_count > 0 else 0,
                                'sample_french': french_matches[:5]  # Premiers exemples
                            })
                        
                        # Identifier les fichiers critiques
                        if 'welcome.html' in file_path or 'dashboard' in file_path:
                            if total_translations < french_count * 0.5:  # Moins de 50% traduit
                                results['critical_missing'].append({
                                    'file': file_path,
                                    'coverage': (total_translations / french_count * 100) if french_count > 0 else 0,
                                    'missing_count': french_count - total_translations
                                })
                                
                except Exception as e:
                    print(f"Erreur lors de l'analyse de {file_path}: {e}")
    
    return results

def generate_translation_report():
    """Génère un rapport complet de l'état des traductions."""
    
    print("🔍 AUDIT COMPLET DES TRADUCTIONS MARTIALCOMP")
    print("=" * 60)
    
    results = analyze_template_translations()
    
    # Calcul du pourcentage réel
    if results['total_french_text'] > 0:
        real_percentage = (results['translated_text'] / results['total_french_text']) * 100
    else:
        real_percentage = 0
    
    print(f"\n📊 RÉSULTATS GLOBAUX:")
    print(f"   • Fichiers analysés: {results['total_files']}")
    print(f"   • Textes français détectés: {results['total_french_text']}")
    print(f"   • Textes traduits: {results['translated_text']}")
    print(f"   • POURCENTAGE RÉEL: {real_percentage:.1f}%")
    
    print(f"\n🚨 FICHIERS CRITIQUES NON TRADUITS:")
    for item in results['critical_missing'][:10]:  # Top 10
        print(f"   • {item['file']}")
        print(f"     Coverage: {item['coverage']:.1f}% - Manquantes: {item['missing_count']}")
    
    print(f"\n📝 EXEMPLES DE TEXTE FRANÇAIS NON TRADUIT:")
    for item in results['untranslated_files'][:5]:  # Top 5
        print(f"\n   📄 {os.path.basename(item['file'])}")
        print(f"      Coverage: {item['coverage']:.1f}%")
        for sample in item['sample_french'][:3]:
            if len(sample) > 50:
                print(f"      - {sample[:50]}...")
            else:
                print(f"      - {sample}")
    
    print(f"\n🎯 PRIORITÉS D'ACTION:")
    print("   1. 🔥 URGENT: Page d'accueil (welcome.html)")
    print("   2. 🔥 URGENT: Dashboards principaux") 
    print("   3. ⚡ IMPORTANT: Formulaires d'authentification")
    print("   4. ⚡ IMPORTANT: Navigation et menus")
    print("   5. 📋 MOYEN: Templates secondaires")
    
    print(f"\n💡 RECOMMANDATIONS:")
    print("   • Utiliser des scripts automatisés pour convertir le texte français")
    print("   • Prioriser les pages les plus visitées")
    print("   • Tester systématiquement chaque section traduite")
    print("   • Créer un système de suivi continu des traductions")

def create_translation_tracking_system():
    """Crée un système de suivi des traductions."""
    
    tracking_content = """
# SUIVI DES TRADUCTIONS MARTIALCOMP

## Delta de Traduction - État au $(date)

### Méthode de Calcul
- Analyse automatique de tous les templates HTML
- Détection des textes français avec accents/mots-clés
- Comparaison avec les balises {% trans %} existantes
- Calcul du pourcentage réel de couverture

### Commandes de Suivi

```bash
# Audit complet
python scripts/translation_audit.py

# Suivi continu
python manage.py translation_delta --language en

# Test de régression
python manage.py test_translations --all-languages
```

### Objectifs par Phase

#### Phase 1 (Semaine 1) - Objectif: 40%
- [ ] Traduction complète welcome.html
- [ ] Formulaires d'authentification
- [ ] Navigation principale

#### Phase 2 (Semaine 2) - Objectif: 70% 
- [ ] Dashboards coach/manager
- [ ] Menus et sidebars
- [ ] Messages d'erreur

#### Phase 3 (Semaine 3) - Objectif: 90%
- [ ] Templates secondaires
- [ ] Help text et tooltips
- [ ] Footer et pages légales

#### Phase 4 (Semaine 4) - Objectif: 95%+
- [ ] Contenu dynamique
- [ ] Meta descriptions
- [ ] Tests exhaustifs

### Suivi Automatisé

Le script `translation_audit.py` doit être exécuté quotidiennement pour suivre les progrès.
"""
    
    with open('docs/TRANSLATION_TRACKING.md', 'w', encoding='utf-8') as f:
        f.write(tracking_content)
    
    print("📋 Système de suivi créé: docs/TRANSLATION_TRACKING.md")

if __name__ == '__main__':
    generate_translation_report()
    create_translation_tracking_system()