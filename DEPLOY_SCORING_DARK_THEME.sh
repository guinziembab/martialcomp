#!/bin/bash
# Script de déploiement des templates Scoring Dark/Gold Theme + URLs corrigées
# Exécuter depuis un environnement avec accès SSH au serveur

REMOTE_HOST="root@87.106.162.45"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement Scoring Dark/Gold Theme ==="
echo ""

# 1. Backup des fichiers existants
echo "[1/4] Backup des fichiers existants..."
ssh $REMOTE_HOST "
    cd $REMOTE_PATH/apps/competitions/templates/competitions/management/
    cp scoring_dashboard.html scoring_dashboard.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'scoring_dashboard.html non existant'

    cd $REMOTE_PATH/apps/competitions/urls/
    cp management.py management.py.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null
"

# 2. Copie des templates
echo "[2/4] Copie des templates..."
scp apps/competitions/templates/competitions/management/scoring_dashboard.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/scoring_dashboard.html

scp apps/competitions/templates/competitions/management/judges.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/judges.html

# 3. Copie des URLs corrigées
echo "[3/4] Copie des URLs corrigées..."
scp apps/competitions/urls/management.py \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/urls/management.py

# 4. Redémarrage du service
echo "[4/4] Redémarrage de Gunicorn..."
ssh $REMOTE_HOST "systemctl restart martialcomp || supervisorctl restart martialcomp || pkill -HUP gunicorn"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Fichiers déployés:"
echo "  - scoring_dashboard.html (Dark/Gold Theme)"
echo "  - judges.html (Dark/Gold Theme - corrigé JS)"
echo "  - management.py (URLs scoring corrigées)"
echo ""
echo "URLs à tester:"
echo "  - https://martialcomp.com/fr/competitions/management/scoring/4/"
echo "  - https://martialcomp.com/fr/competitions/management/scoring/4/category/33/setup/"
echo "  - https://martialcomp.com/fr/competitions/management/scoring/4/category/33/performances/"
echo "  - https://martialcomp.com/fr/competitions/management/scoring/4/category/33/results/"
echo "  - https://martialcomp.com/fr/competitions/management/4/judges/"
