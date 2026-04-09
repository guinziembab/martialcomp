#!/bin/bash

echo "=========================================="
echo "🧪 TEST DE LA SOLUTION B"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}📍 URL à tester:${NC}"
echo "https://martialcomp.com/fr/competitions/club/competitions/4/manage-simple/"
echo ""

echo -e "${YELLOW}⚠️  AVANT DE TESTER:${NC}"
echo "1. Videz le cache de votre navigateur (Ctrl + Shift + R)"
echo "2. Ouvrez la Console (F12)"
echo ""

# Test 1: Vérifier que le fichier existe en production
echo -e "${YELLOW}🔍 Test 1: Vérification du fichier template...${NC}"
ssh martialcomp-production "test -f /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/competition_management_simple.html && echo 'OK' || echo 'MANQUANT'" 2>/dev/null | grep -q "OK"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Template simplifié: OK${NC}"
else
    echo -e "   ${RED}❌ Template simplifié: MANQUANT${NC}"
    exit 1
fi

# Test 2: Vérifier que la vue existe
echo -e "${YELLOW}🔍 Test 2: Vérification de la vue...${NC}"
ssh martialcomp-production "grep -q 'def competition_management_simple' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/event_organizer.py && echo 'OK' || echo 'MANQUANT'" 2>/dev/null | grep -q "OK"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Vue competition_management_simple: OK${NC}"
else
    echo -e "   ${RED}❌ Vue: MANQUANTE${NC}"
    exit 1
fi

# Test 3: Vérifier que l'URL est configurée
echo -e "${YELLOW}🔍 Test 3: Vérification de l'URL...${NC}"
ssh martialcomp-production "grep -q 'manage-simple' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/club.py && echo 'OK' || echo 'MANQUANT'" 2>/dev/null | grep -q "OK"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ URL /manage-simple/: OK${NC}"
else
    echo -e "   ${RED}❌ URL: MANQUANTE${NC}"
    exit 1
fi

# Test 4: Vérifier que les services tournent
echo -e "${YELLOW}🔍 Test 4: Vérification des services...${NC}"
ssh martialcomp-production "sudo systemctl is-active martialcomp" 2>/dev/null | grep -q "active"

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Service Gunicorn: ACTIF${NC}"
else
    echo -e "   ${RED}❌ Service Gunicorn: INACTIF${NC}"
    echo "   Tentative de redémarrage..."
    ssh martialcomp-production "sudo systemctl restart martialcomp"
fi

# Test 5: Test HTTP
echo -e "${YELLOW}🔍 Test 5: Test de l'URL (HTTP)...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/club/competitions/4/manage-simple/" -L --max-time 10)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "   ${GREEN}✅ Réponse HTTP: $HTTP_CODE (OK)${NC}"
elif [ "$HTTP_CODE" = "403" ]; then
    echo -e "   ${YELLOW}⚠️  Réponse HTTP: 403 (Authentification requise - NORMAL)${NC}"
elif [ "$HTTP_CODE" = "500" ]; then
    echo -e "   ${RED}❌ Réponse HTTP: 500 (ERREUR SERVEUR)${NC}"
    echo "   Vérifiez les logs: ssh martialcomp-production 'tail -50 /var/log/martialcomp/gunicorn.err.log'"
else
    echo -e "   ${RED}❌ Réponse HTTP: $HTTP_CODE${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ TESTS AUTOMATIQUES TERMINÉS${NC}"
echo "=========================================="
echo ""

echo -e "${YELLOW}📋 CHECKLIST MANUELLE:${NC}"
echo ""
echo "1. ☐ Allez sur: https://martialcomp.com/fr/competitions/club/competitions/4/manage-simple/"
echo "2. ☐ Videz le cache (Ctrl + Shift + R)"
echo "3. ☐ Ouvrez la Console (F12)"
echo "4. ☐ Vérifiez: Aucune erreur rouge"
echo "5. ☐ Vérifiez: Message '✅ Template simplifié chargé'"
echo "6. ☐ Testez: Créer un type de compétition"
echo "7. ☐ Testez: Supprimer le type créé"
echo "8. ☐ Testez: Créer une catégorie"
echo "9. ☐ Testez: Supprimer la catégorie créée"
echo ""

echo -e "${YELLOW}🎯 RÉSULTATS ATTENDUS:${NC}"
echo "✅ Aucune erreur JavaScript"
echo "✅ Messages verts de succès"
echo "✅ Rechargement automatique après chaque action"
echo "✅ Éléments visibles dans les listes"
echo ""

echo -e "${YELLOW}📚 DOCUMENTATION:${NC}"
echo "- Guide utilisateur: GUIDE_UTILISATEUR_SOLUTION_B.md"
echo "- Documentation technique: SOLUTION_B_REFONTE_TEMPLATE_20251028.md"
echo "- Rapport final: RAPPORT_FINAL_SOLUTION_B_20251028.md"
echo ""

echo "=========================================="
echo -e "${GREEN}🎉 BON TEST !${NC}"
echo "=========================================="
