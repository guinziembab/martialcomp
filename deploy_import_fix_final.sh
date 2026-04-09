#!/bin/bash
# Script de déploiement - Import Fix Final
# Date: 2024-11-22

set -e

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"

echo "=================================================="
echo "  DÉPLOIEMENT IMPORT FIX - DEBUG VERSION"
echo "=================================================="

# 1. Copier import_export.py avec debug
echo ""
echo "[1/4] Copie de import_export.py avec debug prints..."
scp "${LOCAL_PATH}/apps/competitions/views/club/import_export.py" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/views/club/import_export.py"

# 2. Copier registration_api.py pour fixer le NameError
echo ""
echo "[2/4] Copie de registration_api.py..."
scp "${LOCAL_PATH}/apps/competitions/views/club/registration_api.py" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/views/club/registration_api.py"

# 3. Nettoyer cache Python et redémarrer
echo ""
echo "[3/4] Nettoyage du cache Python..."
ssh "${PRODUCTION_SERVER}" "find ${PRODUCTION_PATH} -name '*.pyc' -delete 2>/dev/null; find ${PRODUCTION_PATH} -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true; echo 'Cache nettoyé'"

# 4. Redémarrer Gunicorn
echo ""
echo "[4/4] Redémarrage de Gunicorn..."
ssh "${PRODUCTION_SERVER}" "pkill -9 -f gunicorn 2>/dev/null || true; sleep 2; fuser -k 8888/tcp 2>/dev/null || true; sleep 1"

ssh "${PRODUCTION_SERVER}" "cd ${PRODUCTION_PATH} && \
    export DJANGO_ENV=production && \
    export DJANGO_SETTINGS_MODULE=config.settings.production && \
    export DB_NAME=martialcomp_db && \
    export DB_USER=martialcomp_user && \
    export DB_PASSWORD='AQWZSX123ok,' && \
    export DB_HOST=localhost && \
    export DB_PORT=5432 && \
    /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
        --workers 3 \
        --bind 127.0.0.1:8888 \
        --daemon \
        --access-logfile ${PRODUCTION_PATH}/logs/gunicorn_access.log \
        --error-logfile ${PRODUCTION_PATH}/logs/gunicorn_error.log \
        --log-level debug \
        --capture-output \
        config.wsgi:application"

sleep 3

# Vérifier que Gunicorn est bien lancé
echo ""
echo "Vérification de Gunicorn..."
ssh "${PRODUCTION_SERVER}" "pgrep -c -f gunicorn && echo 'Gunicorn OK' || echo 'Gunicorn FAIL'"

echo ""
echo "=================================================="
echo "  DÉPLOIEMENT TERMINÉ"
echo "=================================================="
echo ""
echo "Pour tester:"
echo "1. Allez sur https://martialcomp.com/fr/competitions/club/import-export/"
echo "2. Uploadez votre fichier Excel"
echo "3. Cliquez sur 'Importer les données'"
echo ""
echo "Puis vérifiez les logs:"
echo "ssh ${PRODUCTION_SERVER} 'tail -50 ${PRODUCTION_PATH}/logs/gunicorn_error.log'"
echo ""
