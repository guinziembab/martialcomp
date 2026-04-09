#!/bin/bash

# Script de déploiement de la correction JS pour club.html
# Corrige l'erreur "Invalid or unexpected token" à la ligne 3480

echo "=== DÉPLOIEMENT CORRECTION JS CLUB.HTML ==="
echo "Date: $(date)"

# Configuration
LOCAL_FILE="/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/club.html"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/"
REMOTE_FILE="club.html"
SSH_HOST="martialcomp-production"

echo "1. Vérification du fichier local..."
if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ Erreur: Fichier local non trouvé: $LOCAL_FILE"
    exit 1
fi

echo "2. Création d'une sauvegarde sur le serveur distant..."
ssh $SSH_HOST "cd $REMOTE_PATH && cp $REMOTE_FILE $REMOTE_FILE.backup_js_fix_$(date +%Y%m%d_%H%M%S)"

echo "3. Copie du fichier corrigé..."
scp "$LOCAL_FILE" "$SSH_HOST:$REMOTE_PATH$REMOTE_FILE"

echo "4. Vérification de la copie..."
ssh $SSH_HOST "ls -la $REMOTE_PATH$REMOTE_FILE"

echo "5. Redémarrage des services si nécessaire..."
# Normalement pas nécessaire pour un changement de template, mais au cas où
ssh $SSH_HOST "sudo systemctl reload nginx || true"

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "ACTIONS À EFFECTUER :"
echo "1. Ouvrir https://martialcomp.com/fr/competitions/dashboard/club/#"
echo "2. Vider le cache du navigateur (Ctrl+Shift+Delete)"
echo "3. Recharger la page (Ctrl+F5)"
echo "4. Ouvrir la console (F12) et vérifier qu'il n'y a plus d'erreur JavaScript"
echo "5. Tester le bouton 'S'inscrire' dans l'onglet Compétitions"
echo ""
echo "Si le problème persiste:"
echo "- Vérifier la console pour d'autres erreurs"
echo "- Restaurer la sauvegarde avec: ssh $SSH_HOST 'cd $REMOTE_PATH && cp $REMOTE_FILE.backup_js_fix_* $REMOTE_FILE'"