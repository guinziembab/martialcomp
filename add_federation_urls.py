#!/usr/bin/env python
"""
Script pour ajouter les URLs manquantes pour le dashboard federation
"""

import shutil
from datetime import datetime

print("🔧 Ajout des URLs manquantes pour le dashboard Federation")
print("=" * 50)

# Lire le fichier original
urls_file = '/mnt/c/martial_hub_django/martialcomp/apps/competitions/urls/dashboard.py'
backup_file = f'{urls_file}.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'

try:
    # Sauvegarder
    shutil.copy2(urls_file, backup_file)
    print(f"✅ Sauvegarde créée: {backup_file}")
    
    # Lire le contenu
    with open(urls_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Trouver où insérer les nouvelles URLs (après la ligne federation_dashboard)
    federation_line = "path('federations/', federations.federation_dashboard, name='federations'),"
    
    # URLs à ajouter
    new_urls = '''    path('federations/', federations.federation_dashboard, name='federations'),
    path('federations/<int:federation_id>/', federations.federation_dashboard, name='federation_detail'),
    
    # URLs de gestion federation
    path('federations/<int:federation_id>/clubs/', federations.federation_manage_clubs, name='federation_manage_clubs'),
    path('federations/<int:federation_id>/judges/', federations.federation_manage_judges, name='federation_manage_judges'),
    path('federations/<int:federation_id>/competitions/', federations.federation_manage_competitions, name='federation_manage_competitions'),
    path('federations/<int:federation_id>/practitioners/', federations.federation_manage_practitioners, name='federation_manage_practitioners'),
    path('federations/<int:federation_id>/licenses/', federations.federation_manage_licenses, name='federation_manage_licenses'),
    path('federations/<int:federation_id>/certifications/', federations.federation_manage_certifications, name='federation_manage_certifications'),
    path('federations/<int:federation_id>/reports/', federations.federation_manage_reports, name='federation_manage_reports'),
    path('federations/<int:federation_id>/settings/', federations.federation_manage_settings, name='federation_manage_settings'),'''
    
    if federation_line in content:
        # Remplacer la ligne existante par les nouvelles URLs
        content = content.replace(federation_line, new_urls)
        print("✅ URLs federation ajoutées")
    else:
        print("⚠️  Ligne federation non trouvée, ajout à la fin des patterns")
        # Insérer avant la dernière ligne ]
        insert_pos = content.rfind(']')
        if insert_pos > 0:
            content = content[:insert_pos] + f"\n    # Dashboard fédérations\n{new_urls}\n" + content[insert_pos:]
    
    # Écrire le fichier modifié
    with open(urls_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fichier modifié: {urls_file}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    if 'backup_file' in locals():
        shutil.copy2(backup_file, urls_file)
        print("↩️  Fichier original restauré")

print("\n📝 URLs ajoutées:")
print("- federations/ (liste)")
print("- federations/<id>/ (détail)")
print("- federations/<id>/clubs/")
print("- federations/<id>/judges/")
print("- federations/<id>/competitions/")
print("- federations/<id>/practitioners/")
print("- federations/<id>/licenses/")
print("- federations/<id>/certifications/")
print("- federations/<id>/reports/")
print("- federations/<id>/settings/")