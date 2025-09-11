#!/bin/bash

################################################################################
# SCRIPT DE DÉPLOIEMENT CORRIGÉ - MARTIALCOMP PRODUCTION
################################################################################

set -e

PACKAGE_PATH="/tmp/martialcomp_fixes_20250623_172300.tar.gz"
REMOTE_SERVER="martialcomp.com"
REMOTE_USER="root"  # Ou votre nom d'utilisateur SSH

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

verify_package() {
    info "🔍 Vérification du package..."
    
    if [ ! -f "$PACKAGE_PATH" ]; then
        error "Package non trouvé: $PACKAGE_PATH"
    fi
    
    # Vérifier le contenu
    local files_count=$(tar -tzf "$PACKAGE_PATH" | wc -l)
    info "Package contient $files_count fichiers"
    
    # Vérifier les fichiers critiques
    if tar -tzf "$PACKAGE_PATH" | grep -q "install_on_server.sh"; then
        success "Script d'installation trouvé"
    else
        error "Script d'installation manquant"
    fi
    
    if tar -tzf "$PACKAGE_PATH" | grep -q "views/__init__.py"; then
        success "Fichier views/__init__.py trouvé"
    else
        error "Fichier views/__init__.py manquant"
    fi
}

show_deployment_commands() {
    info "📋 COMMANDES DE DÉPLOIEMENT"
    info "=========================="
    
    echo ""
    info "Option 1 - Transfert SCP puis installation manuelle:"
    echo "────────────────────────────────────────────────────"
    echo "# 1. Transférer le package"
    echo "scp $PACKAGE_PATH $REMOTE_USER@$REMOTE_SERVER:/tmp/"
    echo ""
    echo "# 2. Se connecter au serveur"
    echo "ssh $REMOTE_USER@$REMOTE_SERVER"
    echo ""
    echo "# 3. Installer sur le serveur"
    echo "cd /tmp"
    echo "tar -xzf $(basename $PACKAGE_PATH)"
    echo "cd $(basename $PACKAGE_PATH .tar.gz)"
    echo "chmod +x install_on_server.sh"
    echo "sudo ./install_on_server.sh"
    
    echo ""
    info "Option 2 - Installation directe (si SSH configuré):"
    echo "───────────────────────────────────────────────────"
    echo "./deploy_corrected.sh --auto"
    
    echo ""
    info "Option 3 - Commande unique (copier-coller):"
    echo "────────────────────────────────────────────────"
    echo "scp $PACKAGE_PATH $REMOTE_USER@$REMOTE_SERVER:/tmp/ && ssh $REMOTE_USER@$REMOTE_SERVER 'cd /tmp && tar -xzf $(basename $PACKAGE_PATH) && cd $(basename $PACKAGE_PATH .tar.gz) && chmod +x install_on_server.sh && sudo ./install_on_server.sh'"
}

auto_deploy() {
    info "🚀 Déploiement automatique..."
    
    local package_name=$(basename $PACKAGE_PATH)
    local extract_dir=$(basename $PACKAGE_PATH .tar.gz)
    
    # Étape 1: Transfert
    info "📤 Transfert vers $REMOTE_SERVER..."
    if scp "$PACKAGE_PATH" "$REMOTE_USER@$REMOTE_SERVER:/tmp/"; then
        success "Transfert réussi"
    else
        error "Échec du transfert SCP"
    fi
    
    # Étape 2: Installation
    info "⚙️ Installation sur le serveur..."
    if ssh "$REMOTE_USER@$REMOTE_SERVER" "cd /tmp && tar -xzf $package_name && cd $extract_dir && chmod +x install_on_server.sh && sudo ./install_on_server.sh"; then
        success "Installation réussie"
    else
        error "Échec de l'installation"
    fi
    
    # Étape 3: Test
    info "🧪 Test de l'accès..."
    sleep 10
    
    if curl -s -f "https://martialcomp.com/" > /dev/null; then
        success "Site accessible"
    else
        warning "Site potentiellement inaccessible"
    fi
}

test_ssh_connection() {
    info "🔗 Test de connexion SSH..."
    
    if ssh -o ConnectTimeout=10 "$REMOTE_USER@$REMOTE_SERVER" "echo 'Connexion SSH OK'"; then
        success "Connexion SSH fonctionnelle"
        return 0
    else
        warning "Connexion SSH échoue"
        return 1
    fi
}

show_manual_instructions() {
    info "📝 INSTRUCTIONS MANUELLES DÉTAILLÉES"
    info "==================================="
    
    echo ""
    echo "Si le déploiement automatique ne fonctionne pas, suivez ces étapes:"
    echo ""
    echo "1. 📁 Copier le fichier vers le serveur:"
    echo "   - Utilisez FileZilla, WinSCP ou scp"
    echo "   - Source: $PACKAGE_PATH"
    echo "   - Destination: /tmp/ sur le serveur"
    echo ""
    echo "2. 🔧 Sur le serveur, exécuter:"
    echo "   cd /tmp"
    echo "   tar -xzf $(basename $PACKAGE_PATH)"
    echo "   cd $(basename $PACKAGE_PATH .tar.gz)"
    echo "   chmod +x install_on_server.sh"
    echo "   sudo ./install_on_server.sh"
    echo ""
    echo "3. ✅ URLs à tester après installation:"
    echo "   • https://martialcomp.com/"
    echo "   • https://martialcomp.com/fr/competitions/practitioner/profile/"
    echo "   • https://martialcomp.com/fr/competitions/club/dashboard/"
}

main() {
    info "🚀 DÉPLOIEMENT MARTIALCOMP - VERSION CORRIGÉE"
    info "============================================="
    
    verify_package
    
    case "${1:-manual}" in
        "--auto"|"-a")
            if test_ssh_connection; then
                auto_deploy
            else
                warning "SSH non configuré - affichage des instructions manuelles"
                show_deployment_commands
            fi
            ;;
        "--test"|"-t")
            test_ssh_connection
            ;;
        *)
            show_deployment_commands
            echo ""
            show_manual_instructions
            ;;
    esac
    
    echo ""
    success "🎯 PRÊT POUR LE DÉPLOIEMENT"
    info "Package vérifié: $PACKAGE_PATH"
    info "Taille: $(du -h $PACKAGE_PATH | cut -f1)"
}

main "$@"