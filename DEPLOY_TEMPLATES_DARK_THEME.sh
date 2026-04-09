#!/bin/bash
# Script de déploiement des templates dark/gold theme
# Exécuter depuis un environnement avec accès SSH au serveur

REMOTE_HOST="root@87.106.162.45"  # IP réelle du serveur
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement des templates Dark/Gold Theme ==="
echo ""

# 1. Backup des templates existants
echo "[1/4] Backup des templates existants..."
ssh $REMOTE_HOST "
    cd $REMOTE_PATH/apps/competitions/templates/competitions/management/
    cp schedule.html schedule.html.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'schedule.html non existant'
    cp participants.html participants.html.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'participants.html non existant'
"

# 2. Copie du template schedule.html
echo "[2/4] Copie de schedule.html..."
scp apps/competitions/templates/competitions/management/schedule.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/schedule.html

# 3. Copie du template participants.html
echo "[3/4] Copie de participants.html..."
scp apps/competitions/templates/competitions/management/participants.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/participants.html

# 4. Redémarrage du service
echo "[4/4] Redémarrage de Gunicorn..."
ssh $REMOTE_HOST "systemctl restart martialcomp || supervisorctl restart martialcomp || pkill -HUP gunicorn"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Templates déployés:"
echo "  - schedule.html (Planning des compétitions)"
echo "  - participants.html (Gestion des participants)"
echo ""
echo "URLs à tester:"
echo "  - https://martialcomp.com/fr/competitions/management/schedule/4/overview/"
echo "  - https://martialcomp.com/fr/competitions/management/4/participants/"
