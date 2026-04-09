#!/bin/bash
# ================================================================
# DÉPLOIEMENT CONFIGURATION EMAIL - PRODUCTION
# Phase 1: Configuration SMTP IONOS
# ================================================================

echo "=== Déploiement Configuration Email ==="
echo ""

# Variables
PROD_SERVER="martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
PROD_USER="martialcomp"

# Fichiers à déployer
FILES_TO_DEPLOY=(
    "config/settings/production.py"
    "config/settings/base.py"
    "apps/competitions/services/email_service.py"
    "apps/competitions/management/commands/test_email_config.py"
)

echo "1. Transfert des fichiers..."
echo ""

for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "   Transfert: $file"
    scp "$file" "${PROD_USER}@${PROD_SERVER}:${PROD_PATH}/${file}"
done

echo ""
echo "2. Configuration des variables d'environnement..."
echo ""
echo "   IMPORTANT: Configurer ces variables sur le serveur:"
echo ""
echo "   export EMAIL_HOST=smtp.ionos.fr"
echo "   export EMAIL_PORT=587"
echo "   export EMAIL_HOST_USER=noreply@martialcomp.com"
echo "   export EMAIL_HOST_PASSWORD=<votre_mot_de_passe>"
echo "   export ADMIN_EMAIL=admin@martialcomp.com"
echo ""

echo "3. Redémarrage du serveur..."
echo ""
echo "   ssh ${PROD_USER}@${PROD_SERVER} 'cd ${PROD_PATH} && kill -HUP \$(cat gunicorn.pid)'"
echo ""

echo "4. Test de la configuration email..."
echo ""
echo "   ssh ${PROD_USER}@${PROD_SERVER} 'cd ${PROD_PATH} && python manage.py test_email_config'"
echo ""

echo "=== Fin du déploiement ==="
