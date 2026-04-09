#!/usr/bin/env python
"""Script pour ajouter les URLs API dans competition_types.py"""

print("=== Mise à jour des URLs pour la gestion des types ===\n")

urls_file = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/competition_types.py'

with open(urls_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(urls_file + '.backup_api', 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✓ Backup créé")

# Ajouter l'import de la vue api
if 'from apps.competitions.views import api' not in content:
    # Ajouter après les autres imports
    content = content.replace(
        'from apps.competitions.views.competition_types import (',
        'from apps.competitions.views import api\nfrom apps.competitions.views.competition_types import ('
    )
    print("✓ Import api ajouté")

# Ajouter les nouvelles URLs si elles n'existent pas
if 'api/competition/' not in content:
    # Chercher la fin du urlpatterns
    urls_to_add = '''    
    # API pour la gestion des types dans une compétition
    path('api/competition/<int:competition_id>/create-type/', 
         api.create_competition_type, 
         name='api_create_type_for_competition'),
    path('api/competition/<int:competition_id>/remove-type/<int:type_id>/', 
         api.remove_competition_type, 
         name='api_remove_type_from_competition'),
'''
    
    # Ajouter avant la dernière fermeture ]
    content = content.rstrip()
    if content.endswith(']'):
        content = content[:-1] + urls_to_add + '\n]'
        print("✓ URLs API ajoutées")

with open(urls_file, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ URLs mises à jour avec succès!")

# Maintenant vérifier le fichier principal des URLs competitions
main_urls = '/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/__init__.py'
print(f"\n📝 Vérification du fichier principal: {main_urls}")

try:
    with open(main_urls, 'r', encoding='utf-8') as f:
        main_content = f.read()
    
    if 'competition-types/' in main_content:
        print("✓ Les URLs competition-types sont déjà incluses")
    else:
        print("⚠️  Il faut vérifier que les URLs competition-types sont bien incluses dans le fichier principal")
except Exception as e:
    print(f"❌ Erreur: {e}")