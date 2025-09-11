#!/bin/bash

# Script de Démarrage Rapide - Synchronisation Dev → Production
# MartialComp - Lancement Automatique du Workflow Complet

set -e

# Configuration
PROJECT_NAME="martialcomp"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction d'affichage du menu
show_menu() {
    echo
    echo "=== SYNC WORKFLOW - MARTIALCOMP ==="
    echo
    echo "Choisissez une option:"
    echo
    echo "1. 🔍 Diagnostic complet (recommandé en premier)"
    echo "2. 🧹 Nettoyage complet de la production"
    echo "3. 🔄 Synchronisation complète dev → production"
    echo "4. 🚀 Workflow complet (diagnostic + sync)"
    echo "5. 📋 Lister les éléments à conserver"
    echo "6. 🔙 Rollback (en cas de problème)"
    echo "7. 📊 Vérifier l'état actuel"
    echo "8. ❌ Quitter"
    echo
}

# Fonction de diagnostic
run_diagnostic() {
    log "=== LANCEMENT DU DIAGNOSTIC ==="
    
    if [ -f "diagnostic_pre_sync.sh" ]; then
        bash diagnostic_pre_sync.sh
    else
        error "Script de diagnostic non trouvé"
        return 1
    fi
}

# Fonction de nettoyage
run_cleanup() {
    log "=== LANCEMENT DU NETTOYAGE ==="
    
    if [ -f "clean_production_complete.sh" ]; then
        echo
        warning "ATTENTION: Cette opération va nettoyer complètement la production"
        echo "Un backup sera créé automatiquement"
        echo
        read -p "Continuer? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            bash clean_production_complete.sh clean-complete
        else
            log "Nettoyage annulé"
        fi
    else
        error "Script de nettoyage non trouvé"
        return 1
    fi
}

# Fonction de synchronisation
run_sync() {
    log "=== LANCEMENT DE LA SYNCHRONISATION ==="
    
    if [ -f "sync_dev_to_production_final.sh" ]; then
        bash sync_dev_to_production_final.sh
    else
        error "Script de synchronisation non trouvé"
        return 1
    fi
}

# Fonction de workflow complet
run_complete_workflow() {
    log "=== LANCEMENT DU WORKFLOW COMPLET ==="
    
    if [ -f "execute_sync_workflow.sh" ]; then
        bash execute_sync_workflow.sh
    else
        error "Script de workflow complet non trouvé"
        return 1
    fi
}

# Fonction de liste des éléments
list_elements() {
    log "=== LISTE DES ÉLÉMENTS À CONSERVER ==="
    
    if [ -f "clean_production_complete.sh" ]; then
        bash clean_production_complete.sh list
    else
        echo "📁 ÉLÉMENTS À CONSERVER:"
        echo "  - config/production.py"
        echo "  - production.env"
        echo "  - vhost.conf"
        echo "  - media/"
        echo "  - uploads/"
        echo "  - logs/"
        echo "  - backups/"
        echo "  - *.sh"
        echo "  - *.sql"
    fi
}

# Fonction de rollback
run_rollback() {
    log "=== ROLLBACK ==="
    
    if [ -f "rollback_production.sh" ]; then
        echo
        echo "Options de rollback:"
        echo "1. Lister les backups disponibles"
        echo "2. Restauration complète"
        echo "3. Restauration du code uniquement"
        echo "4. Restauration de la base de données uniquement"
        echo "5. Test après restauration"
        echo "6. Retour au menu principal"
        echo
        read -p "Choisissez une option (1-6): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                bash rollback_production.sh list
                ;;
            2)
                read -p "Date du backup (ex: 20250630_212938): " backup_date
                bash rollback_production.sh complete "$backup_date"
                ;;
            3)
                read -p "Date du backup (ex: 20250630_212938): " backup_date
                bash rollback_production.sh code "$backup_date"
                ;;
            4)
                read -p "Date du backup (ex: 20250630_212938): " backup_date
                bash rollback_production.sh db "$backup_date"
                ;;
            5)
                bash rollback_production.sh test
                ;;
            6)
                return
                ;;
            *)
                error "Option invalide"
                ;;
        esac
    else
        error "Script de rollback non trouvé"
        return 1
    fi
}

