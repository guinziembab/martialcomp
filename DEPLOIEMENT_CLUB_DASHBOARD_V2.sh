#!/bin/bash
# ========================================
# SCRIPT DE DÉPLOIEMENT - Dashboard Club v2.0.0
# ========================================
# Date: $(date +%Y-%m-%d)
# Version: 2.0.0
# ========================================

set -e  # Arrêter en cas d'erreur

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/martialcomp"
BACKUP_DIR="${PROJECT_DIR}/backups/club_dashboard_v2_$(date +%Y%m%d_%H%M%S)"
STATIC_DIR="${PROJECT_DIR}/static"
TEMPLATE_DIR="${PROJECT_DIR}/templates/competitions/dashboard"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DÉPLOIEMENT DASHBOARD CLUB v2.0.0${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Créer le répertoire de sauvegarde
echo -e "${YELLOW}[1/8] Création du répertoire de sauvegarde...${NC}"
mkdir -p "${BACKUP_DIR}"
echo -e "${GREEN}✓ Répertoire créé: ${BACKUP_DIR}${NC}"

# 2. Sauvegarder l'ancien template
echo -e "${YELLOW}[2/8] Sauvegarde de l'ancien template...${NC}"
if [ -f "${TEMPLATE_DIR}/club.html" ]; then
    cp "${TEMPLATE_DIR}/club.html" "${BACKUP_DIR}/club.html"
    echo -e "${GREEN}✓ Template sauvegardé${NC}"
else
    echo -e "${YELLOW}⚠ Template actuel non trouvé${NC}"
fi

# 3. Sauvegarder les fichiers static existants
echo -e "${YELLOW}[3/8] Sauvegarde des fichiers static...${NC}"
if [ -d "${STATIC_DIR}/js/club_" ] || [ -f "${STATIC_DIR}/js/club_dashboard_*.js" ]; then
    cp -r ${STATIC_DIR}/js/club_* "${BACKUP_DIR}/" 2>/dev/null || true
    echo -e "${GREEN}✓ Fichiers JS sauvegardés${NC}"
fi

if [ -d "${STATIC_DIR}/css/club_" ] || [ -f "${STATIC_DIR}/css/club_dashboard_*.css" ]; then
    cp -r ${STATIC_DIR}/css/club_* "${BACKUP_DIR}/" 2>/dev/null || true
    echo -e "${GREEN}✓ Fichiers CSS sauvegardés${NC}"
fi

# 4. Créer les répertoires nécessaires
echo -e "${YELLOW}[4/8] Création des répertoires...${NC}"
mkdir -p "${STATIC_DIR}/js/dashboard"
mkdir -p "${STATIC_DIR}/css/dashboard"
echo -e "${GREEN}✓ Répertoires créés${NC}"

# 5. Copier les nouveaux fichiers JavaScript
echo -e "${YELLOW}[5/8] Copie des fichiers JavaScript...${NC}"
# Note: Les fichiers doivent être uploadés manuellement via WinSCP/SFTP
# depuis apps/competitions/Package_Club_NEW_DASHBOARD/ vers les répertoires ci-dessus
echo -e "${YELLOW}⚠ Veuillez uploader manuellement les fichiers suivants:${NC}"
echo -e "   - club_dashboard_core.js → ${STATIC_DIR}/js/dashboard/"
echo -e "   - club_dashboard_bulk.js → ${STATIC_DIR}/js/dashboard/"
echo -e "   - club_dashboard_import.js → ${STATIC_DIR}/js/dashboard/"
echo -e "   - club_dashboard.css → ${STATIC_DIR}/css/dashboard/"
read -p "Appuyez sur Entrée une fois les fichiers uploadés..."

# Vérifier que les fichiers existent
if [ ! -f "${STATIC_DIR}/js/dashboard/club_dashboard_core.js" ]; then
    echo -e "${RED}✗ Erreur: club_dashboard_core.js non trouvé${NC}"
    exit 1
fi
if [ ! -f "${STATIC_DIR}/js/dashboard/club_dashboard_bulk.js" ]; then
    echo -e "${RED}✗ Erreur: club_dashboard_bulk.js non trouvé${NC}"
    exit 1
fi
if [ ! -f "${STATIC_DIR}/js/dashboard/club_dashboard_import.js" ]; then
    echo -e "${RED}✗ Erreur: club_dashboard_import.js non trouvé${NC}"
    exit 1
fi
if [ ! -f "${STATIC_DIR}/css/dashboard/club_dashboard.css" ]; then
    echo -e "${RED}✗ Erreur: club_dashboard.css non trouvé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Tous les fichiers JavaScript/CSS sont présents${NC}"

# 6. Copier le nouveau template
echo -e "${YELLOW}[6/8] Copie du nouveau template...${NC}"
# Note: Le template doit être uploadé manuellement
echo -e "${YELLOW}⚠ Veuillez uploader le template club.html vers:${NC}"
echo -e "   ${TEMPLATE_DIR}/club.html"
read -p "Appuyez sur Entrée une fois le template uploadé..."

if [ ! -f "${TEMPLATE_DIR}/club.html" ]; then
    echo -e "${RED}✗ Erreur: Template club.html non trouvé${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Template copié${NC}"

# 7. Vérifier l'encodage UTF-8
echo -e "${YELLOW}[7/8] Vérification de l'encodage UTF-8...${NC}"
if file -i "${TEMPLATE_DIR}/club.html" | grep -q "utf-8"; then
    echo -e "${GREEN}✓ Encodage UTF-8 correct${NC}"
else
    echo -e "${YELLOW}⚠ Encodage non UTF-8 détecté, conversion...${NC}"
    iconv -f ISO-8859-1 -t UTF-8 "${TEMPLATE_DIR}/club.html" > "${TEMPLATE_DIR}/club.html.utf8"
    mv "${TEMPLATE_DIR}/club.html.utf8" "${TEMPLATE_DIR}/club.html"
    echo -e "${GREEN}✓ Conversion effectuée${NC}"
fi

# 8. Collectstatic Django
echo -e "${YELLOW}[8/8] Collectstatic Django...${NC}"
cd "${PROJECT_DIR}"
source venv/bin/activate 2>/dev/null || true
python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Collectstatic terminé${NC}"

# 9. Redémarrer Gunicorn
echo -e "${YELLOW}[9/9] Redémarrage de Gunicorn...${NC}"
sudo systemctl restart gunicorn || touch "${PROJECT_DIR}/reload"
echo -e "${GREEN}✓ Gunicorn redémarré${NC}"

# Résumé
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}DÉPLOIEMENT TERMINÉ AVEC SUCCÈS${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backup sauvegardé dans: ${BACKUP_DIR}"
echo -e "\n${YELLOW}Prochaines étapes:${NC}"
echo -e "1. Tester le dashboard: https://martialcomp.com/dashboard/club/"
echo -e "2. Vérifier la console navigateur (F12) pour les erreurs"
echo -e "3. Tester les fonctionnalités:"
echo -e "   - Import CSV"
echo -e "   - Inscription en masse"
echo -e "   - Navigation par onglets"
echo -e "\n${YELLOW}En cas de problème, restaurer depuis:${NC}"
echo -e "   ${BACKUP_DIR}"
