#!/bin/bash

# Script de déploiement des corrections pour la gestion des compétitions
# Date: 2025-11-14
# Problème résolu: Affichage "undefined" dans les types de compétition et manque d'inscrits dans les catégories

echo "=========================================="
echo "Déploiement des corrections - Competition Management"
echo "=========================================="
echo ""

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Vérifier qu'on est bien sur le serveur de production
if [ ! -d "/home/martialcomp" ]; then
    print_error "Ce script doit être exécuté sur le serveur de production"
    exit 1
fi

print_status "Connexion au serveur de production détectée"

# Se placer dans le répertoire du projet
cd /home/martialcomp/martialcomp || exit 1
print_status "Répertoire du projet: $(pwd)"

# Activer l'environnement virtuel
source venv/bin/activate
print_status "Environnement virtuel activé"

# Sauvegarder les fichiers actuels
BACKUP_DIR="backups/competition_management_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

print_status "Création du backup dans: $BACKUP_DIR"

# Backup des fichiers modifiés
cp apps/competitions/views/competition_management_pro.py "$BACKUP_DIR/" 2>/dev/null
cp apps/competitions/urls/club.py "$BACKUP_DIR/" 2>/dev/null
cp apps/competitions/templates/competitions/club/competition_management_detail.html "$BACKUP_DIR/" 2>/dev/null

print_status "Fichiers sauvegardés"

# Récupérer les dernières modifications depuis Git
print_status "Récupération des modifications depuis Git..."
git fetch origin

# Vérifier la branche actuelle
CURRENT_BRANCH=$(git branch --show-current)
print_warning "Branche actuelle: $CURRENT_BRANCH"

# Si on n'est pas sur la bonne branche, basculer
if [ "$CURRENT_BRANCH" != "fix/federation-dashboard" ]; then
    print_warning "Changement de branche vers fix/federation-dashboard"
    git stash
    git checkout fix/federation-dashboard
    git pull origin fix/federation-dashboard
fi

# Appliquer les modifications
print_status "Application des modifications..."

# Collecter les fichiers statiques
print_status "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Vérifier la syntaxe Python
print_status "Vérification de la syntaxe Python..."
python -m py_compile apps/competitions/views/competition_management_pro.py
if [ $? -eq 0 ]; then
    print_status "Syntaxe Python valide"
else
    print_error "Erreur de syntaxe Python détectée"
    exit 1
fi

# Vérifier les URLs
print_status "Vérification des URLs..."
python manage.py show_urls | grep -E "api_get_competition_types|api_get_competition_categories" > /dev/null
if [ $? -eq 0 ]; then
    print_status "URLs API correctement configurées"
else
    print_warning "URLs API non trouvées - vérification manuelle requise"
fi

# Redémarrer Gunicorn
print_status "Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn

# Attendre que le service redémarre
sleep 3

# Vérifier que Gunicorn est bien démarré
if sudo systemctl is-active --quiet gunicorn; then
    print_status "Gunicorn redémarré avec succès"
else
    print_error "Erreur lors du redémarrage de Gunicorn"
    print_warning "Tentative de restauration du backup..."
    
    # Restaurer les fichiers
    cp "$BACKUP_DIR/competition_management_pro.py" apps/competitions/views/ 2>/dev/null
    cp "$BACKUP_DIR/club.py" apps/competitions/urls/ 2>/dev/null
    cp "$BACKUP_DIR/competition_management_detail.html" apps/competitions/templates/competitions/club/ 2>/dev/null
    
    sudo systemctl restart gunicorn
    print_error "Backup restauré. Veuillez vérifier les logs."
    exit 1
fi

# Redémarrer Nginx (optionnel)
print_status "Rechargement de Nginx..."
sudo systemctl reload nginx

echo ""
echo "=========================================="
print_status "Déploiement terminé avec succès !"
echo "=========================================="
echo ""
echo "Modifications appliquées:"
echo "  ✓ Nouvelles APIs pour récupérer les types et catégories"
echo "  ✓ Affichage correct des catégories dans les types"
echo "  ✓ Affichage des inscrits dans les catégories (cliquable)"
echo ""
echo "URLs à tester:"
echo "  - https://martialcomp.com/en/competitions/club/competitions/4/manage/"
echo "  - Onglet 'Types of competition'"
echo "  - Onglet 'Catégories'"
echo ""
echo "Backup disponible dans: $BACKUP_DIR"
echo ""

# Afficher les logs récents
print_status "Dernières lignes des logs Gunicorn:"
sudo journalctl -u gunicorn -n 20 --no-pager

echo ""
print_warning "Veuillez vérifier manuellement que tout fonctionne correctement"
echo ""
