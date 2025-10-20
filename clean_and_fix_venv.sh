#!/bin/bash

echo "=== NETTOYAGE ET CONFIGURATION DES ENVIRONNEMENTS VIRTUELS ==="
echo ""

# 1. D'abord, sortir de tout environnement virtuel actif
echo "1. Désactivation de tout environnement virtuel actif..."
deactivate 2>/dev/null || true

# Réinitialiser le PATH pour être sûr
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# 2. Lister tous les environnements virtuels trouvés
echo ""
echo "2. Environnements virtuels trouvés :"
echo "-----------------------------------"
find /var/www/vhosts/martialcomp.com -name "pyvenv.cfg" -type f 2>/dev/null | while read cfg; do
    venv_dir=$(dirname "$cfg")
    echo "- $venv_dir"
    if [ -f "$venv_dir/bin/python" ]; then
        echo "  Python: $($venv_dir/bin/python --version 2>&1)"
    fi
done

# 3. Supprimer l'environnement virtuel dans httpdocs
echo ""
echo "3. Suppression de l'environnement virtuel dans httpdocs..."
if [ -d "/var/www/vhosts/martialcomp.com/httpdocs/venv" ]; then
    rm -rf /var/www/vhosts/martialcomp.com/httpdocs/venv
    echo "✓ Environnement virtuel supprimé de httpdocs"
else
    echo "✓ Aucun environnement virtuel dans httpdocs"
fi

# 4. Vérifier/recréer l'environnement virtuel principal
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"
echo ""
echo "4. Configuration de l'environnement virtuel principal..."

if [ -d "$VENV_PATH" ]; then
    echo "Environnement virtuel existant trouvé. Vérification..."
    if [ ! -f "$VENV_PATH/bin/python" ]; then
        echo "⚠️ L'environnement virtuel est corrompu. Recréation..."
        rm -rf $VENV_PATH
        python3 -m venv $VENV_PATH
    fi
else
    echo "Création d'un nouvel environnement virtuel..."
    python3 -m venv $VENV_PATH
fi

# 5. Activer et configurer l'environnement virtuel
echo ""
echo "5. Activation et configuration de l'environnement virtuel..."
cd /var/www/vhosts/martialcomp.com/httpdocs

# Utiliser le chemin complet pour pip et python
VENV_PYTHON="$VENV_PATH/bin/python"
VENV_PIP="$VENV_PATH/bin/pip"

echo "Python utilisé : $VENV_PYTHON"
$VENV_PYTHON --version

# Mettre à jour pip
echo ""
echo "Mise à jour de pip..."
$VENV_PYTHON -m pip install --upgrade pip

# 6. Installer les dépendances
echo ""
echo "6. Installation des dépendances..."

# Dépendances essentielles
$VENV_PIP install django==4.2.11
$VENV_PIP install psycopg2-binary
$VENV_PIP install python-decouple
$VENV_PIP install pillow
$VENV_PIP install django-cors-headers
$VENV_PIP install djangorestframework
$VENV_PIP install gunicorn

# Si requirements.txt existe
if [ -f "requirements.txt" ]; then
    echo "Installation depuis requirements.txt..."
    $VENV_PIP install -r requirements.txt
fi

# 7. Vérifier l'installation
echo ""
echo "7. Vérification de l'installation..."
$VENV_PYTHON -c "import django; print(f'✓ Django {django.get_version()} installé')"
$VENV_PYTHON -c "import psycopg2; print('✓ psycopg2 installé')"

# 8. Mettre à jour passenger_wsgi.py
echo ""
echo "8. Mise à jour de passenger_wsgi.py..."
cat > passenger_wsgi.py << 'EOF'
import sys
import os

# Chemin vers l'environnement virtuel
VENV_PATH = '/var/www/vhosts/martialcomp.com/venv'

# Utiliser le Python de l'environnement virtuel
python_bin = os.path.join(VENV_PATH, 'bin', 'python')
if os.path.exists(python_bin):
    # Ajouter le site-packages au path
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = os.path.join(VENV_PATH, 'lib', f'python{python_version}', 'site-packages')
    if os.path.exists(site_packages):
        sys.path.insert(0, site_packages)

# Ajouter le chemin du projet
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

# Charger les variables d'environnement
env_path = '/var/www/vhosts/martialcomp.com/httpdocs/.env.production'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# Définir le module de settings Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Importer l'application WSGI Django
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    print("✓ Application Django chargée avec succès")
except Exception as e:
    print(f"✗ Erreur lors du chargement de Django: {e}")
    import traceback
    traceback.print_exc()
    raise
EOF

chown www-data:www-data passenger_wsgi.py
chmod 644 passenger_wsgi.py

# 9. Tester les migrations
echo ""
echo "9. Test de la connexion à la base de données..."
$VENV_PYTHON manage.py migrate --settings=config.settings.production --check

# 10. Redémarrer Apache
echo ""
echo "10. Redémarrage d'Apache..."
systemctl restart apache2
sleep 2

# 11. Vérifier les erreurs
echo ""
echo "11. Vérification finale..."
echo "Statut Apache:"
systemctl status apache2 --no-pager | head -5

echo ""
echo "Dernières erreurs dans les logs:"
tail -10 /var/log/apache2/error.log | grep -E "(Error|ERROR|Exception)" || echo "Aucune erreur récente trouvée"

echo ""
echo "=== CONFIGURATION TERMINÉE ==="
echo ""
echo "L'environnement virtuel est maintenant à : $VENV_PATH"
echo "Pour l'utiliser manuellement : source $VENV_PATH/bin/activate"
echo ""
echo "Testez le site : curl -I https://martialcomp.com"