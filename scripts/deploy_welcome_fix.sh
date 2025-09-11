#!/bin/bash

# Script de déploiement rapide pour la correction du fichier welcome.html
# Usage: ./deploy_welcome_fix.sh

set -e

# Configuration
PROJECT_NAME="martialcomp"
PROJECT_DIR="/var/www/martialcomp"
VENV_DIR="/var/www/martialcomp/venv"
USER="www-data"
GROUP="www-data"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérification des prérequis
check_prerequisites() {
    log_info "Vérification des prérequis..."
    
    # Vérifier si on est root ou sudo
    if [[ $EUID -eq 0 ]]; then
        log_error "Ce script ne doit pas être exécuté en tant que root"
        exit 1
    fi
    
    # Vérifier que le projet existe
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Le projet n'existe pas dans $PROJECT_DIR"
        exit 1
    fi
    
    log_success "Prérequis vérifiés"
}

# Sauvegarde du fichier actuel
create_backup() {
    log_info "Création de la sauvegarde du fichier welcome.html..."
    
    local backup_dir="$PROJECT_DIR/backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local welcome_file="$PROJECT_DIR/competitions/templates/competitions/welcome.html"
    
    # Créer le dossier de sauvegarde
    sudo mkdir -p "$backup_dir"
    
    # Sauvegarde du fichier welcome.html
    if [ -f "$welcome_file" ]; then
        sudo cp "$welcome_file" "$backup_dir/welcome_backup_$timestamp.html"
        log_success "Sauvegarde créée: welcome_backup_$timestamp.html"
    else
        log_warning "Fichier welcome.html non trouvé, pas de sauvegarde"
    fi
}

# Copie du fichier corrigé
deploy_welcome_fix() {
    log_info "Déploiement de la correction du fichier welcome.html..."
    
    local source_file="competitions/templates/competitions/welcome.html"
    local target_file="$PROJECT_DIR/competitions/templates/competitions/welcome.html"
    
    # Vérifier que le fichier source existe
    if [ ! -f "$source_file" ]; then
        log_error "Fichier source $source_file non trouvé"
        exit 1
    fi
    
    # Copier le fichier corrigé
    sudo cp "$source_file" "$target_file"
    sudo chown $USER:$GROUP "$target_file"
    sudo chmod 644 "$target_file"
    
    log_success "Fichier welcome.html déployé"
}

# Collecte des fichiers statiques
collect_static() {
    log_info "Collecte des fichiers statiques..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Collecter les fichiers statiques
    python manage.py collectstatic --noinput --clear
    
    # Définir les permissions
    sudo chown -R $USER:$GROUP "$PROJECT_DIR/static"
    sudo chmod -R 755 "$PROJECT_DIR/static"
    
    log_success "Fichiers statiques collectés"
}

# Redémarrage des services
restart_services() {
    log_info "Redémarrage des services..."
    
    # Redémarrer l'application
    sudo systemctl restart martialcomp
    
    # Redémarrer Nginx
    sudo systemctl restart nginx
    
    # Vérifier l'état des services
    sudo systemctl status martialcomp --no-pager
    sudo systemctl status nginx --no-pager
    
    log_success "Services redémarrés"
}

# Tests de santé
health_check() {
    log_info "Vérification de la santé de l'application..."
    
    # Attendre que l'application démarre
    sleep 3
    
    # Test de connectivité
    if curl -f http://localhost:8000/fr/ > /dev/null 2>&1; then
        log_success "Application accessible"
    else
        log_error "Application non accessible"
        return 1
    fi
    
    log_success "Test de santé réussi"
}

# Fonction principale
main() {
    echo "🚀 Déploiement de la correction welcome.html - Production"
    echo "========================================================"
    
    check_prerequisites
    create_backup
    deploy_welcome_fix
    collect_static
    restart_services
    health_check
    
    echo ""
    echo "🎉 Déploiement terminé avec succès !"
    echo "🌐 Application accessible sur: https://martialcomp.com"
    echo "📊 Monitoring: sudo systemctl status martialcomp"
    echo "📝 Logs: sudo tail -f $PROJECT_DIR/logs/django.log"
}

# Gestion des erreurs
trap 'log_error "Déploiement interrompu"; exit 1' INT TERM

# Exécution
main "$@" 