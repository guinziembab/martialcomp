#!/bin/bash
# Script de déploiement - Correction bouton création compétition fédération
# À exécuter depuis le serveur de production

echo "=== Déploiement de la correction du bouton création compétition fédération ==="

# Configuration
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# 1. Sauvegarder le fichier actuel
echo "1. Sauvegarde du fichier actuel..."
cp $PROD_PATH/apps/competitions/views/competitions.py $PROD_PATH/apps/competitions/views/competitions.py.backup_$(date +%Y%m%d_%H%M%S)

# 3. Redémarrer Gunicorn
echo "2. Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# 4. Vérifier le statut
echo "3. Vérification du statut..."
sudo systemctl status gunicorn --no-pager | head -10

echo ""
echo "=== Déploiement terminé ==="
echo "Testez le bouton 'Créer une compétition' sur le dashboard fédération."
