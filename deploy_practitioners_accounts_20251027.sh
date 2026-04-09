#!/bin/bash
# Script de déploiement - Gestion des comptes pratiquants
# Date: 27 octobre 2025
# Fonctionnalités: Création automatique de comptes + Association comptes existants

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "DÉPLOIEMENT - Gestion Comptes Pratiquants"
echo "=========================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REMOTE_USER="martialcomp-production"
REMOTE_HOST="martialcomp-production"
REMOTE_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${YELLOW}📦 Étape 1/6 : Préparation des fichiers locaux${NC}"
echo "-------------------------------------------"

# Vérifier que les fichiers existent
if [ ! -f "apps/competitions/views/club/practitioners.py" ]; then
    echo -e "${RED}❌ Erreur : Le fichier practitioners.py n'existe pas${NC}"
    exit 1
fi

if [ ! -f "apps/competitions/templates/competitions/club/create_user_form.html" ]; then
    echo -e "${RED}❌ Erreur : Le template create_user_form.html n'existe pas${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Fichiers locaux vérifiés${NC}"
echo ""

echo -e "${YELLOW}📋 Étape 2/6 : Création du backup en production${NC}"
echo "-------------------------------------------"

# Créer le répertoire de backup si nécessaire
ssh $REMOTE_USER "mkdir -p $BACKUP_DIR"

# Backup du fichier practitioners.py
ssh $REMOTE_USER "if [ -f $REMOTE_DIR/apps/competitions/views/club/practitioners.py ]; then \
    cp $REMOTE_DIR/apps/competitions/views/club/practitioners.py \
    $BACKUP_DIR/practitioners_${TIMESTAMP}.py.bak; \
    echo 'Backup de practitioners.py créé'; \
fi"

echo -e "${GREEN}✅ Backup créé : practitioners_${TIMESTAMP}.py.bak${NC}"
echo ""

echo -e "${YELLOW}📤 Étape 3/6 : Transfert des fichiers vers la production${NC}"
echo "-------------------------------------------"

# Transférer le fichier practitioners.py
echo "Transfert de practitioners.py..."
scp apps/competitions/views/club/practitioners.py \
    $REMOTE_USER:$REMOTE_DIR/apps/competitions/views/club/practitioners.py

# Transférer le template create_user_form.html
echo "Transfert de create_user_form.html..."
scp apps/competitions/templates/competitions/club/create_user_form.html \
    $REMOTE_USER:$REMOTE_DIR/apps/competitions/templates/competitions/club/create_user_form.html

echo -e "${GREEN}✅ Fichiers transférés avec succès${NC}"
echo ""

echo -e "${YELLOW}🔧 Étape 4/6 : Ajustement des permissions${NC}"
echo "-------------------------------------------"

ssh $REMOTE_USER "cd $REMOTE_DIR && \
    chown www-data:www-data apps/competitions/views/club/practitioners.py && \
    chmod 755 apps/competitions/views/club/practitioners.py && \
    chown www-data:www-data apps/competitions/templates/competitions/club/create_user_form.html && \
    chmod 644 apps/competitions/templates/competitions/club/create_user_form.html"

echo -e "${GREEN}✅ Permissions ajustées${NC}"
echo ""

echo -e "${YELLOW}🔄 Étape 5/6 : Redémarrage des services${NC}"
echo "-------------------------------------------"

# Redémarrer Gunicorn/uWSGI (selon la configuration)
ssh $REMOTE_USER "cd $REMOTE_DIR && \
    if [ -f tmp/restart.txt ]; then \
        touch tmp/restart.txt; \
        echo 'Application redémarrée (Passenger)'; \
    elif systemctl is-active --quiet gunicorn; then \
        sudo systemctl restart gunicorn; \
        echo 'Gunicorn redémarré'; \
    elif systemctl is-active --quiet uwsgi; then \
        sudo systemctl restart uwsgi; \
        echo 'uWSGI redémarré'; \
    else \
        echo 'Aucun service à redémarrer trouvé'; \
    fi"

echo -e "${GREEN}✅ Services redémarrés${NC}"
echo ""

echo -e "${YELLOW}✅ Étape 6/6 : Vérification du déploiement${NC}"
echo "-------------------------------------------"

# Vérifier que les fichiers existent en production
ssh $REMOTE_USER "cd $REMOTE_DIR && \
    if [ -f apps/competitions/views/club/practitioners.py ]; then \
        echo '✓ practitioners.py présent'; \
    else \
        echo '✗ practitioners.py MANQUANT'; \
        exit 1; \
    fi && \
    if [ -f apps/competitions/templates/competitions/club/create_user_form.html ]; then \
        echo '✓ create_user_form.html présent'; \
    else \
        echo '✗ create_user_form.html MANQUANT'; \
        exit 1; \
    fi"

echo ""
echo -e "${GREEN}=========================================="
echo "✅ DÉPLOIEMENT RÉUSSI !"
echo "==========================================${NC}"
echo ""
echo "📝 Résumé des modifications :"
echo "   • Fichier mis à jour : practitioners.py"
echo "   • Template ajouté : create_user_form.html"
echo "   • Backup créé : $BACKUP_DIR/practitioners_${TIMESTAMP}.py.bak"
echo ""
echo "🎯 Nouvelles fonctionnalités disponibles :"
echo "   1. Création automatique de compte avec mot de passe aléatoire"
echo "   2. Envoi d'email d'invitation avec identifiants"
echo "   3. Association de compte existant à un pratiquant"
echo ""
echo "📍 URLs actives :"
echo "   • /club/practitioners/<id>/create-user/"
echo "   • /club/practitioners/<id>/link-user/"
echo ""
echo -e "${YELLOW}⚠️  Note : Vérifiez que les URLs sont bien configurées dans urls/club.py${NC}"
echo ""
