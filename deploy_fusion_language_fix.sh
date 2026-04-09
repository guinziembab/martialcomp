#!/bin/bash
# Script de déploiement - Fusion équipes inter-clubs + Correction changement de langue
# Date: 2025-11-23

set -e

REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement MartialComp - Fusion Équipes + Fix Langue ==="
echo ""

# Étape 1: Copier les fichiers modifiés
echo "1. Déploiement des fichiers..."

echo "   - custom_set_language.py (correction changement de langue)"
scp apps/competitions/views/custom_set_language.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/custom_set_language.py

echo "   - config/urls.py"
scp config/urls.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/config/urls.py

echo "   - registration_api.py (APIs fusion)"
scp apps/competitions/views/club/registration_api.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/club/registration_api.py

echo "   - club.py (URLs)"
scp apps/competitions/urls/club.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/urls/club.py

echo "   - combat.py (modèle Equipe)"
scp apps/competitions/models/combat.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/models/combat.py

echo "   - migration fusion"
scp apps/competitions/migrations/0012_equipe_fusion_fields.py \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/migrations/0012_equipe_fusion_fields.py

echo "   - competition_registration_simple.html (template fusion)"
scp apps/competitions/templates/competitions/club/competition_registration_simple.html \
    ${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/club/competition_registration_simple.html

echo ""
echo "   ✓ Fichiers déployés."

# Étape 2: Exécuter les migrations
echo ""
echo "2. Exécution des migrations sur le serveur..."
ssh ${REMOTE_HOST} << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
python manage.py migrate competitions --settings=config.settings.production
ENDSSH

echo "   ✓ Migrations appliquées."

# Étape 3: Redémarrer Gunicorn
echo ""
echo "3. Redémarrage de Gunicorn..."
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
echo "  ✓ Changement de langue fluide (dropdown fonctionnel)"
echo "  ✓ Préfixe de langue correctement mis à jour (/fr/ -> /en/)"
echo "  ✓ APIs fusion d'équipes inter-clubs"
echo "  ✓ Modèle Equipe étendu (multi-club, statut fusion)"
echo ""
echo "Nouvelles fonctionnalités fusion:"
echo "  - Lister les équipes incomplètes des autres clubs"
echo "  - Demander une fusion avec une équipe partenaire"
echo "  - Accepter/Refuser les demandes de fusion"
echo "  - Créer automatiquement l'équipe fusionnée"
echo ""
echo "Testez:"
echo "  - Changement de langue: https://martialcomp.com/fr/ (cliquez sur le sélecteur)"
echo "  - Équipes: https://martialcomp.com/fr/competitions/club/competition-registration/4/"
echo ""
echo "Pour voir les logs:"
echo "ssh martialcomp-production 'tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log'"
