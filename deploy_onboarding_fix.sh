#!/bin/bash

echo "🚀 Déploiement automatique du fix onboarding Federation"
echo "====================================================="

PATCH_FILE="federation_onboarding_patch_20251015_174726.tar.gz"
REMOTE_HOST="martialcomp-production"

# Vérifier que le patch existe
if [ ! -f "$PATCH_FILE" ]; then
    echo "❌ Fichier patch non trouvé: $PATCH_FILE"
    exit 1
fi

echo "📤 Transfert du patch..."
scp $PATCH_FILE ${REMOTE_HOST}:/tmp/

echo ""
echo "🔧 Application du patch sur le serveur..."

ssh $REMOTE_HOST << 'REMOTE_COMMANDS'
set -e

cd /tmp
echo "📦 Extraction du patch..."
tar -xzf federation_onboarding_patch_20251015_174726.tar.gz

# Chercher le projet Django
echo "🔍 Recherche du projet..."
PROJECT_DIR=""
POSSIBLE_PATHS=(
    "/var/www/martialcomp"
    "/home/martialcomp/martialcomp"
    "/opt/martialcomp"
    "/var/www/html/martialcomp"
)

for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path/apps/competitions" ]; then
        PROJECT_DIR="$path"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Projet non trouvé!"
    exit 1
fi

echo "✅ Projet trouvé: $PROJECT_DIR"
cd $PROJECT_DIR

echo "🚀 Application du patch..."
bash /tmp/federation_onboarding_patch_20251015_174726/apply_patch.sh

# Nettoyer
rm -rf /tmp/federation_onboarding_patch_20251015_174726*

echo ""
echo "✅ Patch appliqué avec succès!"

REMOTE_COMMANDS

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "Le problème d'URL dans l'onboarding Federation est maintenant corrigé."
echo "Les utilisateurs peuvent maintenant terminer le processus d'onboarding."