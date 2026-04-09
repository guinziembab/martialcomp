#!/bin/bash
# Script de déploiement - Correction statistiques mobile
# Date: 2026-01-23

# Configuration
REMOTE_USER="root"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/martialcomp"

echo "=== Déploiement des corrections statistiques mobile ==="
echo ""

# Option 1: Déploiement via rsync (recommandé)
echo "1. Copie des fichiers modifiés..."
rsync -avz --progress \
    api/views.py \
    api_auth/views.py \
    ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

# Option 2: Alternative via scp
# scp api/views.py api_auth/views.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

echo ""
echo "2. Redémarrage du serveur Gunicorn..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "cd ${REMOTE_PATH} && sudo systemctl restart gunicorn"

echo ""
echo "3. Vérification du statut..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "sudo systemctl status gunicorn --no-pager | head -15"

echo ""
echo "=== Déploiement terminé ==="
echo "Testez l'application mobile pour vérifier que les statistiques s'affichent."
