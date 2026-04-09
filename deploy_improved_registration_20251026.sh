#!/bin/bash

# Script de déploiement de l'interface d'inscription améliorée
# Date: 2025-10-26
# Objectif: Déployer le système d'inscription en 3 étapes avec filtres cohérents

echo "=========================================="
echo "Déploiement de l'interface d'inscription améliorée"
echo "=========================================="

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Connexion SSH
SERVER="martialcomp-production"
REMOTE_DIR="/home/martialcomp/martialcomp"

echo -e "${BLUE}Étape 1: Connexion au serveur de production...${NC}"

# Créer un répertoire temporaire pour les fichiers à transférer
TEMP_DIR=$(mktemp -d)
echo "Répertoire temporaire: $TEMP_DIR"

# Copier les fichiers modifiés
echo -e "${BLUE}Étape 2: Préparation des fichiers...${NC}"

# Template d'inscription amélioré
mkdir -p "$TEMP_DIR/templates/competitions/club"
cp "apps/competitions/templates/competitions/club/competition_registration_form.html" "$TEMP_DIR/templates/competitions/club/"

# Vues modifiées
mkdir -p "$TEMP_DIR/views/club"
cp "apps/competitions/views/club/registrations.py" "$TEMP_DIR/views/club/"
cp "apps/competitions/views/club/competitions.py" "$TEMP_DIR/views/club/"

# URLs modifiées
mkdir -p "$TEMP_DIR/urls"
cp "apps/competitions/urls/club.py" "$TEMP_DIR/urls/"

echo -e "${GREEN}✓ Fichiers préparés${NC}"

# Transférer les fichiers
echo -e "${BLUE}Étape 3: Transfert des fichiers vers le serveur...${NC}"

ssh $SERVER << 'ENDSSH'
    cd /home/martialcomp/martialcomp
    
    # Créer une sauvegarde
    echo "Création d'une sauvegarde..."
    BACKUP_DIR="backups/registration_$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    # Sauvegarder les fichiers existants
    cp apps/competitions/templates/competitions/club/competition_registration_form.html $BACKUP_DIR/ 2>/dev/null || true
    cp apps/competitions/views/club/registrations.py $BACKUP_DIR/ 2>/dev/null || true
    cp apps/competitions/views/club/competitions.py $BACKUP_DIR/ 2>/dev/null || true
    cp apps/competitions/urls/club.py $BACKUP_DIR/ 2>/dev/null || true
    
    echo "✓ Sauvegarde créée dans $BACKUP_DIR"
ENDSSH

# Copier les nouveaux fichiers
echo -e "${BLUE}Copie des nouveaux fichiers...${NC}"
scp -r "$TEMP_DIR/templates/competitions/club/competition_registration_form.html" \
    "$SERVER:$REMOTE_DIR/apps/competitions/templates/competitions/club/"

scp -r "$TEMP_DIR/views/club/registrations.py" \
    "$SERVER:$REMOTE_DIR/apps/competitions/views/club/"

scp -r "$TEMP_DIR/views/club/competitions.py" \
    "$SERVER:$REMOTE_DIR/apps/competitions/views/club/"

scp -r "$TEMP_DIR/urls/club.py" \
    "$SERVER:$REMOTE_DIR/apps/competitions/urls/"

echo -e "${GREEN}✓ Fichiers transférés${NC}"

# Redémarrer les services
echo -e "${BLUE}Étape 4: Redémarrage des services...${NC}"

ssh $SERVER << 'ENDSSH'
    cd /home/martialcomp/martialcomp
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Collecter les fichiers statiques
    echo "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    
    # Redémarrer Gunicorn
    echo "Redémarrage de Gunicorn..."
    sudo systemctl restart gunicorn
    
    # Vérifier le statut
    sleep 2
    if sudo systemctl is-active --quiet gunicorn; then
        echo "✓ Gunicorn redémarré avec succès"
    else
        echo "✗ Erreur lors du redémarrage de Gunicorn"
        sudo systemctl status gunicorn
        exit 1
    fi
    
    # Redémarrer Nginx
    echo "Redémarrage de Nginx..."
    sudo systemctl restart nginx
    
    if sudo systemctl is-active --quiet nginx; then
        echo "✓ Nginx redémarré avec succès"
    else
        echo "✗ Erreur lors du redémarrage de Nginx"
        sudo systemctl status nginx
        exit 1
    fi
ENDSSH

# Nettoyer le répertoire temporaire
rm -rf "$TEMP_DIR"

echo ""
echo -e "${GREEN}=========================================="
echo "Déploiement terminé avec succès !"
echo "==========================================${NC}"
echo ""
echo "Changements déployés:"
echo "  ✓ Nouveau système d'inscription en 3 étapes"
echo "  ✓ Filtres de genre cohérents (Homme/Femme)"
echo "  ✓ Interface drag & drop améliorée"
echo "  ✓ API pour récupérer les catégories par type"
echo ""
echo "URL de test: https://martialcomp.com/fr/competitions/competitions/4/"
echo ""
echo -e "${BLUE}Prochaines étapes:${NC}"
echo "  1. Tester l'inscription d'un pratiquant"
echo "  2. Vérifier les filtres de genre"
echo "  3. Tester le drag & drop"
echo ""
