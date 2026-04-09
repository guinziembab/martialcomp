#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère un résumé prioritaire des problèmes de traduction
en excluant les fichiers de backup et les faux positifs
"""

import json
from pathlib import Path
from collections import defaultdict

REPORT_DIR = Path(__file__).parent / 'rapports_traductions'
JSON_REPORT = REPORT_DIR / 'rapport_traductions_complet.json'
PRIORITY_REPORT = REPORT_DIR / 'rapport_prioritaire.md'

# Patterns pour identifier les fichiers de backup
BACKUP_PATTERNS = [
    'backup', 'Backup', 'BACKUP',
    '.backup', '.old', '.new', '_OLD', '_NEW',
    'Packages-', 'Package_', 'Production-',
    'migration_package', 'production_complete',
]

# Types de problèmes à prioriser
PRIORITY_TYPES = [
    'default:"',  # Valeurs par défaut dans les templates
    'message":',  # Messages d'erreur/succès
    'title":',    # Titres
    'label":',    # Labels
    'error":',    # Erreurs
    'success":',  # Messages de succès
]

def is_backup_file(filepath: str) -> bool:
    """Vérifie si un fichier est un backup"""
    for pattern in BACKUP_PATTERNS:
        if pattern in filepath:
            return True
    return False

def is_priority_issue(issue: dict) -> bool:
    """Vérifie si un problème est prioritaire"""
    context = issue.get('context', '').lower()
    text = issue.get('text', '').lower()
    
    # Ignorer les commentaires
    if context.strip().startswith('//') or context.strip().startswith('#'):
        return False
    
    # Ignorer les console.log (sauf si vraiment important)
    if 'console.log' in context or 'console.error' in context or 'console.warn' in context:
        return False
    
    # Ignorer les docstrings
    if '"""' in context or "'''" in context:
        return False
    
    # Prioriser les messages utilisateur
    for priority_type in PRIORITY_TYPES:
        if priority_type in context:
            return True
    
    # Prioriser les textes dans les templates (pas dans les commentaires)
    if issue.get('type') == 'template_hardcoded_french':
        if '{% trans' not in context and '{% translate' not in context:
            # Vérifier que ce n'est pas un commentaire HTML
            if not context.strip().startswith('<!--'):
                return True
    
    # Prioriser les messages d'erreur/succès dans Python
    if issue.get('type') == 'python_hardcoded_french':
        if any(word in text for word in ['erreur', 'succès', 'message', 'validation', 'enregistré']):
            return True
    
    return False

def generate_priority_report():
    """Génère un rapport prioritaire"""
    print("📊 Génération du rapport prioritaire...")
    
    # Charger le rapport JSON
    with open(JSON_REPORT, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = data.get('issues', {})
    
    # Filtrer les problèmes prioritaires
    priority_issues = defaultdict(list)
    stats = {
        'total_files': 0,
        'priority_files': 0,
        'total_issues': 0,
        'priority_issues': 0,
    }
    
    for filepath, file_issues in issues.items():
        stats['total_files'] += 1
        
        # Ignorer les fichiers de backup
        if is_backup_file(filepath):
            continue
        
        stats['priority_files'] += 1
        
        for issue in file_issues:
            stats['total_issues'] += 1
            if is_priority_issue(issue):
                priority_issues[filepath].append(issue)
                stats['priority_issues'] += 1
    
    # Générer le rapport
    with open(PRIORITY_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Rapport Prioritaire des Traductions\n\n")
        f.write("## Résumé\n\n")
        f.write(f"- **Fichiers analysés:** {stats['total_files']}\n")
        f.write(f"- **Fichiers actifs (hors backup):** {stats['priority_files']}\n")
        f.write(f"- **Total problèmes trouvés:** {stats['total_issues']}\n")
        f.write(f"- **Problèmes prioritaires:** {stats['priority_issues']}\n\n")
        f.write("## Problèmes Prioritaires à Corriger\n\n")
        f.write("> ⚠️ **Note:** Ce rapport exclut les fichiers de backup et se concentre sur les problèmes critiques.\n\n")
        
        if not priority_issues:
            f.write("✅ **Aucun problème prioritaire trouvé !**\n\n")
        else:
            # Trier par nombre de problèmes
            sorted_files = sorted(priority_issues.items(), key=lambda x: len(x[1]), reverse=True)
            
            for filepath, file_issues in sorted_files[:50]:  # Limiter aux 50 premiers fichiers
                f.write(f"### {filepath}\n\n")
                f.write(f"**{len(file_issues)} problème(s) prioritaire(s)**\n\n")
                
                for issue in file_issues[:10]:  # Limiter à 10 problèmes par fichier
                    f.write(f"- **Ligne {issue['line']}:** `{issue['text']}`\n")
                    f.write(f"  - Type: {issue['type']}\n")
                    f.write(f"  - Contexte: `{issue['context'][:150]}`\n\n")
                
                if len(file_issues) > 10:
                    f.write(f"  *... et {len(file_issues) - 10} autre(s) problème(s)*\n\n")
                
                f.write("\n")
            
            if len(sorted_files) > 50:
                f.write(f"\n*... et {len(sorted_files) - 50} autre(s) fichier(s) avec des problèmes*\n\n")
        
        f.write("## Recommandations\n\n")
        f.write("1. **Corriger en priorité:** Les messages d'erreur, de succès et les valeurs par défaut dans les templates\n")
        f.write("2. **Utiliser `{% trans %}`** pour les textes dans les templates\n")
        f.write("3. **Utiliser `_(\"texte\")`** pour les chaînes dans Python\n")
        f.write("4. **Utiliser `default:_(\"texte\")`** pour les valeurs par défaut dans les filtres\n")
        f.write("5. **Exécuter `python manage.py makemessages -l en`** pour mettre à jour les fichiers de traduction\n")
        f.write("6. **Exécuter `python manage.py compilemessages`** pour compiler les traductions\n\n")
    
    print(f"✅ Rapport prioritaire généré: {PRIORITY_REPORT}")
    print(f"   - {stats['priority_issues']} problèmes prioritaires dans {stats['priority_files']} fichiers actifs")

if __name__ == '__main__':
    generate_priority_report()
