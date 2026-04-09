#!/bin/bash
# Déploiement des corrections:
# 1. Analyse des combats (nouvelle fonctionnalité)
# 2. Correction formulaire création fédération (country field + thème sombre)

REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement des corrections MartialComp ==="
echo ""

# 1. Combat analysis feature
echo "1. Déploiement de la fonctionnalité d'analyse des combats..."
scp apps/competitions/views/dashboard/club.py ${REMOTE}:${REMOTE_PATH}/apps/competitions/views/dashboard/
scp apps/competitions/urls/dashboard.py ${REMOTE}:${REMOTE_PATH}/apps/competitions/urls/
scp apps/competitions/templates/competitions/dashboard/combat_analysis.html ${REMOTE}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/
scp apps/competitions/templates/competitions/dashboard/club.html ${REMOTE}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/

# 2. Federation onboarding fix
echo "2. Déploiement de la correction du formulaire fédération..."
scp apps/competitions/templates/competitions/onboarding/federation_creation.html ${REMOTE}:${REMOTE_PATH}/apps/competitions/templates/competitions/onboarding/

# 3. Restart service
echo "3. Redémarrage du service Gunicorn..."
ssh ${REMOTE} "sudo systemctl restart gunicorn-martialcomp"

echo ""
echo "=== Déploiement terminé ==="
echo "Vérifiez:"
echo "- https://martialcomp.com/en/competitions/onboarding/federation/"
echo "- Dashboard Club > Onglet Combat > Analyse des combats"
