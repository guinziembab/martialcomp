#!/bin/bash
# Script de déploiement des corrections d'authentification
# Date: 2026-01-12
#
# Corrections appliquées:
# 1. API d'inscription (RegisterView) - Validation améliorée
# 2. Endpoint de changement de mot de passe (PasswordChangeView)
# 3. Endpoint de réinitialisation de mot de passe (PasswordResetRequestView, PasswordResetConfirmView)
# 4. HomeScreen mobile aligné avec dashboard backend participant

set -e

echo "=========================================="
echo "Déploiement des corrections d'authentification"
echo "Date: $(date)"
echo "=========================================="

# Variables
PROD_HOST="martialcomp-production"
PROD_PATH="/var/www/martialcomp"
LOCAL_PATH="c:/martial_hub_django/martialcomp"

# Fichiers à déployer (API auth)
API_AUTH_FILES=(
    "api_auth/serializers.py"
    "api_auth/urls.py"
    "api_auth/views.py"
)

# Fichier mobile (HomeScreen)
MOBILE_FILES=(
    "mobile/src/screens/main/HomeScreen.tsx"
)

echo ""
echo "=== Étape 1: Sauvegarde des fichiers sur le serveur ==="
ssh $PROD_HOST "cd $PROD_PATH && \
    mkdir -p backups/$(date +%Y%m%d_%H%M%S) && \
    cp -r api_auth/ backups/$(date +%Y%m%d_%H%M%S)/"

echo ""
echo "=== Étape 2: Transfert des fichiers API auth ==="
for file in "${API_AUTH_FILES[@]}"; do
    echo "Transfert de $file..."
    scp "$LOCAL_PATH/$file" "$PROD_HOST:$PROD_PATH/$file"
done

echo ""
echo "=== Étape 3: Redémarrage du serveur Django ==="
ssh $PROD_HOST "cd $PROD_PATH && \
    source venv/bin/activate && \
    sudo systemctl restart gunicorn"

echo ""
echo "=== Étape 4: Vérification du service ==="
ssh $PROD_HOST "sudo systemctl status gunicorn --no-pager | head -20"

echo ""
echo "=========================================="
echo "Déploiement terminé avec succès!"
echo "=========================================="
echo ""
echo "Endpoints disponibles:"
echo "- POST /api/v1/auth/register/ - Inscription"
echo "- POST /api/v1/auth/password-change/ - Changement de mot de passe"
echo "- POST /api/v1/auth/password-reset/ - Demande de réinitialisation"
echo "- POST /api/v1/auth/password-reset-confirm/ - Confirmation de réinitialisation"
echo ""
echo "Pour tester l'inscription:"
echo 'curl -X POST https://app.martialcomp.com/api/v1/auth/register/ \'
echo '  -H "Content-Type: application/json" \'
echo '  -d '"'"'{"username":"test","email":"test@example.com","password":"Test1234","password_confirm":"Test1234"}'"'"
