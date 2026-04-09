#!/bin/bash
# Script de déploiement pour corriger l'import avec debug
# Date: 2024-11-21

# Configuration
PRODUCTION_SERVER="ftp_martialcomp@94.130.130.68"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"

echo "=================================================="
echo "  DÉPLOIEMENT CORRECTION IMPORT - Debug"
echo "=================================================="

# 1. Copier import_export.py avec debug logging
echo ""
echo "[1/4] Copie de import_export.py..."
scp -o StrictHostKeyChecking=no "${LOCAL_PATH}/apps/competitions/views/club/import_export.py" \
    "${PRODUCTION_SERVER}:${PRODUCTION_PATH}/apps/competitions/views/club/import_export.py"

# 2. Vider le cache Python
echo ""
echo "[2/4] Nettoyage du cache Python..."
ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "find ${PRODUCTION_PATH} -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null; find ${PRODUCTION_PATH} -name '*.pyc' -delete 2>/dev/null; echo 'Cache vidé'"

# 3. Redémarrer Gunicorn
echo ""
echo "[3/4] Redémarrage de Gunicorn..."
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
        --capture-output \
        config.wsgi:application"

sleep 3

# 4. Configurer Django logging vers gunicorn
echo ""
echo "[4/4] Configuration du logging Django..."
ssh -o StrictHostKeyChecking=no "${PRODUCTION_SERVER}" "cd ${PRODUCTION_PATH} && \
    cat > /tmp/test_logging.py << 'EOFPY'
import sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
import logging
logger = logging.getLogger('apps.competitions.views.club.import_export')
print(f'Logger handlers: {logger.handlers}')
print(f'Logger level: {logger.level}')
print(f'Logger effective level: {logger.getEffectiveLevel()}')
EOFPY
/var/www/vhosts/martialcomp.com/venv/bin/python /tmp/test_logging.py 2>&1"

echo ""
echo "=================================================="
echo "  DÉPLOIEMENT TERMINÉ"
echo "=================================================="
echo ""
echo "Pour tester l'import:"
echo "1. Allez sur https://martialcomp.com/fr/competitions/club/import-export/"
echo "2. Uploadez un fichier Excel"
echo "3. Cliquez sur 'Importer les données'"
echo ""
echo "Puis vérifiez les logs:"
echo "ssh ${PRODUCTION_SERVER} 'tail -100 ${PRODUCTION_PATH}/logs/gunicorn_error.log | grep -i import'"
echo ""
