#!/bin/bash

echo "=== INSTALLATION ET CONFIGURATION DE MOD_WSGI ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Installer mod_wsgi
echo "1. Installation de mod_wsgi..."
apt-get update
apt-get install -y libapache2-mod-wsgi-py3

# 2. Activer le module
echo ""
echo "2. Activation du module..."
a2enmod wsgi
a2dismod python 2>/dev/null || true  # Désactiver mod_python s'il est actif

# 3. Créer la configuration Apache pour WSGI
echo ""
echo "3. Création de la configuration Apache personnalisée..."
mkdir -p /var/www/vhosts/system/martialcomp.com/conf/
cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf << 'EOF'
# Configuration WSGI pour Django
WSGIDaemonProcess martialcomp python-home=/var/www/vhosts/martialcomp.com/venv python-path=/var/www/vhosts/martialcomp.com/httpdocs
WSGIProcessGroup martialcomp
WSGIScriptAlias / /var/www/vhosts/martialcomp.com/httpdocs/wsgi.py

<Directory /var/www/vhosts/martialcomp.com/httpdocs>
    <Files wsgi.py>
        Require all granted
    </Files>
</Directory>

# Fichiers statiques
Alias /static /var/www/vhosts/martialcomp.com/httpdocs/staticfiles
Alias /media /var/www/vhosts/martialcomp.com/httpdocs/media

<Directory /var/www/vhosts/martialcomp.com/httpdocs/staticfiles>
    Require all granted
</Directory>

<Directory /var/www/vhosts/martialcomp.com/httpdocs/media>
    Require all granted
</Directory>
EOF

# 4. Créer le fichier wsgi.py
echo ""
echo "4. Création de wsgi.py..."
cat > wsgi.py << 'EOF'
"""
WSGI config for production
"""
import os
import sys

# Ajouter le projet au path
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Charger les variables d'environnement
def load_env():
    env_path = '/var/www/vhosts/martialcomp.com/httpdocs/.env.production'
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip()

load_env()

# Définir les settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Importer l'application Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF

chown www-data:www-data wsgi.py
chmod 644 wsgi.py

# 5. Créer aussi une copie pour vhost.conf (HTTP)
echo ""
echo "5. Configuration pour HTTP..."
cp /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf /var/www/vhosts/system/martialcomp.com/conf/vhost.conf

# 6. Reconstruire la configuration Apache via Plesk
echo ""
echo "6. Mise à jour de la configuration Plesk..."
/usr/local/psa/admin/sbin/httpdmng --reconfigure-domain martialcomp.com

# 7. Redémarrer Apache
echo ""
echo "7. Redémarrage d'Apache..."
systemctl restart apache2

# 8. Test final
echo ""
echo "8. Test du site..."
sleep 3
response=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com)
echo "Code de réponse HTTP : $response"

if [ "$response" = "200" ] || [ "$response" = "301" ] || [ "$response" = "302" ]; then
    echo "✅ LE SITE FONCTIONNE !"
else
    echo "⚠️ Erreur $response - Vérification des logs..."
    tail -20 /var/log/apache2/error.log | grep -i "error\|exception"
fi

echo ""
echo "=== CONFIGURATION TERMINÉE ==="
echo ""
echo "Le site devrait maintenant fonctionner avec mod_wsgi !"
echo "URL : https://martialcomp.com"