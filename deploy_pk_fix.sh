#!/bin/bash

echo "=== DÉPLOIEMENT CORRECTION URL PK -> COMPETITION_ID ==="
echo "Date: $(date)"

# Configuration
LOCAL_FILE="/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/competitions.py"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/"

echo "1. Copie du fichier corrigé..."
scp "$LOCAL_FILE" "martialcomp-production:$REMOTE_PATH/competitions.py"

echo "2. Redémarrage nginx..."
ssh martialcomp-production "sudo systemctl reload nginx"

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ !"
echo ""
echo "Correction appliquée : pk=pk → competition_id=pk"
echo ""
echo "Testez : https://martialcomp.com/fr/competitions/competitions/4/"