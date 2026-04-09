#!/bin/bash
# =============================================================================
# DEPLOY FIX ERREUR 500 - MartialComp Production
# =============================================================================
# Exécuter sur le serveur de production pour corriger l'erreur 500
# =============================================================================

set -e

APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"

echo "==========================================="
echo "CORRECTION ERREUR 500 - MartialComp"
echo "==========================================="
echo ""

# 1. Arrêter Gunicorn
echo "[1/7] Arrêt Gunicorn..."
pkill -9 -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2

# 2. Détecter la version Python
echo "[2/7] Détection version Python..."
PYTHON_VERSION=$($VENV_DIR/bin/python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PYTHON_VERSION"

# 3. Mettre à jour wsgi.py avec auto-détection version Python
echo "[3/7] Mise à jour wsgi.py..."
cp $APP_DIR/config/wsgi.py $APP_DIR/config/wsgi.py.backup_$(date +%Y%m%d_%H%M%S)

cat > $APP_DIR/config/wsgi.py << 'EOF'
"""
WSGI config for MartialComp project - Production
Version: 2025-12-20 - Auto-détection version Python
"""
import os
import sys

# =============================================================================
# CONFIGURATION ABSOLUE - AUTO-DETECTION VERSION PYTHON
# =============================================================================
PROJECT_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
VENV_DIR = '/var/www/vhosts/martialcomp.com/venv'

# Auto-détecter la version Python
PYTHON_VERSION = f'{sys.version_info.major}.{sys.version_info.minor}'
VENV_SITE_PACKAGES = f'{VENV_DIR}/lib/python{PYTHON_VERSION}/site-packages'

# =============================================================================
# AJOUTER les chemins du venv EN PREMIER
# =============================================================================
if VENV_SITE_PACKAGES not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES)

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

APPS_DIR = os.path.join(PROJECT_DIR, 'apps')
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)

# Changer le répertoire de travail
os.chdir(PROJECT_DIR)

# =============================================================================
# CHARGER LES VARIABLES D'ENVIRONNEMENT
# =============================================================================
try:
    from dotenv import load_dotenv
    env_path = os.path.join(PROJECT_DIR, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
except ImportError:
    env_path = os.path.join(PROJECT_DIR, '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# =============================================================================
# CONFIGURER DJANGO
# =============================================================================
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
EOF

echo "wsgi.py mis à jour avec auto-détection Python"

# 4. Nettoyer les caches Python
echo "[4/7] Nettoyage caches Python..."
find $APP_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $APP_DIR -name "*.pyc" -delete 2>/dev/null || true

# 5. Vider le cache Redis
echo "[5/7] Vidage cache Redis..."
redis-cli FLUSHALL 2>/dev/null || echo "Redis non disponible ou déjà vidé"

# 6. Tester l'import Django
echo "[6/7] Test import Django..."
cd $APP_DIR
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python -c "
import sys
print(f'Python: {sys.executable}')
print(f'Version: {sys.version_info.major}.{sys.version_info.minor}')

try:
    import django
    django.setup()
    print('Django setup: OK')

    from config.wsgi import application
    print('WSGI import: OK')
except Exception as e:
    print(f'ERREUR: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "ERREUR: Django ne peut pas démarrer"
    exit 1
fi

# 7. Redémarrer Gunicorn
echo "[7/7] Redémarrage Gunicorn..."
$VENV_DIR/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 2 \
    --timeout 120 \
    --chdir $APP_DIR \
    --error-logfile $APP_DIR/logs/gunicorn_error.log \
    --access-logfile $APP_DIR/logs/gunicorn_access.log \
    --capture-output \
    --daemon

sleep 3

# Vérification finale
echo ""
echo "==========================================="
echo "VÉRIFICATION FINALE"
echo "==========================================="
echo ""
echo "Processus Gunicorn:"
ps aux | grep gunicorn | grep -v grep || echo "Aucun processus Gunicorn!"

echo ""
echo "Test HTTP..."
HTTP_CODE=$(curl -sL -w "%{http_code}" -o /tmp/test_result.html \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/' 2>/dev/null)

echo "Code HTTP: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "==========================================="
    echo "SUCCÈS - Le site fonctionne!"
    echo "==========================================="
else
    echo ""
    echo "ERREUR - Code HTTP: $HTTP_CODE"
    echo ""
    echo "Contenu réponse (premiers 50 lignes):"
    head -50 /tmp/test_result.html
    echo ""
    echo "Dernières erreurs Gunicorn:"
    tail -30 $APP_DIR/logs/gunicorn_error.log
fi
