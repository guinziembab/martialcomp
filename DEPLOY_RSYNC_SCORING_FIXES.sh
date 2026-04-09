#!/bin/bash
# =============================================================================
# DEPLOY VIA RSYNC - Corrections Scoring MartialComp
# Date: 2025-12-20
# =============================================================================
# À exécuter depuis la machine locale (Windows avec Git Bash ou Linux)
# =============================================================================

# Configuration
REMOTE_USER="root"
REMOTE_HOST="martialcomp.com"
REMOTE_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_DIR="."

echo "==========================================="
echo "DEPLOIEMENT VIA RSYNC"
echo "==========================================="
echo ""

# Liste des fichiers à transférer
FILES=(
    "apps/competitions/views/technical_scoring.py"
    "apps/competitions/templates/competitions/technical_scoring/scoring_history.html"
    "apps/competitions/templates/competitions/technical_scoring/categories.html"
    "apps/competitions/templatetags/custom_filters.py"
)

echo "Fichiers à transférer:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Transfert de chaque fichier
for file in "${FILES[@]}"; do
    echo "Transfert: $file"
    rsync -avz --progress "$LOCAL_DIR/$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/$file"
done

echo ""
echo "==========================================="
echo "TRANSFERT TERMINÉ"
echo "==========================================="
echo ""
echo "Maintenant, connectez-vous au serveur et exécutez:"
echo ""
echo "  ssh $REMOTE_USER@$REMOTE_HOST"
echo "  cd $REMOTE_DIR"
echo "  bash DEPLOY_SCORING_FIXES_20251220.sh"
echo ""
echo "Ou exécutez directement:"
echo ""
echo "  ssh $REMOTE_USER@$REMOTE_HOST 'cd $REMOTE_DIR && bash -s' < COMMANDES_RESTART_GUNICORN.sh"
