#!/bin/bash
# Script de déploiement automatique des corrections
# Date: 2025-10-24

set -e

echo "=========================================="
echo "DÉPLOIEMENT DES CORRECTIONS"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}[1/3]${NC} Transfert du template corrigé..."
scp apps/competitions/templates/competitions/club/competition_management_general.html \
    martialcomp-production:/home/martialcomp/martialcomp/apps/competitions/templates/competitions/club/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Template transféré avec succès"
else
    echo -e "${RED}✗${NC} Erreur lors du transfert du template"
    exit 1
fi
echo ""

echo -e "${BLUE}[2/3]${NC} Transfert du script de déploiement..."
scp fix_competition_management_500.sh martialcomp-production:/home/martialcomp/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Script transféré avec succès"
else
    echo -e "${RED}✗${NC} Erreur lors du transfert du script"
    exit 1
fi
echo ""

echo -e "${BLUE}[3/3]${NC} Exécution du script sur le serveur..."
ssh martialcomp-production "cd /home/martialcomp && chmod +x fix_competition_management_500.sh && bash fix_competition_management_500.sh"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Déploiement terminé avec succès"
else
    echo -e "${RED}✗${NC} Erreur lors de l'exécution du script"
    exit 1
fi
echo ""

echo "=========================================="
echo -e "${GREEN}DÉPLOIEMENT RÉUSSI !${NC}"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "1. Testez: https://martialcomp.com/fr/competitions/club/competitions/management/"
echo "2. Vérifiez: https://martialcomp.com/fr/competitions/dashboard/club/"
echo "3. Ouvrez la console (F12) pour vérifier les erreurs JavaScript"
echo ""
