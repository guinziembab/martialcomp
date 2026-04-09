#!/bin/bash
# Script de déploiement complet pour corriger l'import/export et les APIs
# Date: 2024-11-21

# Configuration
PRODUCTION_SERVER="ftp_martialcomp@94.130.130.68"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"

echo "=================================================="
echo "  DÉPLOIEMENT IMPORT/EXPORT ET APIs - Production"
echo "=================================================="

# 1. Copier les fichiers nécessaires
echo ""
echo "[1/5] Copie des fichiers vers le serveur..."

# Copier registration_api.py (contient available_competitions_api et bulk_registration_process)
echo "  - Copie de registration_api.py..."
scp -o StrictHostKeyChecking=no "${LOCAL_PATH}/apps/competitions/views/club/registration_api.py" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/views/club/registration_api.py"

# Copier import_export.py
echo "  - Copie de import_export.py..."
scp -o StrictHostKeyChecking=no "${LOCAL_PATH}/apps/competitions/views/club/import_export.py" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/views/club/import_export.py"

# Copier club.py (URLs)
echo "  - Copie de club.py (URLs)..."
scp -o StrictHostKeyChecking=no "${LOCAL_PATH}/apps/competitions/urls/club.py" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/urls/club.py"

# Copier le template import_export.html
echo "  - Copie de import_export.html..."
scp -o StrictHostKeyChecking=no "${LOCAL_PATH}/apps/competitions/templates/competitions/club/import_export.html" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/templates/competitions/club/import_export.html"

# 2. Vérifier les imports Python
echo ""
echo "[2/5] Vérification des imports Python sur le serveur..."
ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "cd ${PRODUCTION_PATH} && /var/www/vhosts/martialcomp.com/venv/bin/python -c '
from apps.competitions.views.club.registration_api import (
    get_categories_by_type_api, competition_registration_simple, unregister_practitioner,
    available_competitions_api, bulk_registration_process
)
from apps.competitions.views.club.import_export import import_export_data, download_import_template, export_practitioners
print(\"OK - Tous les imports sont valides\")
' 2>&1"

# 3. Collecter les fichiers statiques
echo ""
echo "[3/5] Collecte des fichiers statiques..."
ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "cd ${PRODUCTION_PATH} && \
    export DJANGO_SETTINGS_MODULE=config.settings && \
    export DJANGO_ENV=production && \
    /var/www/vhosts/martialcomp.com/venv/bin/python manage.py collectstatic --noinput 2>&1 | tail -5"

# 4. Redémarrer Gunicorn
echo ""
echo "[4/5] Redémarrage de Gunicorn..."
ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "pkill -f gunicorn; sleep 2"

ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "cd ${PRODUCTION_PATH} && \
    export DJANGO_ENV=production && \
    export DJANGO_SETTINGS_MODULE=config.settings && \
    export DB_NAME=martialcomp_db && \
    export DB_USER=martialcomp_user && \
    export DB_PASSWORD='AQWZSX123ok,' && \
    export DB_HOST=localhost && \
    export DB_PORT=5432 && \
    /var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
        --workers 3 \
        --bind 127.0.0.1:8888 \
        --daemon \
        --access-logfile logs/gunicorn_access.log \
        --error-logfile logs/gunicorn_error.log \
        --log-level info \
        config.wsgi:application"

sleep 3

# 5. Vérification finale
echo ""
echo "[5/5] Vérification du déploiement..."

# Compter les processus Gunicorn
GUNICORN_COUNT=$(ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "ps aux | grep gunicorn | grep -v grep | wc -l")
echo "  - Processus Gunicorn actifs: ${GUNICORN_COUNT}"

# Tester le site
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/")
echo "  - Code HTTP de la page d'accueil: ${HTTP_CODE}"

# Tester la page import/export
HTTP_CODE_IMPORT=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/club/import-export/")
echo "  - Code HTTP de import/export: ${HTTP_CODE_IMPORT}"

# Tester l'API available-competitions
HTTP_CODE_API=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/club/available-competitions/api/")
echo "  - Code HTTP de l'API available-competitions: ${HTTP_CODE_API}"

echo ""
echo "=================================================="
if [ "${HTTP_CODE}" = "200" ] || [ "${HTTP_CODE}" = "302" ]; then
    echo "  DÉPLOIEMENT RÉUSSI!"
else
    echo "  ATTENTION: Vérifier les logs d'erreur"
    echo "  ssh ${PRODUCTION_SERVER} 'tail -50 ${PRODUCTION_PATH}/logs/gunicorn_error.log'"
fi
echo "=================================================="
