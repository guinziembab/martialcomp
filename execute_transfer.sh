#!/bin/bash
# Script pour transférer les fichiers vers production via SSH

PRODUCTION_HOST="root@martialcomp.com"
PRODUCTION_DIR="/var/www/martialcomp"
REMOTE_TEMP="/tmp/martialcomp_transfer_$(date +%Y%m%d_%H%M%S)"

echo "======================================"
echo "TRANSFERT SSH VERS PRODUCTION"
echo "======================================"
echo ""

# 1. Copier le package vers le serveur
echo "1. Transfert du package vers le serveur..."
echo "   Destination: $PRODUCTION_HOST:$REMOTE_TEMP"
echo ""
echo "ATTENTION: Vous allez devoir entrer le mot de passe SSH"
echo ""

# Créer le répertoire temporaire sur le serveur
ssh $PRODUCTION_HOST "mkdir -p $REMOTE_TEMP"

# Transférer tous les fichiers
scp -r transfer_package/* patches/*.patch $PRODUCTION_HOST:$REMOTE_TEMP/

# 2. Exécuter le script de déploiement
echo ""
echo "2. Exécution du déploiement sur le serveur..."
echo "   (Vous devrez peut-être entrer le mot de passe à nouveau)"
echo ""

ssh $PRODUCTION_HOST "cd $REMOTE_TEMP && chmod +x deploy_on_server.sh && ./deploy_on_server.sh"

# 3. Nettoyer les fichiers temporaires
echo ""
echo "3. Nettoyage des fichiers temporaires..."
ssh $PRODUCTION_HOST "rm -rf $REMOTE_TEMP"

echo ""
echo "======================================"
echo "TRANSFERT TERMINÉ!"
echo "======================================"
echo ""
echo "Actions recommandées:"
echo "1. Vérifier le site: https://martialcomp.com"
echo "2. Tester l'API: curl https://martialcomp.com/api/health/"
echo "3. Vérifier les logs sur le serveur:"
echo "   ssh $PRODUCTION_HOST 'tail -f /var/log/nginx/error.log'"