import sys
import os

# Ajouter le chemin du projet au path Python
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Charger manuellement les variables d'environnement depuis .env.production
env_path = '/var/www/vhosts/martialcomp.com/httpdocs/.env.production'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Définir explicitement le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Importer l'application WSGI Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# CORRECTION DE L'ERREUR DISCIPLINE - IMPORT DU SCRIPT DE CORRECTION
try:
    import wsgi_startup_fix
    print("✅ Script de correction Discipline importé avec succès")
except Exception as e:
    print(f"⚠️ Erreur import script de correction: {e}")