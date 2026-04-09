#!/bin/bash
# =============================================================================
# SCRIPT DE DEPLOIEMENT - Banniere et Galerie Organisation
# =============================================================================
# Ce script applique la migration et redémarre gunicorn en production
#
# UTILISATION:
#   ssh martialcomp-production 'bash -s' < DEPLOY_BANNER_GALLERY_PRODUCTION.sh
#
# OU connexion manuelle puis:
#   cd /var/www/vhosts/martialcomp.com/httpdocs
#   bash /chemin/vers/DEPLOY_BANNER_GALLERY_PRODUCTION.sh
# =============================================================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  DEPLOIEMENT BANNIERE & GALERIE       ${NC}"
echo -e "${YELLOW}========================================${NC}"

# Variables
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
PYTHON="${VENV_PATH}/bin/python"

# Vérifier que le venv existe
if [ ! -f "${PYTHON}" ]; then
    echo -e "${RED}ERREUR: Python venv non trouvé à ${PYTHON}${NC}"
    exit 1
fi

# Aller dans le répertoire du projet
cd "${PROJECT_PATH}"
echo -e "${GREEN}[1/4] Répertoire: $(pwd)${NC}"

# Appliquer les migrations
echo -e "${YELLOW}[2/4] Application de la migration organizations...${NC}"
${PYTHON} manage.py migrate organizations --verbosity=1
echo -e "${GREEN}[2/4] Migration appliquée avec succès!${NC}"

# Collecter les fichiers statiques (si nécessaire)
echo -e "${YELLOW}[3/4] Vérification des fichiers statiques...${NC}"
${PYTHON} manage.py collectstatic --noinput --verbosity=0 2>/dev/null || true
echo -e "${GREEN}[3/4] Fichiers statiques OK${NC}"

# Redémarrer gunicorn
echo -e "${YELLOW}[4/4] Redémarrage de gunicorn...${NC}"
pkill -HUP -f 'gunicorn.*config.wsgi' 2>/dev/null || true
sleep 2

# Vérifier que gunicorn tourne
if pgrep -f 'gunicorn.*config.wsgi' > /dev/null; then
    echo -e "${GREEN}[4/4] Gunicorn redémarré avec succès!${NC}"
else
    echo -e "${RED}[4/4] ATTENTION: Gunicorn ne semble pas tourner. Démarrage...${NC}"
    ${PROJECT_PATH}/start_gunicorn.sh &
    sleep 3
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  DEPLOIEMENT TERMINE AVEC SUCCES!     ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Nouvelles fonctionnalités disponibles:"
echo "  - Upload de bannière (1920x600px recommandé)"
echo "  - Galerie photos (max 6 images)"
echo "  - Calendrier des événements"
echo ""
echo "Testez sur: /org/{slug}/admin/site/"
