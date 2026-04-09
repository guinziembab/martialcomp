#!/bin/bash

# ============================================================================
# SCRIPT DE DÉPLOIEMENT - TEMPLATE PROFESSIONNEL DE MANAGEMENT
# Date: 2025-10-25
# Description: Déploie les modifications du template professionnel en production
# ============================================================================

set -e  # Arrêter en cas d'erreur

echo "🚀 DÉPLOIEMENT DU TEMPLATE PROFESSIONNEL DE MANAGEMENT"
echo "======================================================"
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="/home/martialcomp/martialcomp"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="$PROJECT_DIR/backups/template_pro_$(date +%Y%m%d_%H%M%S)"

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

# Vérifier qu'on est sur le serveur de production
if [ ! -d "$PROJECT_DIR" ]; then
    log_error "Répertoire du projet non trouvé: $PROJECT_DIR"
    log_warning "Ce script doit être exécuté sur le serveur de production"
    exit 1
fi

echo "📁 Répertoire du projet: $PROJECT_DIR"
echo ""

# Étape 1: Créer le répertoire de backup
echo "1️⃣  Création du répertoire de backup..."
mkdir -p "$BACKUP_DIR"
log_info "Répertoire de backup créé: $BACKUP_DIR"
echo ""

# Étape 2: Sauvegarder les fichiers actuels
echo "2️⃣  Sauvegarde des fichiers actuels..."
cd "$PROJECT_DIR"

FILES_TO_BACKUP=(
    "apps/competitions/views/club/competitions.py"
    "apps/competitions/views/club/event_organizer.py"
    "apps/competitions/urls/club.py"
    "apps/competitions/templates/competitions/club/competition_management_general.html"
    "apps/competitions/templates/competitions/club/competition_management_pro.html"
)

for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/$(basename $file).backup"
        log_info "Sauvegardé: $file"
    else
        log_warning "Fichier non trouvé: $file"
    fi
done
echo ""

# Étape 3: Vérifier l'environnement virtuel
echo "3️⃣  Vérification de l'environnement virtuel..."
if [ ! -d "$VENV_DIR" ]; then
    log_error "Environnement virtuel non trouvé: $VENV_DIR"
    exit 1
fi
log_info "Environnement virtuel trouvé"
echo ""

# Étape 4: Activer l'environnement virtuel
echo "4️⃣  Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"
log_info "Environnement virtuel activé"
echo ""

# Étape 5: Vérifier les dépendances
echo "5️⃣  Vérification des dépendances..."
python -c "import django; print(f'Django version: {django.get_version()}')"
log_info "Dépendances vérifiées"
echo ""

# Étape 6: Collecter les fichiers statiques
echo "6️⃣  Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
log_info "Fichiers statiques collectés"
echo ""

# Étape 7: Vérifier la configuration Django
echo "7️⃣  Vérification de la configuration Django..."
python manage.py check --deploy
if [ $? -eq 0 ]; then
    log_info "Configuration Django OK"
else
    log_warning "Avertissements de configuration détectés (non bloquants)"
fi
echo ""

# Étape 8: Redémarrer Gunicorn
echo "8️⃣  Redémarrage de Gunicorn..."
sudo systemctl restart gunicorn
if [ $? -eq 0 ]; then
    log_info "Gunicorn redémarré avec succès"
else
    log_error "Erreur lors du redémarrage de Gunicorn"
    exit 1
fi
echo ""

# Étape 9: Vérifier le statut de Gunicorn
echo "9️⃣  Vérification du statut de Gunicorn..."
sleep 3
sudo systemctl status gunicorn --no-pager | head -n 10
if sudo systemctl is-active --quiet gunicorn; then
    log_info "Gunicorn est actif"
else
    log_error "Gunicorn n'est pas actif"
    log_warning "Restauration des fichiers de backup..."
    for file in "${FILES_TO_BACKUP[@]}"; do
        if [ -f "$BACKUP_DIR/$(basename $file).backup" ]; then
            cp "$BACKUP_DIR/$(basename $file).backup" "$file"
        fi
    done
    sudo systemctl restart gunicorn
    exit 1
fi
echo ""

# Étape 10: Test de connexion
echo "🔟 Test de connexion au site..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/fr/competitions/club/competitions/management/)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    log_info "Site accessible (HTTP $HTTP_CODE)"
else
    log_warning "Code HTTP inattendu: $HTTP_CODE"
fi
echo ""

# Résumé
echo "=============================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
echo "=============================================="
echo ""
echo "📊 Résumé:"
echo "  - Fichiers sauvegardés dans: $BACKUP_DIR"
echo "  - Gunicorn: $(sudo systemctl is-active gunicorn)"
echo "  - Site: https://martialcomp.com"
echo ""
echo "🧪 URLs à tester:"
echo "  1. Liste des compétitions:"
echo "     https://martialcomp.com/fr/competitions/club/competitions/management/"
echo ""
echo "  2. Gestion détaillée (remplacer <id> par l'ID d'une compétition):"
echo "     https://martialcomp.com/fr/competitions/club/competitions/<id>/manage/"
echo ""
echo "📝 Logs Gunicorn:"
echo "  sudo journalctl -u gunicorn -f"
echo ""
echo "🔄 En cas de problème, restaurer avec:"
echo "  cd $PROJECT_DIR"
for file in "${FILES_TO_BACKUP[@]}"; do
    echo "  cp $BACKUP_DIR/$(basename $file).backup $file"
done
echo "  sudo systemctl restart gunicorn"
echo ""
log_info "Déploiement terminé !"
