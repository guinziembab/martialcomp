#!/bin/bash
# Script de déploiement du thème dark/gold pour la page événements

SERVER="martial@217.154.24.122"
REMOTE_PATH="/home/martial/martialcomp"

echo "=== Déploiement du template événements avec thème dark/gold ==="

# Déployer le template event_list.html
echo "1. Envoi du template event_list.html..."
scp apps/competitions/templates/competitions/events/event_list.html $SERVER:$REMOTE_PATH/apps/competitions/templates/competitions/events/

# Redémarrer Gunicorn pour vider le cache des templates
echo "2. Redémarrage de Gunicorn..."
ssh $SERVER "sudo systemctl restart gunicorn || (pgrep -f gunicorn | head -1 | xargs kill -HUP)"

echo "=== Déploiement terminé ==="
echo "Testez: https://martialcomp.com/fr/competitions/events/"
