#!/bin/bash

# Script de déploiement pour corriger l'API d'inscription des compétitions
# Date: $(date)

echo "========================================"
echo "Déploiement du fix pour l'inscription aux compétitions"
echo "========================================"

# Configuration
REMOTE_USER="root"
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/martial_hub_django/martialcomp"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}1. Création de l'archive des fichiers à déployer...${NC}"

# Créer un répertoire temporaire
TEMP_DIR="temp_deploy_$(date +%Y%m%d_%H%M%S)"
mkdir -p $TEMP_DIR

# Copier les fichiers modifiés
echo "Copie des fichiers..."
cp apps/competitions/views/club/registration_api.py $TEMP_DIR/
cp apps/competitions/urls/club.py $TEMP_DIR/
cp apps/competitions/urls/competitions.py $TEMP_DIR/

# Créer l'archive
tar -czf fix_registration_api.tar.gz -C $TEMP_DIR .

echo -e "${GREEN}✓ Archive créée${NC}"

echo -e "${YELLOW}2. Transfert des fichiers vers la production...${NC}"
scp fix_registration_api.tar.gz $REMOTE_USER@$REMOTE_HOST:/tmp/

echo -e "${YELLOW}3. Application des modifications sur le serveur...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
    set -e
    
    # Variables
    REMOTE_PATH="/var/www/vhosts/martialcomp.com/martial_hub_django/martialcomp"
    BACKUP_DIR="$REMOTE_PATH/backups/fix_registration_$(date +%Y%m%d_%H%M%S)"
    
    echo "Création du répertoire de sauvegarde..."
    mkdir -p $BACKUP_DIR
    
    # Sauvegarder les fichiers existants
    echo "Sauvegarde des fichiers existants..."
    if [ -f "$REMOTE_PATH/apps/competitions/views/club/registration_api.py" ]; then
        cp "$REMOTE_PATH/apps/competitions/views/club/registration_api.py" "$BACKUP_DIR/" || true
    fi
    cp "$REMOTE_PATH/apps/competitions/urls/club.py" "$BACKUP_DIR/"
    cp "$REMOTE_PATH/apps/competitions/urls/competitions.py" "$BACKUP_DIR/"
    
    # Extraire les nouveaux fichiers
    echo "Extraction des nouveaux fichiers..."
    cd /tmp
    tar -xzf fix_registration_api.tar.gz
    
    # Créer le répertoire si nécessaire
    mkdir -p "$REMOTE_PATH/apps/competitions/views/club/"
    
    # Copier les fichiers
    echo "Copie des fichiers..."
    cp registration_api.py "$REMOTE_PATH/apps/competitions/views/club/"
    cp club.py "$REMOTE_PATH/apps/competitions/urls/"
    cp competitions.py "$REMOTE_PATH/apps/competitions/urls/"
    
    # Ajuster les permissions
    echo "Ajustement des permissions..."
    chown -R www-data:www-data "$REMOTE_PATH/apps/competitions/views/club/registration_api.py"
    chown -R www-data:www-data "$REMOTE_PATH/apps/competitions/urls/"
    chmod 644 "$REMOTE_PATH/apps/competitions/views/club/registration_api.py"
    chmod 644 "$REMOTE_PATH/apps/competitions/urls/club.py"
    chmod 644 "$REMOTE_PATH/apps/competitions/urls/competitions.py"
    
    # Compiler les fichiers Python
    echo "Compilation des fichiers Python..."
    cd $REMOTE_PATH
    python3 -m py_compile apps/competitions/views/club/registration_api.py
    python3 -m py_compile apps/competitions/urls/club.py
    python3 -m py_compile apps/competitions/urls/competitions.py
    
    # Collecter les fichiers statiques si nécessaire
    echo "Collection des fichiers statiques..."
    cd $REMOTE_PATH
    source ../venv/bin/activate
    python manage.py collectstatic --noinput
    
    # Redémarrer les services
    echo "Redémarrage des services..."
    systemctl restart gunicorn
    systemctl reload nginx
    
    # Nettoyer
    rm -f /tmp/fix_registration_api.tar.gz
    rm -f /tmp/registration_api.py
    rm -f /tmp/club.py
    rm -f /tmp/competitions.py
    
    echo "✓ Déploiement terminé avec succès!"
ENDSSH

# Nettoyer les fichiers locaux
echo -e "${YELLOW}4. Nettoyage des fichiers temporaires...${NC}"
rm -rf $TEMP_DIR
rm -f fix_registration_api.tar.gz

echo -e "${GREEN}========================================"
echo -e "✓ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo -e "========================================${NC}"

echo ""
echo "Actions effectuées:"
echo "- Création de l'API endpoint /competitions/{id}/api/categories/{type_id}/"
echo "- Mise à jour de la vue d'inscription simplifiée"
echo "- Ajout de la fonction de désinscription"
echo "- Mise à jour des routes URL"

echo ""
echo -e "${YELLOW}IMPORTANT: Veuillez tester l'inscription avec l'utilisateur SN_admin${NC}"
echo "URL de test: https://martialcomp.com/en/competitions/club/competition-registration/4/"