#!/bin/bash
# Script maître pour déployer toute la fonctionnalité de profil hors-ligne

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  DÉPLOIEMENT DE LA FONCTIONNALITÉ PROFIL HORS-LIGNE  ${NC}"
echo -e "${BLUE}=================================================${NC}\n"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Erreur : Ce script doit être exécuté depuis le répertoire racine du projet Django${NC}"
    exit 1
fi

# Vérifier que les scripts individuels existent
if [ ! -f "deploy_offline_profile.sh" ] || [ ! -f "compile_offline_profile_translations.sh" ] || [ ! -f "deploy_static_files.sh" ]; then
    echo -e "${RED}Erreur : Un ou plusieurs scripts de déploiement sont manquants${NC}"
    exit 1
fi

# Vérifier qu'ils sont exécutables
if [ ! -x "deploy_offline_profile.sh" ] || [ ! -x "compile_offline_profile_translations.sh" ] || [ ! -x "deploy_static_files.sh" ]; then
    echo "Rendre les scripts exécutables..."
    chmod +x deploy_offline_profile.sh compile_offline_profile_translations.sh deploy_static_files.sh
fi

# Demander confirmation
echo -e "${YELLOW}Ce script va déployer la fonctionnalité de profil hors-ligne en :${NC}"
echo "1. Exécutant la migration pour ajouter les champs au modèle PractitionerQRCode"
echo "2. Compilant les fichiers de traduction pour toutes les langues"
echo "3. Déployant les fichiers CSS et autres fichiers statiques"
echo "4. Redémarrant les services nécessaires"
echo
echo -e "${YELLOW}Voulez-vous continuer ? [y/N]${NC}"
read -r CONTINUE

if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Déploiement annulé.${NC}"
    exit 0
fi

# Exécuter les scripts dans l'ordre
echo -e "\n${YELLOW}===== 1/3 : Exécution de la migration =====${NC}"
./deploy_offline_profile.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'exécution de la migration.${NC}"
    echo "Le déploiement est arrêté. Corrigez les erreurs et réessayez."
    exit 1
fi

echo -e "\n${YELLOW}===== 2/3 : Compilation des traductions =====${NC}"
./compile_offline_profile_translations.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de la compilation des traductions.${NC}"
    echo "Le déploiement continue, mais les traductions peuvent être incomplètes."
fi

echo -e "\n${YELLOW}===== 3/3 : Déploiement des fichiers statiques =====${NC}"
./deploy_static_files.sh
if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors du déploiement des fichiers statiques.${NC}"
    echo "Le déploiement est terminé, mais les fichiers CSS peuvent ne pas être disponibles."
    exit 1
fi

# Vérification finale
echo -e "\n${GREEN}===== Déploiement terminé avec succès ! =====${NC}"
echo -e "${YELLOW}Pour finaliser l'installation :${NC}"
echo "1. Redémarrez votre serveur web (Nginx/Apache) et votre serveur d'application (Gunicorn/uWSGI)"
echo "2. Vérifiez que les pages suivantes fonctionnent correctement :"
echo "   - /scan/practitioner/ID/offline-profile/"
echo "   - /scan/profile/offline/"
echo "3. Testez la fonctionnalité en scannant un QR code généré"
echo
echo -e "${GREEN}Bonne utilisation de la fonctionnalité de profil hors-ligne !${NC}"