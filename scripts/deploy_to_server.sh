#!/bin/bash

################################################################################
# SCRIPT DE DÉPLOIEMENT VERS SERVEUR PRODUCTION
################################################################################

set -e

LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"
REMOTE_SERVER="martialcomp.com"
REMOTE_USER="your_username"  # À remplacer par votre nom d'utilisateur
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Créer un package de déploiement local
create_deployment_package() {
    info "📦 Création du package de déploiement..."
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local package_dir="/tmp/martialcomp_deployment_$timestamp"
    
    mkdir -p "$package_dir"
    
    # Copier les fichiers corrigés
    cp -r "$LOCAL_PATH/competitions/views/" "$package_dir/"
    cp -r "$LOCAL_PATH/competitions/templates/" "$package_dir/" 2>/dev/null || true
    cp "$LOCAL_PATH/config/settings.py" "$package_dir/" 2>/dev/null || true
    
    # Créer le script d'installation sur le serveur
    cat > "$package_dir/install_on_server.sh" << 'EOF'
#!/bin/bash

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/httpdocs/venv"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; exit 1; }
info() { echo -e "${BLUE}ℹ️ $1${NC}"; }

info "🚀 Installation des corrections sur le serveur..."

# Sauvegarde
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/tmp/backup_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

cp -r "$PRODUCTION_PATH/competitions/views/" "$BACKUP_DIR/" 2>/dev/null || true
cp "$PRODUCTION_PATH/config/settings.py" "$BACKUP_DIR/" 2>/dev/null || true

# Installation
info "📁 Installation des fichiers..."
cp -r views/* "$PRODUCTION_PATH/competitions/views/" 2>/dev/null || warning "Erreur copie views"
cp -r templates/* "$PRODUCTION_PATH/competitions/templates/" 2>/dev/null || warning "Erreur copie templates"
cp settings.py "$PRODUCTION_PATH/config/" 2>/dev/null || warning "Erreur copie settings"

# Redémarrage
info "🔄 Redémarrage Django..."
cd "$PRODUCTION_PATH"
source "$VENV_PATH/bin/activate" || error "Impossible d'activer venv"

pkill -f "python.*manage.py" || true
pkill -f "runserver" || true
pkill -f "gunicorn" || true
sleep 3

# Test configuration
if python manage.py check; then
    success "Configuration Django valide"
else
    error "Configuration Django invalide"
fi

# Démarrage
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_fixed.log 2>&1 &
sleep 5

if pgrep -f "runserver" > /dev/null; then
    success "🎉 Django redémarré avec succès"
    
    # Test rapide
    if curl -s -f "http://localhost:8000/" > /dev/null; then
        success "Site accessible"
    else
        warning "Site potentiellement inaccessible"
    fi
else
    error "Échec redémarrage Django"
fi

success "Installation terminée!"
info "Sauvegarde dans: $BACKUP_DIR"
EOF

    chmod +x "$package_dir/install_on_server.sh"
    
    # Créer l'archive
    cd /tmp
    tar -czf "martialcomp_fixes_$timestamp.tar.gz" "martialcomp_deployment_$timestamp"
    
    success "Package créé: /tmp/martialcomp_fixes_$timestamp.tar.gz"
    echo "/tmp/martialcomp_fixes_$timestamp.tar.gz" > /tmp/deployment_package_path
}

show_deployment_instructions() {
    local package_path=$(cat /tmp/deployment_package_path)
    
    info "📋 INSTRUCTIONS DE DÉPLOIEMENT"
    info "=============================="
    
    echo ""
    info "1. Transférer le package vers le serveur:"
    echo "   scp $package_path $REMOTE_USER@$REMOTE_SERVER:/tmp/"
    
    echo ""
    info "2. Se connecter au serveur:"
    echo "   ssh $REMOTE_USER@$REMOTE_SERVER"
    
    echo ""
    info "3. Extraire et installer sur le serveur:"
    echo "   cd /tmp"
    echo "   tar -xzf $(basename $package_path)"
    echo "   cd $(basename $package_path .tar.gz)"
    echo "   sudo ./install_on_server.sh"
    
    echo ""
    info "4. Tester les URLs:"
    echo "   • https://martialcomp.com/fr/competitions/practitioner/profile/"
    echo "   • https://martialcomp.com/fr/competitions/club/dashboard/"
    
    echo ""
    warning "ALTERNATIVE - Déploiement automatique (si SSH configuré):"
    echo "   ./deploy_to_server.sh --auto"
}

auto_deploy() {
    info "🚀 Déploiement automatique..."
    
    local package_path=$(cat /tmp/deployment_package_path)
    local package_name=$(basename $package_path)
    local extract_dir=$(basename $package_path .tar.gz)
    
    # Transférer
    info "📤 Transfert vers le serveur..."
    scp "$package_path" "$REMOTE_USER@$REMOTE_SERVER:/tmp/" || error "Erreur transfert"
    
    # Installer
    info "⚙️ Installation sur le serveur..."
    ssh "$REMOTE_USER@$REMOTE_SERVER" "cd /tmp && tar -xzf $package_name && cd $extract_dir && sudo ./install_on_server.sh" || error "Erreur installation"
    
    success "🎉 Déploiement automatique terminé!"
}

main() {
    info "🚀 PRÉPARATION DÉPLOIEMENT PRODUCTION"
    info "===================================="
    
    create_deployment_package
    
    if [[ "$1" == "--auto" ]]; then
        auto_deploy
    else
        show_deployment_instructions
    fi
}

main "$@"