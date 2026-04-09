#!/bin/bash
# =============================================================================
# Script de déploiement Super Admin en production
# Serveur: 217.154.24.122
# Dossier: /var/www/vhosts/martialcomp.com/httpdocs/
# =============================================================================

set -e

# Configuration
PROD_HOST="root@217.154.24.122"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="c:/martial_hub_django/martialcomp"

echo "=========================================="
echo "DÉPLOIEMENT SUPER ADMIN EN PRODUCTION"
echo "=========================================="
echo ""

# 1. Déployer l'application superadmin complète
echo "[1/6] Déploiement de l'application superadmin..."
scp -r apps/superadmin ${PROD_HOST}:${PROD_PATH}/apps/

# 2. Déployer les corrections des fichiers existants
echo "[2/6] Déploiement des corrections..."

# Corrections calendar
scp apps/competitions/api/calendar.py ${PROD_HOST}:${PROD_PATH}/apps/competitions/api/
scp apps/competitions/services/calendar_service.py ${PROD_HOST}:${PROD_PATH}/apps/competitions/services/

# Template base.html
scp templates/base.html ${PROD_HOST}:${PROD_PATH}/templates/

# 3. Mettre à jour les URLs principales
echo "[3/6] Mise à jour des URLs..."
scp config/urls.py ${PROD_HOST}:${PROD_PATH}/config/

# 4. Mettre à jour les settings
echo "[4/6] Mise à jour des settings..."
scp config/settings/base.py ${PROD_HOST}:${PROD_PATH}/config/settings/

# 5. Exécuter les migrations
echo "[5/6] Exécution des migrations..."
ssh ${PROD_HOST} << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py migrate superadmin --settings=config.settings.production
python manage.py collectstatic --noinput --settings=config.settings.production
ENDSSH

# 6. Redémarrer les services
echo "[6/6] Redémarrage des services..."
ssh ${PROD_HOST} << 'ENDSSH'
systemctl restart gunicorn
systemctl restart nginx
echo "Services redémarrés avec succès!"
ENDSSH

echo ""
echo "=========================================="
echo "DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "=========================================="
echo ""
echo "Vérifiez: https://martialcomp.com/superadmin/"
