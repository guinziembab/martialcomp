#!/bin/bash

echo "🚀 Déploiement automatisé Federation Dashboard vers Production"
echo "============================================================="

# Configuration
PACKAGE_FILE="federation_production_package_20251015_172243_v2.tar.gz"
REMOTE_HOST="martialcomp-production"
REMOTE_TEMP="/tmp/"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Vérifier le package
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Package non trouvé: $PACKAGE_FILE"
    exit 1
fi

echo "📦 Package: $PACKAGE_FILE"
echo "🎯 Serveur: $REMOTE_HOST"
echo ""

# Étape 1: Transfert
echo "📤 [1/4] Transfert du package..."
scp $PACKAGE_FILE ${REMOTE_HOST}:${REMOTE_TEMP}

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du transfert!"
    exit 1
fi

echo "✅ Transfert réussi"
echo ""

# Étape 2: Extraction et déploiement sur le serveur
echo "🔧 [2/4] Déploiement sur le serveur..."

ssh $REMOTE_HOST << 'REMOTE_SCRIPT'
set -e

echo "📍 Serveur: $(hostname)"
echo ""

# Variables
PACKAGE_FILE="federation_production_package_20251015_172243_v2.tar.gz"
TEMP_DIR="/tmp"
EXTRACT_DIR="federation_production_package_20251015_172243"

# Trouver le répertoire du projet
echo "🔍 Recherche du projet Django..."
POSSIBLE_PATHS=(
    "/var/www/martialcomp"
    "/home/martialcomp/martialcomp"
    "/opt/martialcomp"
    "/var/www/html/martialcomp"
    "/home/*/martialcomp"
)

PROJECT_DIR=""
for path in "${POSSIBLE_PATHS[@]}"; do
    if [ -d "$path/apps/competitions" ]; then
        PROJECT_DIR="$path"
        break
    fi
done

if [ -z "$PROJECT_DIR" ]; then
    echo "❌ Impossible de trouver le projet Django!"
    echo "Chemins vérifiés: ${POSSIBLE_PATHS[@]}"
    exit 1
fi

echo "✅ Projet trouvé: $PROJECT_DIR"
echo ""

# Extraire le package
cd $TEMP_DIR
echo "📦 Extraction du package..."
tar -xzf $PACKAGE_FILE

# Aller dans le projet
cd $PROJECT_DIR
echo "📍 Répertoire de travail: $(pwd)"
echo ""

# Exécuter le script de déploiement
echo "🚀 Exécution du déploiement..."
bash $TEMP_DIR/$EXTRACT_DIR/deploy_production.sh

echo ""
echo "✅ Déploiement terminé sur le serveur"

# Nettoyer
rm -rf $TEMP_DIR/$EXTRACT_DIR
rm -f $TEMP_DIR/$PACKAGE_FILE

REMOTE_SCRIPT

if [ $? -ne 0 ]; then
    echo "❌ Erreur lors du déploiement!"
    exit 1
fi

echo ""
echo "🔄 [3/4] Redémarrage des services..."

# Redémarrer les services
ssh $REMOTE_HOST << 'RESTART_SCRIPT'
echo "🔍 Détection du serveur web..."

# Détecter et redémarrer le service approprié
if systemctl is-active --quiet apache2; then
    echo "✅ Apache2 détecté"
    sudo systemctl restart apache2
    echo "✅ Apache2 redémarré"
elif systemctl is-active --quiet httpd; then
    echo "✅ HTTPD détecté"
    sudo systemctl restart httpd
    echo "✅ HTTPD redémarré"
elif systemctl is-active --quiet gunicorn; then
    echo "✅ Gunicorn détecté"
    sudo systemctl restart gunicorn
    if systemctl is-active --quiet nginx; then
        sudo systemctl restart nginx
        echo "✅ Nginx redémarré"
    fi
    echo "✅ Gunicorn redémarré"
else
    echo "⚠️  Aucun serveur web détecté automatiquement"
    echo "Veuillez redémarrer manuellement votre serveur web"
fi

# Si supervisord est utilisé
if command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart all 2>/dev/null || true
fi

RESTART_SCRIPT

echo ""
echo "🧪 [4/4] Test de vérification..."

# Test basique
ssh $REMOTE_HOST << 'TEST_SCRIPT'
# Essayer de trouver l'URL du site
if [ -f "/etc/apache2/sites-enabled/000-default.conf" ]; then
    DOMAIN=$(grep -oP 'ServerName\s+\K[^\s]+' /etc/apache2/sites-enabled/*.conf | head -1)
elif [ -f "/etc/nginx/sites-enabled/default" ]; then
    DOMAIN=$(grep -oP 'server_name\s+\K[^\s;]+' /etc/nginx/sites-enabled/* | head -1)
fi

if [ -z "$DOMAIN" ]; then
    DOMAIN="votre-domaine.com"
fi

echo ""
echo "📌 URL à tester: https://$DOMAIN/fr/competitions/dashboard/federations/"
echo ""
echo "Vérifiez manuellement que la page s'affiche sans erreur"

TEST_SCRIPT

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ!"
echo ""
echo "📋 Résumé:"
echo "- Package transféré et extrait"
echo "- Fichiers déployés avec sauvegardes"
echo "- Services redémarrés"
echo ""
echo "🧪 Testez maintenant le dashboard:"
echo "1. Ouvrez votre navigateur"
echo "2. Allez à /fr/competitions/dashboard/federations/"
echo "3. Vérifiez qu'il n'y a pas d'erreur"
echo ""
echo "💡 En cas de problème:"
echo "- Vérifiez les logs du serveur"
echo "- Les sauvegardes sont dans backups_federation_*"