#!/bin/bash
# =============================================================================
# COMMANDES REDÉMARRAGE GUNICORN APRÈS DÉPLOIEMENT
# =============================================================================
# Exécuter sur le serveur de production après transfert des fichiers
# =============================================================================

APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"

echo "=== Nettoyage caches Python ==="
find $APP_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $APP_DIR -name "*.pyc" -delete 2>/dev/null || true

echo "=== Vidage cache Redis ==="
redis-cli FLUSHALL 2>/dev/null || echo "Redis non disponible"

echo "=== Test import Django ==="
cd $APP_DIR
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python -c "
import django
django.setup()
from apps.competitions.views.technical_scoring import scoring_history, scoring_categories
from apps.competitions.templatetags.custom_filters import dict_keys, get_item
print('Imports OK')
"

if [ $? -ne 0 ]; then
    echo "ERREUR: Import failed"
    exit 1
fi

echo "=== Redémarrage Gunicorn ==="
pkill -9 -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2

if [ -f "$APP_DIR/start_gunicorn.sh" ]; then
    bash $APP_DIR/start_gunicorn.sh
else
    $VENV_DIR/bin/gunicorn config.wsgi:application \
        --bind 127.0.0.1:8888 \
        --workers 2 \
        --timeout 120 \
        --chdir $APP_DIR \
        --error-logfile $APP_DIR/logs/gunicorn_error.log \
        --access-logfile $APP_DIR/logs/gunicorn_access.log \
        --capture-output \
        --daemon
fi

sleep 3

echo "=== Vérification ==="
ps aux | grep gunicorn | grep -v grep

echo ""
echo "=== Test HTTP ==="
curl -sL -w "HTTP Code: %{http_code}\n" -o /dev/null \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/'

echo ""
echo "=== TERMINÉ ==="
