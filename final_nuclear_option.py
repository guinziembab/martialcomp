#!/usr/bin/env python3
"""
Option NUCLÉAIRE - Supprimer complètement practitioner de l'admin
"""
import os

print("☢️  OPTION NUCLÉAIRE - SUPPRESSION COMPLÈTE PRACTITIONER")
print("=" * 60)

# Script à exécuter directement sur le serveur
nuclear_script = '''#!/usr/bin/env python3
import os
import sys
import django

# Force production settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Setup Django
django.setup()

from django.contrib import admin
from django.apps import apps

print("☢️ SUPPRESSION NUCLÉAIRE EN COURS...")

# 1. Désenregistrer TOUT ce qui contient practitioner
models_to_remove = []
for model, admin_class in list(admin.site._registry.items()):
    if 'practitioner' in model._meta.model_name.lower():
        models_to_remove.append(model)
        
for model in models_to_remove:
    try:
        admin.site.unregister(model)
        print(f"✅ Supprimé: {model._meta.label}")
    except:
        pass

# 2. Empêcher le rechargement
import apps.competitions.admin
if hasattr(apps.competitions.admin, 'practitioner'):
    delattr(apps.competitions.admin, 'practitioner')
    
# 3. Vider le cache des apps
apps.apps.clear_cache()

print("✅ Nettoyage terminé")
print("🔄 Redémarrez Apache maintenant!")
'''

# Sauvegarder le script
with open('nuclear_fix_server.py', 'w') as f:
    f.write(nuclear_script)
    
print("✅ Script créé: nuclear_fix_server.py")
print("\n📋 INSTRUCTIONS D'URGENCE:")
print("-" * 40)
print("1. Copier sur le serveur:")
print("   scp nuclear_fix_server.py root@martialcomp.com:/tmp/")
print()
print("2. Exécuter en tant que root:")
print("   cd /var/www/vhosts/martialcomp.com/httpdocs")
print("   source venv/bin/activate")
print("   python /tmp/nuclear_fix_server.py")
print()
print("3. Modifier immédiatement le fichier admin:")
print("   rm -f apps/competitions/admin/practitioner.py")
print("   echo '# DISABLED' > apps/competitions/admin/practitioner.py")
print()
print("4. Redémarrer Apache:")
print("   systemctl restart apache2")
print()
print("⚠️  CECI EST UNE MESURE D'URGENCE!")
print("   Une refonte complète du module practitioner est nécessaire.")