#!/bin/bash
# =============================================================================
# DEPLOIEMENT GRADE TRACKING (Prompt 1 + 5) - PRODUCTION
# Date: 17 décembre 2025
# Compte SSH: martialcomp-production
# =============================================================================

# Chemin distant PRODUCTION (corrigé)
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SSH_HOST="martialcomp-production"

echo "========================================"
echo "DEPLOIEMENT GRADE TRACKING - PRODUCTION"
echo "========================================"

# -----------------------------------------------------------------------------
# 1. FICHIERS CREES (nouveaux)
# -----------------------------------------------------------------------------

echo ""
echo "[1/6] Transfert du service GradeEligibilityService..."
scp apps/competitions/services/grade_eligibility.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/services/

echo ""
echo "[2/6] Transfert des template tags..."
scp apps/grades/templatetags/grade_progress_tags.py ${SSH_HOST}:${REMOTE_PATH}/apps/grades/templatetags/

echo ""
echo "[3/6] Creation du dossier components et transfert des templates..."
ssh ${SSH_HOST} "mkdir -p ${REMOTE_PATH}/apps/competitions/templates/components"
scp apps/competitions/templates/components/grade_progress_widget.html ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/templates/components/
scp apps/competitions/templates/components/grade_progress_bar.html ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/templates/components/

echo ""
echo "[4/6] Transfert du CSS..."
scp apps/competitions/static/css/grade_progress.css ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/static/css/

echo ""
echo "[5/6] Transfert du JavaScript..."
scp apps/competitions/static/js/grade_progress.js ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/static/js/

# -----------------------------------------------------------------------------
# 2. FICHIERS MODIFIES
# -----------------------------------------------------------------------------

echo ""
echo "[6/6] Transfert des fichiers modifies..."

# Services __init__.py
scp apps/competitions/services/__init__.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/services/

# Signals grades
scp apps/grades/signals.py ${SSH_HOST}:${REMOTE_PATH}/apps/grades/

# Vue dashboard participant
scp apps/competitions/views/dashboard/participant.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/views/dashboard/

# Template dashboard participant
scp apps/competitions/templates/competitions/dashboard/participant_modern.html ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/

# URLs (correction Rosetta)
scp config/urls.py ${SSH_HOST}:${REMOTE_PATH}/config/

# -----------------------------------------------------------------------------
# 3. COMMANDES POST-DEPLOIEMENT
# -----------------------------------------------------------------------------

echo ""
echo "========================================"
echo "COMMANDES POST-DEPLOIEMENT A EXECUTER"
echo "========================================"
echo ""
echo "Connectez-vous au serveur et executez:"
echo ""
echo "  ssh ${SSH_HOST}"
echo "  cd ${REMOTE_PATH}"
echo ""
echo "  # Collecter les fichiers statiques"
echo "  python manage.py collectstatic --noinput"
echo ""
echo "  # Redemarrer le serveur"
echo "  sudo systemctl restart gunicorn"
echo "  # OU"
echo "  sudo supervisorctl restart martialcomp"
echo ""
echo "  # Vider le cache Redis (optionnel)"
echo "  redis-cli FLUSHDB"
echo ""
echo "========================================"
echo "DEPLOIEMENT TERMINE"
echo "========================================"
