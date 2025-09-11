#!/bin/bash

# Script pour déployer les corrections des icônes volumineuses sur martialcomp.com
echo "🚀 Déploiement des corrections d'icônes sur le serveur de production..."

# Fichiers à transférer
TEMPLATE_FILE="apps/competitions/templates/competitions/dashboard/base.html"
URLS_FILE="apps/competitions/urls/dashboard.py"
DOC_TEMPLATE="apps/competitions/templates/competitions/dashboard/documentation/index.html"

# Serveur de production (à adapter selon votre configuration)
SERVER="root@martialcomp.com"
REMOTE_PATH="/var/www/martialcomp"

echo "📁 Transfert du template de base du dashboard..."
scp "$TEMPLATE_FILE" "$SERVER:$REMOTE_PATH/$TEMPLATE_FILE"

echo "🔗 Transfert du fichier URLs..."
scp "$URLS_FILE" "$SERVER:$REMOTE_PATH/$URLS_FILE"

echo "📄 Transfert du template de documentation..."
scp "$DOC_TEMPLATE" "$SERVER:$REMOTE_PATH/$DOC_TEMPLATE"

echo "🔄 Redémarrage des services sur le serveur..."
ssh "$SERVER" << 'ENDSSH'
cd /var/www/martialcomp
# Collecte des fichiers statiques
python3 manage.py collectstatic --noinput
# Redémarrage de l'application
systemctl restart nginx
systemctl restart martialcomp
# ou selon votre configuration : systemctl restart gunicorn, etc.
echo "✅ Services redémarrés"
ENDSSH

echo "🎉 Déploiement terminé ! Les icônes volumineuses ont été supprimées."
echo "🌐 Vérifiez sur https://martialcomp.com/fr/competitions/dashboard/documentation/"