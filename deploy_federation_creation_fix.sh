#!/bin/bash

echo "🚀 Déploiement automatique de la correction de création de fédération"
echo "===================================================================="

PACKAGE_DIR="federation_creation_fix_20251015_184730"
SERVER="martialcomp-production"

echo "📤 Transfert du package vers le serveur..."
scp -r "federation_creation_fix_20251015_184730" ":/tmp/"

echo "🔧 Application de la correction sur le serveur..."
ssh "" "cd /home/martialcomp/martialcomp && bash /tmp/federation_creation_fix_20251015_184730/deploy_fix.sh"

echo "✅ Déploiement terminé !"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://directive/fr/competitions/onboarding/federation/"
