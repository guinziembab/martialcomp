#!/bin/bash
# Script pour déployer la correction du template csrf_protection.html

SSH_TARGET="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_FILE="apps/competitions/templates/competitions/includes/csrf_protection.html"
REMOTE_FILE="$REMOTE_PATH/$LOCAL_FILE"

echo "=========================================="
echo "Déploiement de la correction CSRF"
echo "=========================================="
echo ""

# Créer une sauvegarde
BACKUP_DIR="$REMOTE_PATH/backups/$(date +%Y%m%d_%H%M%S)_csrf_protection"
ssh $SSH_TARGET "mkdir -p $BACKUP_DIR && cp $REMOTE_FILE $BACKUP_DIR/ 2>/dev/null || echo 'Fichier nouveau'"
echo "✅ Sauvegarde: $BACKUP_DIR"
echo ""

# Copier le fichier
scp "$LOCAL_FILE" "$SSH_TARGET:$REMOTE_FILE"
if [ $? -eq 0 ]; then
    echo "✅ Fichier copié"
else
    echo "❌ Erreur lors de la copie"
    exit 1
fi

# Recharger
ssh $SSH_TARGET "touch $REMOTE_PATH/config/wsgi.py"
echo "✅ Application rechargée"
echo ""

echo "=========================================="
echo "✅ Déploiement terminé!"
echo "=========================================="
