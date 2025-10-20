#!/bin/bash

echo "🚀 Déploiement automatique de la correction du RÔLE"
echo "=================================================="

PACKAGE_DIR="federation_role_fix_20251015_220313"
SERVER="martialcomp-production"

echo "📤 Transfert du package vers le serveur..."
scp -r "federation_role_fix_20251015_220313" ":/tmp/"

echo "🔧 Application de la correction sur le serveur..."
ssh "" "cd /home/martialcomp/martialcomp && bash /tmp/federation_role_fix_20251015_220313/deploy_role_fix.sh"

echo "✅ Déploiement terminé !"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://directive/fr/competitions/onboarding/federation/"
