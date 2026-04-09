#!/bin/bash
# Script de correction de l'import des pratiquants
# Date: 2025-11-23
# Utilise l'alias SSH: martialcomp-production

set -e

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Fix Import Pratiquants - MartialComp ==="
echo ""

# Étape 1: Copier le fichier import_export.py corrigé
echo "1. Déploiement du fichier import_export.py corrigé..."
scp apps/competitions/views/club/import_export.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/club/import_export.py

echo "   Fichier déployé."

# Étape 2: Redémarrer Gunicorn
echo ""
echo "2. Redémarrage de Gunicorn..."
ssh ${REMOTE_HOST} << 'ENDSSH'
# Trouver et tuer le processus gunicorn
pkill -f "gunicorn config.wsgi" || true
sleep 2

# Redémarrer avec le chemin complet
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
nohup /var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 3 \
    --daemon \
    --error-logfile logs/gunicorn_error.log \
    --access-logfile logs/gunicorn_access.log &

sleep 3
echo "Vérification du processus gunicorn..."
ps aux | grep gunicorn | grep -v grep || echo "Gunicorn ne semble pas démarré!"
ENDSSH

echo ""
echo "=== Fix terminé ==="
echo "Veuillez tester l'import depuis: https://martialcomp.com/fr/club/import-export/"
echo ""
echo "Pour voir les logs après le test, exécuter:"
echo "ssh martialcomp-production 'tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log'"
