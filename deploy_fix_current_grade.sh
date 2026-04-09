#!/bin/bash

# Script de déploiement pour corriger l'erreur current_grade
# Correction de l'erreur 500 sur la page d'inscription

echo "========================================"
echo "Déploiement du fix current_grade"
echo "========================================"

# Configuration
REMOTE_USER="root"
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

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
cp apps/competitions/templates/competitions/club/competition_registration_simple.html $TEMP_DIR/

# Créer l'archive
tar -czf fix_current_grade.tar.gz -C $TEMP_DIR .

echo -e "${GREEN}✓ Archive créée${NC}"

echo -e "${YELLOW}2. Transfert des fichiers vers la production...${NC}"
scp fix_current_grade.tar.gz $REMOTE_USER@$REMOTE_HOST:/tmp/

echo -e "${YELLOW}3. Application des modifications sur le serveur...${NC}"
ssh $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
    set -e
    
    # Variables
    REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
    BACKUP_DIR="$REMOTE_PATH/backups/fix_current_grade_$(date +%Y%m%d_%H%M%S)"
    
    echo "Création du répertoire de sauvegarde..."
    mkdir -p $BACKUP_DIR
    
    # Sauvegarder les fichiers existants
    echo "Sauvegarde des fichiers existants..."
    cp "$REMOTE_PATH/apps/competitions/views/club/registration_api.py" "$BACKUP_DIR/"
    cp "$REMOTE_PATH/apps/competitions/templates/competitions/club/competition_registration_simple.html" "$BACKUP_DIR/"
    
    # Extraire les nouveaux fichiers
    echo "Extraction des nouveaux fichiers..."
    cd /tmp
    tar -xzf fix_current_grade.tar.gz
    
    # Copier les fichiers
    echo "Copie des fichiers..."
    cp registration_api.py "$REMOTE_PATH/apps/competitions/views/club/"
    cp competition_registration_simple.html "$REMOTE_PATH/apps/competitions/templates/competitions/club/"
    
    # Ajuster les permissions
    echo "Ajustement des permissions..."
    chown -R www-data:www-data "$REMOTE_PATH/apps/competitions/views/club/registration_api.py"
    chown -R www-data:www-data "$REMOTE_PATH/apps/competitions/templates/competitions/club/competition_registration_simple.html"
    chmod 644 "$REMOTE_PATH/apps/competitions/views/club/registration_api.py"
    chmod 644 "$REMOTE_PATH/apps/competitions/templates/competitions/club/competition_registration_simple.html"
    
    # Compiler les fichiers Python
    echo "Compilation des fichiers Python..."
    cd $REMOTE_PATH
    python3 -m py_compile apps/competitions/views/club/registration_api.py || echo "Erreur de compilation"
    
    # Redémarrer le service
    echo "Redémarrage du service..."
    systemctl restart martialcomp.service || echo "Erreur restart service"
    
    # Vérifier le statut
    systemctl status martialcomp.service --no-pager | head -5
    
    # Nettoyer
    rm -f /tmp/fix_current_grade.tar.gz
    rm -f /tmp/registration_api.py
    rm -f /tmp/competition_registration_simple.html
    
    echo "✓ Déploiement terminé!"
ENDSSH

# Nettoyer les fichiers locaux
echo -e "${YELLOW}4. Nettoyage des fichiers temporaires...${NC}"
rm -rf $TEMP_DIR
rm -f fix_current_grade.tar.gz

echo -e "${GREEN}========================================"
echo -e "✓ DÉPLOIEMENT TERMINÉ!"
echo -e "========================================${NC}"

echo ""
echo "Correction appliquée:"
echo "- Remplacé 'current_grade' par 'grade' dans registration_api.py"
echo "- Remplacé 'current_grade' par 'grade' dans le template"

echo ""
echo -e "${YELLOW}L'erreur 500 devrait être corrigée${NC}"
echo "URL de test: https://martialcomp.com/fr/competitions/club/competition-registration/4/"