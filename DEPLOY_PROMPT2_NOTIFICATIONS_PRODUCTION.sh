#!/bin/bash
# =============================================================================
# DEPLOIEMENT PROMPT 2 - NOTIFICATIONS DE GRADE (PRODUCTION)
# Date: 17 decembre 2025
# =============================================================================

REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SSH_HOST="martialcomp-production"

echo "========================================"
echo "DEPLOIEMENT PROMPT 2 - NOTIFICATIONS"
echo "========================================"

# -----------------------------------------------------------------------------
# 1. FICHIERS CREES (nouveaux)
# -----------------------------------------------------------------------------

echo ""
echo "[1/5] Creation du dossier tasks et transfert des fichiers..."
ssh ${SSH_HOST} "mkdir -p ${REMOTE_PATH}/apps/competitions/tasks"
scp apps/competitions/tasks/__init__.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/tasks/
scp apps/competitions/tasks/grade_notifications.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/tasks/

echo ""
echo "[2/5] Transfert des templates email..."
ssh ${SSH_HOST} "mkdir -p ${REMOTE_PATH}/templates/emails/txt"
scp templates/emails/html/grade_eligibility.html ${SSH_HOST}:${REMOTE_PATH}/templates/emails/html/
scp templates/emails/txt/grade_eligibility.txt ${SSH_HOST}:${REMOTE_PATH}/templates/emails/txt/

# -----------------------------------------------------------------------------
# 2. FICHIERS MODIFIES
# -----------------------------------------------------------------------------

echo ""
echo "[3/5] Transfert des fichiers modifies..."

# Configuration Celery avec nouveaux beat_schedule
scp config/celery.py ${SSH_HOST}:${REMOTE_PATH}/config/

# Signals avec notifications
scp apps/grades/signals.py ${SSH_HOST}:${REMOTE_PATH}/apps/grades/

echo ""
echo "[4/5] Transfert des corrections grade_eligibility..."
scp apps/competitions/services/grade_eligibility.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/services/

# -----------------------------------------------------------------------------
# 3. REDEMARRAGE SERVICES
# -----------------------------------------------------------------------------

echo ""
echo "[5/5] Redemarrage des services..."

# Redemarrer gunicorn
ssh ${SSH_HOST} "kill -HUP \$(pgrep -f 'gunicorn.*config.wsgi')"

# Redemarrer Celery worker et beat si configure
# ssh ${SSH_HOST} "sudo systemctl restart celery-worker celery-beat"

echo ""
echo "========================================"
echo "DEPLOIEMENT TERMINE"
echo "========================================"
echo ""
echo "IMPORTANT: Verifier que Celery est configure sur le serveur."
echo "Si Celery n'est pas encore configure, executez:"
echo ""
echo "  # Sur le serveur:"
echo "  pip install celery redis"
echo ""
echo "  # Demarrer le worker:"
echo "  cd ${REMOTE_PATH}"
echo "  celery -A config worker -l info --detach"
echo ""
echo "  # Demarrer le beat (planificateur):"
echo "  celery -A config beat -l info --detach"
echo ""
