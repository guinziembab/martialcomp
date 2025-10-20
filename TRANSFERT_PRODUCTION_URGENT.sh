#!/bin/bash
# Script de transfert urgent vers la production

echo "=== TRANSFERT URGENT VERS LA PRODUCTION ==="
echo ""
echo "Ce script va transférer les fichiers corrigés vers le serveur de production"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier la connexion SSH
echo -e "${YELLOW}1. Vérification de la connexion SSH...${NC}"
if ssh martialcomp.com "echo 'Connexion OK'" 2>/dev/null; then
    echo -e "${GREEN}   ✓ Connexion SSH établie${NC}"
else
    echo -e "${RED}   ✗ Impossible de se connecter au serveur${NC}"
    echo "   Essayez manuellement: ssh martialcomp.com"
    exit 1
fi

# Transférer le fichier corrigé
echo ""
echo -e "${YELLOW}2. Transfert du fichier corrigé...${NC}"
scp apps/competitions/views/dashboard/federations.py martialcomp.com:~/martialcomp/apps/competitions/views/dashboard/federations.py.NEW

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Fichier transféré${NC}"
else
    echo -e "${RED}   ✗ Échec du transfert${NC}"
    exit 1
fi

# Transférer les scripts de diagnostic
echo ""
echo -e "${YELLOW}3. Transfert des scripts de diagnostic...${NC}"
scp check_users_production.sh martialcomp.com:~/martialcomp/
scp fix_federation_500_error.sh martialcomp.com:~/martialcomp/
scp recreate_fedetest1.sh martialcomp.com:~/martialcomp/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✓ Scripts transférés${NC}"
else
    echo -e "${RED}   ✗ Échec du transfert des scripts${NC}"
fi

# Exécuter les commandes sur le serveur
echo ""
echo -e "${YELLOW}4. Exécution des commandes sur le serveur...${NC}"

ssh martialcomp.com << 'ENDSSH'
cd ~/martialcomp

# Rendre les scripts exécutables
chmod +x check_users_production.sh fix_federation_500_error.sh recreate_fedetest1.sh

echo "Scripts rendus exécutables"

# Sauvegarder l'ancien fichier
echo ""
echo "Sauvegarde du fichier actuel..."
cp apps/competitions/views/dashboard/federations.py apps/competitions/views/dashboard/federations.py.backup_$(date +%Y%m%d_%H%M%S)

# Remplacer par le nouveau fichier
echo "Remplacement par le fichier corrigé..."
mv apps/competitions/views/dashboard/federations.py.NEW apps/competitions/views/dashboard/federations.py

# Vérifier qu'il n'y a plus d'erreurs
echo ""
echo "Vérification des corrections..."
if grep -q "self\.request\.user" apps/competitions/views/dashboard/federations.py; then
    echo "⚠ ATTENTION: Il reste des occurrences de 'self.request.user'"
    grep -n "self\.request\.user" apps/competitions/views/dashboard/federations.py
else
    echo "✓ Aucune occurrence de 'self.request.user' trouvée"
fi

# Redémarrer l'application
echo ""
echo "Redémarrage de l'application..."
touch passenger_wsgi.py
echo "✓ Application redémarrée"

ENDSSH

echo ""
echo -e "${GREEN}=== TRANSFERT TERMINÉ ===${NC}"
echo ""
echo "Prochaines étapes à effectuer MANUELLEMENT sur le serveur:"
echo ""
echo "1. Vérifier l'état des utilisateurs:"
echo -e "   ${YELLOW}ssh martialcomp.com${NC}"
echo -e "   ${YELLOW}cd ~/martialcomp && bash check_users_production.sh${NC}"
echo ""
echo "2. Si l'utilisateur FEDETEST1 a disparu, le recréer:"
echo -e "   ${YELLOW}bash recreate_fedetest1.sh${NC}"
echo ""
echo "3. Tester la connexion:"
echo "   URL: https://martialcomp.com/fr/account/login/"
echo "   Username: FEDETEST1"
echo "   Dashboard: https://martialcomp.com/fr/competitions/federations/6/dashboard/"
echo ""
echo "4. Vérifier les logs en cas d'erreur:"
echo -e "   ${YELLOW}tail -f ~/logs/error_log${NC}"
echo ""
