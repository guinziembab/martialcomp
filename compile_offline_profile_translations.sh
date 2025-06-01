#!/bin/bash
# Script pour compiler les traductions du profil hors-ligne

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Erreur : Ce script doit être exécuté depuis le répertoire racine du projet Django${NC}"
    exit 1
fi

echo -e "${YELLOW}===== Compilation des traductions pour le profil hors-ligne =====${NC}"

# Étape 1: Extraire les traductions de tous les fichiers
echo -e "\n${YELLOW}1. Extraction des chaînes de traduction${NC}"

python manage.py makemessages -a
if [ $? -ne 0 ]; then
    echo -e "${RED}Erreur lors de l'extraction des messages.${NC}"
    echo "Vérifiez que gettext est bien installé sur votre système."
    exit 1
fi
echo -e "${GREEN}✓ Messages extraits avec succès${NC}"

# Étape 2: Vérifier que le fichier de référence existe
echo -e "\n${YELLOW}2. Vérification du fichier de référence des traductions${NC}"
REFERENCE_FILE="locale/offline_profile_translations.po"

if [ ! -f "$REFERENCE_FILE" ]; then
    echo -e "${RED}Le fichier de référence $REFERENCE_FILE n'existe pas.${NC}"
    echo "Créez d'abord ce fichier avec les traductions pour le profil hors-ligne."
    exit 1
fi
echo -e "${GREEN}✓ Fichier de référence trouvé${NC}"

# Étape 3: Proposer d'ajouter les traductions aux fichiers de langue
echo -e "\n${YELLOW}3. Ajout des traductions aux fichiers de langue${NC}"
echo "Voulez-vous ajouter les traductions du profil hors-ligne aux fichiers .po existants ? [y/N]"
read -r ADD_TRANSLATIONS

if [[ "$ADD_TRANSLATIONS" =~ ^[Yy]$ ]]; then
    # Parcourir les répertoires de langue
    for LANG_DIR in locale/*/LC_MESSAGES; do
        LANG=$(echo "$LANG_DIR" | cut -d'/' -f2)
        PO_FILE="$LANG_DIR/django.po"
        
        if [ -f "$PO_FILE" ]; then
            echo "Traitement de $PO_FILE pour la langue $LANG..."
            
            # Ajouter un en-tête pour les nouvelles traductions
            echo -e "\n# === Nouvelles traductions pour le profil hors-ligne ===" >> "$PO_FILE"
            echo -e "# Ajoutées automatiquement le $(date '+%Y-%m-%d %H:%M:%S')\n" >> "$PO_FILE"
            
            # Ajouter les traductions au fichier
            cat "$REFERENCE_FILE" >> "$PO_FILE"
            
            echo -e "${GREEN}✓ Traductions ajoutées pour $LANG${NC}"
        else
            echo -e "${YELLOW}⚠️  Fichier .po non trouvé pour $LANG${NC}"
        fi
    done
else
    echo "Vous devrez ajouter manuellement les traductions du fichier $REFERENCE_FILE à chaque fichier .po"
fi

# Étape 4: Compiler les messages
echo -e "\n${YELLOW}4. Compilation des messages${NC}"
python manage.py compilemessages
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Messages compilés avec succès${NC}"
else
    echo -e "${RED}✗ Erreur lors de la compilation des messages${NC}"
    exit 1
fi

echo -e "\n${GREEN}===== Compilation des traductions terminée =====${NC}"
echo "N'oubliez pas de redémarrer le serveur si nécessaire"