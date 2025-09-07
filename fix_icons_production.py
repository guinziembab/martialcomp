#!/usr/bin/env python3
"""
Script pour corriger les icônes volumineuses sur le serveur de production.
Ce script peut être exécuté directement sur le serveur de production.
"""

import os
import sys
import re
from pathlib import Path

def remove_svg_icons_from_template():
    """Supprimer les icônes SVG volumineuses du template base.html"""
    
    template_path = Path("apps/competitions/templates/competitions/dashboard/base.html")
    
    if not template_path.exists():
        print(f"❌ Template non trouvé: {template_path}")
        return False
    
    print(f"📝 Lecture du template: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Patterns de remplacement pour supprimer les icônes SVG
    replacements = [
        # Lien Accueil
        (
            r'<a href="{% url \'competitions:dashboard:index\' %}" class="nav-link[^"]*">\s*<svg class="nav-icon"[^>]*>.*?</svg>{% trans "Accueil" %}</a>',
            '<a href="{% url \'competitions:dashboard:index\' %}" class="nav-link {% if request.path == \'/dashboard/\' %}active{% endif %}">\n                    {% trans "Accueil" %}\n                </a>'
        ),
        # Lien Compétitions
        (
            r'<a href="{% url \'competitions:competitions:list\' %}" class="nav-link">\s*<svg class="nav-icon"[^>]*>.*?</svg>{% trans "Compétitions" %}</a>',
            '<a href="{% url \'competitions:competitions:list\' %}" class="nav-link">\n                    {% trans "Compétitions" %}\n                </a>'
        ),
        # Lien Profil
        (
            r'<a href="{% url \'profile\' %}" class="nav-link">\s*<svg class="nav-icon"[^>]*>.*?</svg>{% trans "Profil" %}</a>',
            '<a href="{% url \'profile\' %}" class="nav-link">\n                    {% trans "Profil" %}\n                </a>'
        ),
        # Lien Documentation
        (
            r'<a href="{% url \'competitions:dashboard:documentation\' %}" class="nav-link[^"]*">\s*<svg class="nav-icon"[^>]*>.*?</svg>\s*{% translate "Documentation" %}\s*</a>',
            '<a href="{% url \'competitions:dashboard:documentation\' %}" class="nav-link {% if \'/dashboard/documentation/\' in request.path %}active{% endif %}">\n                    {% translate "Documentation" %}\n                </a>'
        ),
        # Lien Déconnexion
        (
            r'<a href="{% url \'account_logout\' %}" class="nav-link">\s*<svg class="nav-icon"[^>]*>.*?</svg>\s*{% translate "Déconnexion" %}\s*</a>',
            '<a href="{% url \'account_logout\' %}" class="nav-link">\n                    {% translate "Déconnexion" %}\n                </a>'
        )
    ]
    
    # Appliquer les remplacements
    modified = False
    for pattern, replacement in replacements:
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            modified = True
            print(f"✅ Icône supprimée: {pattern[:50]}...")
    
    # Supprimer le CSS .nav-icon inutilisé
    css_pattern = r'\.nav-icon\s*\{[^}]*\}'
    if re.search(css_pattern, content, re.DOTALL):
        content = re.sub(css_pattern, '', content, flags=re.DOTALL)
        modified = True
        print("✅ CSS .nav-icon supprimé")
    
    if modified:
        # Créer une sauvegarde
        backup_path = template_path.with_suffix('.html.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(open(template_path, 'r', encoding='utf-8').read())
        print(f"💾 Sauvegarde créée: {backup_path}")
        
        # Écrire le nouveau contenu
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Template mis à jour: {template_path}")
        return True
    else:
        print("ℹ️ Aucune modification nécessaire")
        return True

def add_missing_dashboard_guide_url():
    """Ajouter l'URL pattern dashboard_guide manquant"""
    
    urls_path = Path("apps/competitions/urls/dashboard.py")
    
    if not urls_path.exists():
        print(f"❌ Fichier URLs non trouvé: {urls_path}")
        return False
    
    print(f"📝 Lecture des URLs: {urls_path}")
    
    with open(urls_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si l'URL existe déjà
    if 'dashboard_guide' in content:
        print("ℹ️ URL dashboard_guide déjà présente")
        return True
    
    # Ajouter l'URL pattern après les URLs de documentation
    pattern = r"(path\('documentation/<str:dashboard_type>/', documentation\.dashboard_documentation, name='dashboard_documentation'\),)"
    replacement = r"\1\n    path('documentation/<str:dashboard_type>/guide/', documentation.dashboard_guide, name='dashboard_guide'),"
    
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        
        # Créer une sauvegarde
        backup_path = urls_path.with_suffix('.py.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(open(urls_path, 'r', encoding='utf-8').read())
        print(f"💾 Sauvegarde créée: {backup_path}")
        
        # Écrire le nouveau contenu
        with open(urls_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ URL dashboard_guide ajoutée: {urls_path}")
        return True
    else:
        print("❌ Pattern de documentation non trouvé dans les URLs")
        return False

def main():
    """Fonction principale"""
    print("🔧 Correction des icônes volumineuses - MartialComp")
    print("=" * 50)
    
    success = True
    
    # 1. Supprimer les icônes SVG
    print("\n1. Suppression des icônes SVG volumineuses...")
    if not remove_svg_icons_from_template():
        success = False
    
    # 2. Ajouter l'URL manquant
    print("\n2. Ajout de l'URL dashboard_guide...")
    if not add_missing_dashboard_guide_url():
        success = False
    
    if success:
        print("\n🎉 Corrections appliquées avec succès !")
        print("\n📋 Actions suivantes recommandées:")
        print("   - Redémarrer l'application Django")
        print("   - Collecter les fichiers statiques: python manage.py collectstatic")
        print("   - Vérifier la page: /fr/competitions/dashboard/documentation/")
        print("   - Vérifier la page: /fr/competitions/federations/3/examens/")
    else:
        print("\n❌ Certaines corrections ont échoué")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())