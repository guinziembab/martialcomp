#!/bin/bash
# Script de déploiement rapide pour le template import_export.html corrigé

SSH_TARGET="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_FILE="apps/competitions/templates/competitions/club/import_export.html"
REMOTE_FILE="$REMOTE_PATH/$LOCAL_FILE"

echo "=========================================="
echo "Déploiement du template import_export.html"
echo "=========================================="
echo ""

# Vérifier que le fichier existe
if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ ERREUR: Le fichier $LOCAL_FILE n'existe pas"
    exit 1
fi

# Créer une sauvegarde
echo "📦 Création d'une sauvegarde..."
BACKUP_DIR="$REMOTE_PATH/backups/$(date +%Y%m%d_%H%M%S)_template_import_export"
ssh $SSH_TARGET "mkdir -p $BACKUP_DIR && cp $REMOTE_FILE $BACKUP_DIR/ 2>/dev/null || echo 'Fichier nouveau ou non existant'"
echo "✅ Sauvegarde créée dans: $BACKUP_DIR"
echo ""

# Copier le fichier
echo "📤 Copie du fichier vers la production..."
scp "$LOCAL_FILE" "$SSH_TARGET:$REMOTE_FILE"
if [ $? -eq 0 ]; then
    echo "✅ Fichier copié avec succès"
else
    echo "❌ ERREUR lors de la copie"
    exit 1
fi

# Toucher wsgi.py pour rechargement
echo ""
echo "🔄 Rechargement de l'application..."
ssh $SSH_TARGET "touch $REMOTE_PATH/config/wsgi.py"
echo "✅ Rechargement déclenché"
echo ""

echo "=========================================="
echo "✅ Déploiement terminé!"
echo "=========================================="
echo ""
echo "Testez maintenant:"
echo "  https://martialcomp.com/fr/competitions/club/import-export/"
echo ""
