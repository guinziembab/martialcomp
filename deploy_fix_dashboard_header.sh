#!/bin/bash
# Script de déploiement - Correction en-tête dashboard (logo + disciplines)
# Date: 2025-11-23

set -e

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement MartialComp - Correction En-tête Dashboard ==="
echo ""

# Étape 1: Copier le template corrigé
echo "1. Déploiement du template corrigé..."

echo "   - club.html (dashboard avec logo et disciplines)"
scp apps/competitions/templates/competitions/dashboard/club.html \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/club.html

echo ""
echo "   ✓ Fichier déployé."

# Étape 2: Redémarrer Gunicorn
echo ""
echo "2. Redémarrage de Gunicorn..."
ssh ${REMOTE_HOST} << 'ENDSSH'
pkill -f "gunicorn config.wsgi" || true
sleep 2

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
ps aux | grep gunicorn | grep -v grep || echo "⚠️ Gunicorn ne semble pas démarré!"
ENDSSH

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Corrections apportées:"
echo "  ✓ Logo de l'organisation affiché dans l'en-tête (modifiable par clic)"
echo "  ✓ Disciplines pratiquées affichées sous forme de badges"
echo "  ✓ Boutons d'édition/suppression du logo"
echo "  ✓ Fonctions JavaScript pour upload/delete du logo"
echo ""
echo "Testez:"
echo "  - Dashboard club: https://martialcomp.com/fr/dashboard/club/"
echo ""
echo "Pour voir les logs:"
echo "ssh martialcomp-production 'tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log'"