# Fonction de vérification d'état
check_status() {
    log "=== VÉRIFICATION DE L'ÉTAT ACTUEL ==="
    
    echo
    echo "📊 ÉTAT DES SCRIPTS:"
    
    local scripts=(
        "diagnostic_pre_sync.sh"
        "clean_production_complete.sh"
        "sync_dev_to_production_final.sh"
        "execute_sync_workflow.sh"
        "rollback_production.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                success "$script - ✅ Disponible et exécutable"
            else
                warning "$script - ⚠️  Disponible mais non exécutable"
            fi
        else
            error "$script - ❌ Manquant"
        fi
    done
    
    echo
    echo "📊 ÉTAT DE L'ENVIRONNEMENT LOCAL:"
    
    # Vérification de Django
    if python -c "import django" 2>/dev/null; then
        success "Django - ✅ Installé"
    else
        error "Django - ❌ Non installé"
    fi
    
    # Vérification de manage.py
    if [ -f "manage.py" ]; then
        success "manage.py - ✅ Présent"
    else
        error "manage.py - ❌ Manquant"
    fi
    
    # Vérification des outils
    local tools=("ssh" "rsync" "curl")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            success "$tool - ✅ Disponible"
        else
            error "$tool - ❌ Non installé"
        fi
    done
    
    echo
    echo "📊 ÉTAT DE LA PRODUCTION:"
    
    # Test de connectivité
    if ssh -o ConnectTimeout=5 root@martialcomp.com "echo 'OK'" > /dev/null 2>&1; then
        success "Connexion SSH - ✅ Établie"
    else
        error "Connexion SSH - ❌ Échec"
    fi
    
    # Test du site web
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com | grep -q "200\|302"; then
        success "Site web - ✅ Accessible"
    else
        warning "Site web - ⚠️  Problème d'accessibilité"
    fi
}

# Fonction principale
main() {
    while true; do
        show_menu
        read -p "Votre choix (1-8): " -n 1 -r
        echo
        
        case $REPLY in
            1)
                run_diagnostic
                ;;
            2)
                run_cleanup
                ;;
            3)
                run_sync
                ;;
            4)
                run_complete_workflow
                ;;
            5)
                list_elements
                ;;
            6)
                run_rollback
                ;;
            7)
                check_status
                ;;
            8)
                log "Au revoir!"
                exit 0
                ;;
            *)
                error "Option invalide"
                ;;
        esac
        
        echo
        read -p "Appuyez sur Entrée pour continuer..."
    done
}

# Vérification des prérequis
check_prerequisites() {
    log "=== VÉRIFICATION DES PRÉREQUIS ==="
    
    # Vérification de la présence des scripts
    local required_scripts=(
        "diagnostic_pre_sync.sh"
        "clean_production_complete.sh"
        "sync_dev_to_production_final.sh"
        "execute_sync_workflow.sh"
        "rollback_production.sh"
    )
    
    local missing_scripts=()
    
    for script in "${required_scripts[@]}"; do
        if [ ! -f "$script" ]; then
            missing_scripts+=("$script")
        fi
    done
    
    if [ ${#missing_scripts[@]} -gt 0 ]; then
        warning "Scripts manquants:"
        for script in "${missing_scripts[@]}"; do
            echo "  - $script"
        done
        echo
        echo "Assurez-vous que tous les scripts sont présents avant de continuer."
        echo
    else
        success "Tous les scripts requis sont présents"
    fi
    
    # Rendre les scripts exécutables
    chmod +x *.sh 2>/dev/null || true
}

# Exécution du script principal
check_prerequisites
main "$@" 