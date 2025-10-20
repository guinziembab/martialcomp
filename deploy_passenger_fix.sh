#!/bin/bash

# Script de déploiement du fix passenger_wsgi.py
# Ce script doit être exécuté sur le serveur de production

echo "=== Déploiement du fix passenger_wsgi.py ==="

# Chemin de destination sur le serveur
DEST_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Créer une sauvegarde du fichier actuel si il existe
if [ -f "$DEST_PATH/passenger_wsgi.py" ]; then
    echo "Sauvegarde du fichier existant..."
    cp "$DEST_PATH/passenger_wsgi.py" "$DEST_PATH/passenger_wsgi.py.backup_$(date +%Y%m%d_%H%M%S)"
fi

# Créer le nouveau fichier passenger_wsgi.py
cat > "$DEST_PATH/passenger_wsgi.py" << 'EOF'
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
EOF

echo "Fichier passenger_wsgi.py créé/mis à jour."

# Définir les bonnes permissions
chown www-data:www-data "$DEST_PATH/passenger_wsgi.py"
chmod 644 "$DEST_PATH/passenger_wsgi.py"

echo "Permissions définies."

# Redémarrer Apache
echo "Redémarrage d'Apache..."
systemctl restart apache2

# Vérifier le statut
systemctl status apache2 --no-pager | head -20

echo "=== Déploiement terminé ==="
echo ""
echo "Pour vérifier les logs:"
echo "tail -f /var/log/apache2/error.log"
echo "tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log"