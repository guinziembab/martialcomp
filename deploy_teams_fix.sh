#!/bin/bash
# Script de déploiement des corrections de gestion des équipes
# Date: 2025-11-23
# Corrections:
#   - Erreur syntaxe JavaScript (apostrophes dans traductions Django)
#   - Utilisation de {% filter escapejs %} pour échapper les caractères
#   - Onglets "Déjà inscrits" et "Équipes" fonctionnels

set -e

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement Corrections Équipes v2 - MartialComp ==="
echo ""

# Étape 1: Copier le template corrigé
echo "1. Déploiement du template competition_registration_simple.html corrigé..."
scp apps/competitions/templates/competitions/club/competition_registration_simple.html \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/club/competition_registration_simple.html

echo "   ✓ Template déployé."

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
ps aux | grep gunicorn | grep -v grep || echo "⚠️ Gunicorn ne semble pas démarré!"
ENDSSH

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Corrections apportées:"
echo "  ✓ Erreur syntaxe JavaScript corrigée (template literals + {% trans %})"
echo "  ✓ Onglets 'Déjà inscrits' et 'Équipes' fonctionnels"
echo "  ✓ Gestion des équipes (création, modification, suppression)"
echo ""
echo "Testez depuis: https://martialcomp.com/fr/competitions/club/competition-registration/4/"
echo ""
echo "Pour voir les logs après le test:"
echo "ssh martialcomp-production 'tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log'"
