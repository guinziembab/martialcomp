#!/bin/bash

echo "🚀 Déploiement automatique de la correction FINALE de création de fédération"
echo "=========================================================================="

PACKAGE_DIR="federation_final_fix_20251015_210505"
SERVER="martialcomp-production"

echo "📤 Transfert du package vers le serveur..."
scp -r "federation_final_fix_20251015_210505" ":/tmp/"

echo "🔧 Application de la correction sur le serveur..."
ssh "" "cd /home/martialcomp/martialcomp && bash /tmp/federation_final_fix_20251015_210505/deploy_final_fix.sh"

echo "✅ Déploiement terminé !"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://directive/fr/competitions/onboarding/federation/"
