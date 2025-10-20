#!/bin/bash

echo "🚀 Déploiement automatique de la correction FINALE du routage"
echo "==========================================================="

PACKAGE_DIR="federation_routing_fix_20251015_223636"
SERVER="martialcomp-production"

echo "📤 Transfert du package vers le serveur..."
scp -r "federation_routing_fix_20251015_223636" ":/tmp/"

echo "🔧 Application de la correction sur le serveur..."
ssh "" "cd /home/martialcomp/martialcomp && bash /tmp/federation_routing_fix_20251015_223636/deploy_routing_fix.sh"

echo "✅ Déploiement terminé !"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://directive/fr/competitions/onboarding/federation/"
