#!/bin/bash
# Script pour déployer les fichiers statiques CSS pour le profil hors-ligne

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

echo -e "${YELLOW}===== Déploiement des fichiers statiques pour le profil hors-ligne =====${NC}"

# Étape 1: Vérifier que les fichiers CSS existent
echo -e "\n${YELLOW}1. Vérification des fichiers CSS${NC}"
CSS_FILE="competitions/static/css/offline_profile.css"

if [ ! -f "$CSS_FILE" ]; then
    echo -e "${RED}Le fichier CSS $CSS_FILE n'existe pas.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Fichier CSS trouvé${NC}"

# Étape 2: Créer le répertoire de destination si nécessaire
echo -e "\n${YELLOW}2. Préparation du répertoire de destination${NC}"
STATIC_ROOT=$(python -c "from django.conf import settings; print(settings.STATIC_ROOT)" 2>/dev/null)

if [ -z "$STATIC_ROOT" ]; then
    # Si la commande échoue ou STATIC_ROOT est vide, utiliser le répertoire staticfiles par défaut
    STATIC_ROOT="staticfiles"
    echo "STATIC_ROOT non défini, utilisation de la valeur par défaut : $STATIC_ROOT"
fi

# Créer le répertoire css dans STATIC_ROOT s'il n'existe pas
CSS_DIR="$STATIC_ROOT/css"
if [ ! -d "$CSS_DIR" ]; then
    mkdir -p "$CSS_DIR"
    echo -e "${GREEN}✓ Répertoire $CSS_DIR créé${NC}"
else
    echo -e "${GREEN}✓ Répertoire $CSS_DIR existe déjà${NC}"
fi

# Étape 3: Copier les fichiers CSS
echo -e "\n${YELLOW}3. Copie des fichiers CSS${NC}"
cp -f "$CSS_FILE" "$CSS_DIR/offline_profile.css"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Fichier CSS copié avec succès${NC}"
else
    echo -e "${RED}✗ Erreur lors de la copie du fichier CSS${NC}"
    exit 1
fi

# Étape 4: Collecter tous les fichiers statiques
echo -e "\n${YELLOW}4. Collecte de tous les fichiers statiques${NC}"
python manage.py collectstatic --noinput
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Fichiers statiques collectés avec succès${NC}"
else
    echo -e "${RED}✗ Erreur lors de la collecte des fichiers statiques${NC}"
    exit 1
fi

# Étape 5: Vérifier la présence du fichier dans le répertoire statique final
echo -e "\n${YELLOW}5. Vérification du déploiement${NC}"
if [ -f "$STATIC_ROOT/css/offline_profile.css" ]; then
    echo -e "${GREEN}✓ Fichier CSS correctement déployé dans $STATIC_ROOT/css/offline_profile.css${NC}"
else
    echo -e "${RED}✗ Le fichier CSS n'a pas été déployé correctement${NC}"
    exit 1
fi

# Étape 6: Mise à jour des permissions si nécessaire
echo -e "\n${YELLOW}6. Mise à jour des permissions${NC}"
if [ -n "$(which nginx)" ] || [ -n "$(which apache2)" ]; then
    echo "Voulez-vous mettre à jour les permissions des fichiers statiques ? [y/N]"
    read -r UPDATE_PERMS
    
    if [[ "$UPDATE_PERMS" =~ ^[Yy]$ ]]; then
        # Détecter l'utilisateur du serveur web
        WEB_USER=""
        if [ -n "$(which nginx)" ]; then
            WEB_USER="www-data"  # Utilisateur par défaut pour Nginx
        elif [ -n "$(which apache2)" ]; then
            WEB_USER="www-data"  # Utilisateur par défaut pour Apache
        fi
        
        if [ -n "$WEB_USER" ]; then
            echo "Attribution des permissions à l'utilisateur $WEB_USER..."
            sudo chown -R "$WEB_USER:$WEB_USER" "$STATIC_ROOT"
            echo -e "${GREEN}✓ Permissions mises à jour${NC}"
        else
            echo "Impossible de déterminer l'utilisateur du serveur web."
        fi
    fi
fi

echo -e "\n${GREEN}===== Déploiement des fichiers statiques terminé =====${NC}"

# Étape 7: Instructions finales
echo -e "\n${YELLOW}7. Instructions finales${NC}"
echo "Pour finaliser le déploiement :"
echo "1. Assurez-vous que votre configuration Nginx/Apache pointe vers le répertoire $STATIC_ROOT"
echo "2. Redémarrez votre serveur web si nécessaire:"
echo "   - Nginx : sudo systemctl restart nginx"
echo "   - Apache : sudo systemctl restart apache2"