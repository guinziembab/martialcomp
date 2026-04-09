#!/bin/bash
# =============================================================================
# DÉPLOIEMENT DU SYSTÈME DE JUGES AD-HOC
# Date: 2025-12-03
# Description: Déploie le nouveau système permettant de recruter des pratiquants
#              adultes comme juges temporaires pour les compétitions
# =============================================================================

set -e

# Configuration
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="c:/martial_hub_django/martialcomp"

echo "=========================================="
echo "DÉPLOIEMENT SYSTÈME JUGES AD-HOC"
echo "=========================================="

# 1. Transférer le nouveau modèle
echo ""
echo "[1/6] Transfert du modèle AdHocJudge..."
scp "${LOCAL_PATH}/apps/competitions/models/adhoc_judges.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/models/"

# 2. Transférer le __init__.py mis à jour des models
echo ""
echo "[2/6] Transfert du __init__.py des modèles..."
scp "${LOCAL_PATH}/apps/competitions/models/__init__.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/models/"

# 3. Transférer les vues
echo ""
echo "[3/6] Transfert des vues..."
scp "${LOCAL_PATH}/apps/competitions/views/adhoc_judges.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/"

# 4. Transférer les URLs
echo ""
echo "[4/6] Transfert des URLs..."
scp "${LOCAL_PATH}/apps/competitions/urls/adhoc_judges.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/urls/"
scp "${LOCAL_PATH}/apps/competitions/urls/__init__.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/urls/"

# 5. Transférer les templates
echo ""
echo "[5/6] Transfert des templates..."
# Créer le dossier manage s'il n'existe pas
ssh ${REMOTE_HOST} "mkdir -p ${REMOTE_PATH}/apps/competitions/templates/competitions/manage"

scp "${LOCAL_PATH}/apps/competitions/templates/competitions/manage/adhoc_judges_section.html" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/manage/"
scp "${LOCAL_PATH}/apps/competitions/templates/competitions/club/competition_management_pro.html" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/club/"
scp "${LOCAL_PATH}/apps/competitions/templates/competitions/dashboard/referee.html" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/"

# 6. Transférer la vue referee mise à jour
echo ""
echo "[6/6] Transfert de la vue referee..."
scp "${LOCAL_PATH}/apps/competitions/views/dashboard/referee.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/dashboard/"

# 7. Transférer les corrections pour l'erreur .rules -> .scoring_system
echo ""
echo "[7/9] Transfert des corrections scoring_system..."
scp "${LOCAL_PATH}/apps/competitions/views/competitions.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/"
scp "${LOCAL_PATH}/apps/competitions/views/competition_management_pro.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/"
scp "${LOCAL_PATH}/apps/competitions/templates/competitions/club/competition_management_detail.html" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/club/"
scp "${LOCAL_PATH}/apps/competitions/templates/competitions/club/competition_management_pro.html" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/club/"
scp "${LOCAL_PATH}/apps/competitions/templates/competitions/manage/adhoc_judges_section.html" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/manage/"

# 8. Transférer la vue event_organizer avec competition_public_url
echo ""
echo "[8/9] Transfert de event_organizer.py (URL publique)..."
scp "${LOCAL_PATH}/apps/competitions/views/club/event_organizer.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/club/"

# 9. Transférer les URLs mises à jour
echo ""
echo "[9/9] Transfert des URLs club..."
scp "${LOCAL_PATH}/apps/competitions/urls/club.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/urls/"

# Transférer la migration
echo ""
echo "[MIGRATION] Transfert de la migration..."
scp "${LOCAL_PATH}/apps/competitions/migrations/0014_add_adhoc_judge_model.py" \
    "${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/migrations/"

echo ""
echo "=========================================="
echo "FICHIERS TRANSFÉRÉS - EXÉCUTER SUR LE SERVEUR:"
echo "=========================================="
echo ""
echo "cd ${REMOTE_PATH}"
echo "source ../venv/bin/activate"
echo "python manage.py migrate competitions"
echo "pkill -f gunicorn"
echo "nohup /var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8888 --workers 3 --error-logfile ${REMOTE_PATH}/logs/gunicorn_error.log --access-logfile ${REMOTE_PATH}/logs/gunicorn_access.log &"
echo ""
echo "=========================================="
echo "DÉPLOIEMENT TERMINÉ"
echo "=========================================="
