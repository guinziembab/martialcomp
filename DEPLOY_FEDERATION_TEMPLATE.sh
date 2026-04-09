#!/bin/bash
# Script de déploiement du template federation.html
# À exécuter depuis WSL avec l'alias martialcomp-production

echo "=== Déploiement du template federation.html ==="

# Configuration
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
TEMPLATE_FILE="apps/competitions/templates/competitions/dashboard/federation.html"

# 1. Copier le template sur le serveur
echo "1. Copie du template federation.html..."
scp ${LOCAL_PATH}/${TEMPLATE_FILE} martialcomp-production:${PROD_PATH}/${TEMPLATE_FILE}

# 2. Vérifier que le fichier a bien été copié
echo "2. Vérification du fichier sur le serveur..."
ssh martialcomp-production "ls -la ${PROD_PATH}/${TEMPLATE_FILE}"

# 3. Redémarrer le serveur pour prendre en compte les changements
echo "3. Redémarrage du serveur..."
ssh martialcomp-production "sudo plesk repair web -y"

echo ""
echo "=== Déploiement terminé ==="
echo "Le template federation.html a été mis à jour."
echo "Testez à nouveau le bouton 'Créer' sur le dashboard fédération."
