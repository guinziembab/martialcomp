#!/usr/bin/env python
"""Script pour ajouter les URLs de gestion des types"""

import re

print("=== Ajout des URLs pour la gestion des types ===\n")

urls_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls.py'

with open(urls_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(urls_file + '.backup_types_urls', 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✓ Backup créé: {urls_file}.backup_types_urls")

# Vérifier si les URLs existent déjà
if 'api_create_competition_type' in content:
    print("ℹ️  Les URLs existent déjà")
else:
    # Chercher où ajouter les URLs - après les autres patterns
    # Chercher la fin du urlpatterns
    pattern = r'(urlpatterns\s*=\s*\[[^\]]*)(])'
    
    urls_to_add = '''
    # API pour la gestion des types de compétitions
    path('api/competition/<int:competition_id>/create-type/', 
         views.api.create_competition_type, 
         name='api_create_competition_type'),
    path('api/competition/<int:competition_id>/remove-type/<int:type_id>/', 
         views.api.remove_competition_type, 
         name='api_remove_competition_type'),
'''
    
    # Ajouter avant la fermeture de urlpatterns
    def add_urls(match):
        return match.group(1) + urls_to_add + '\n' + match.group(2)
    
    new_content = re.sub(pattern, add_urls, content, flags=re.DOTALL)
    
    if new_content != content:
        # Vérifier que views.api est importé
        if 'from . import api' not in new_content and 'from .views import api' not in new_content:
            # Ajouter l'import
            import_line = 'from . import views\n'
            if import_line in new_content:
                new_content = new_content.replace(import_line, import_line + 'from .views import api\n')
            else:
                # Ajouter après les autres imports
                new_content = re.sub(
                    r'(from django\.urls import.*?\n)',
                    r'\1from .views import api\n',
                    new_content,
                    count=1
                )
        
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✓ URLs ajoutées avec succès")
    else:
        print("❌ Impossible d'ajouter les URLs automatiquement")
        print("Veuillez les ajouter manuellement")

print("\n✅ Configuration terminée!")