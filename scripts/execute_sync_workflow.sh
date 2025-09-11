#!/bin/bash

# Script d'Exécution du Workflow de Synchronisation
# MartialComp - Orchestration Complète Dev → Production

set -e

# Configuration
PROJECT_NAME="martialcomp"
PROD_USER="root"
PROD_HOST="martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com"
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

# Fonction de vérification des prérequis
check_prerequisites() {
    log "=== VÉRIFICATION DES PRÉREQUIS ==="
    
    # Vérification des outils nécessaires
    local tools=("ssh" "rsync" "curl" "python")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            success "$tool disponible"
        else
            error "$tool n'est pas installé"
            return 1
        fi
    done
    
    # Vérification de la structure du projet
    if [ ! -f "manage.py" ]; then
        error "manage.py non trouvé - exécutez ce script depuis la racine du projet"
        return 1
    fi
    
    # Vérification de l'environnement Python
    if ! python -c "import django" 2>/dev/null; then
        error "Django n'est pas installé dans l'environnement Python"
        return 1
    fi
    
    success "Tous les prérequis sont satisfaits"
}

# Fonction de diagnostic préalable
run_pre_diagnostic() {
    log "=== DIAGNOSTIC PRÉALABLE ==="
    
    # Exécution du script de diagnostic
    if [ -f "diagnostic_pre_sync.sh" ]; then
        log "Exécution du diagnostic préalable..."
        bash diagnostic_pre_sync.sh
    else
        warning "Script de diagnostic non trouvé, création d'un diagnostic basique..."
        
        # Diagnostic basique
        log "Test de connectivité vers la production..."
        if ssh -o ConnectTimeout=10 $PROD_USER@$PROD_HOST "echo 'Connexion OK'" > /dev/null 2>&1; then
            success "Connexion à la production établie"
        else
            error "Impossible de se connecter à la production"
            return 1
        fi
        
        # Vérification de l'espace disque
        log "Vérification de l'espace disque..."
        local space=$(ssh $PROD_USER@$PROD_HOST "df / | tail -1 | awk '{print \$5}' | sed 's/%//'")
        if [ "$space" -gt 90 ]; then
            warning "Espace disque critique: ${space}% utilisé"
            echo "Nettoyage recommandé avant de continuer"
            read -p "Continuer malgré l'espace disque limité? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                return 1
            fi
        else
            success "Espace disque OK: ${space}% utilisé"
        fi
    fi
}

# Fonction de confirmation utilisateur
get_user_confirmation() {
    echo
    log "=== CONFIRMATION DE SYNCHRONISATION ==="
    echo
    echo "Résumé de la synchronisation:"
    echo "  - Source: Environnement de développement local"
    echo "  - Destination: $PROD_HOST:$PROD_PATH"
    echo "  - Timestamp: $TIMESTAMP"
    echo
    echo "Cette opération va:"
    echo "  1. Synchroniser le code source"
    echo "  2. Synchroniser la base de données"
    echo "  3. Synchroniser les fichiers statiques"
    echo "  4. Reconfigurer les services"
    echo "  5. Effectuer des tests de validation"
    echo
    warning "ATTENTION: Cette opération va modifier l'environnement de production"
    echo
    read -p "Êtes-vous sûr de vouloir continuer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Synchronisation annulée par l'utilisateur"
        exit 0
    fi
}

# Fonction d'exécution de la synchronisation
run_synchronization() {
    log "=== EXÉCUTION DE LA SYNCHRONISATION ==="
    
    # Exécution du script de synchronisation principal
    if [ -f "sync_dev_to_production_final.sh" ]; then
        log "Exécution du script de synchronisation..."
        bash sync_dev_to_production_final.sh
    else
        error "Script de synchronisation non trouvé"
        return 1
    fi
}

# Fonction de validation post-synchronisation
run_post_validation() {
    log "=== VALIDATION POST-SYNCHRONISATION ==="
    
    # Test de connectivité
    log "Test de connectivité vers la production..."
    if ssh -o ConnectTimeout=10 $PROD_USER@$PROD_HOST "echo 'Connexion OK'" > /dev/null 2>&1; then
        success "Connexion à la production établie"
    else
        error "Impossible de se connecter à la production"
        return 1
    fi
    
    # Test de l'application Django
    log "Test de l'application Django..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py check --deploy" || warning "Problèmes détectés sur la production"
    
    # Test de connectivité HTTP
    log "Test de connectivité HTTP..."
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com | grep -q "200\|302"; then
        success "Site accessible via HTTPS"
    else
        warning "Problème d'accessibilité HTTPS détecté"
    fi
    
    # Vérification des services
    log "Vérification des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl status nginx --no-pager -l"
    ssh $PROD_USER@$PROD_HOST "systemctl status gunicorn --no-pager -l" || warning "Gunicorn non configuré"
    
    success "Validation post-synchronisation terminée"
}

# Fonction de génération de rapport
generate_final_report() {
    log "=== RAPPORT FINAL ==="
    
    echo
    echo "=== RAPPORT DE SYNCHRONISATION ==="
    echo "Timestamp: $(date)"
    echo "Environnement source: $(python --version 2>&1)"
    echo "Environnement destination: $PROD_HOST"
    echo "Chemin destination: $PROD_PATH"
    echo
    
    # Statut des services
    echo "=== STATUT DES SERVICES ==="
    ssh $PROD_USER@$PROD_HOST "systemctl is-active nginx" && echo "Nginx: ACTIF" || echo "Nginx: INACTIF"
    ssh $PROD_USER@$PROD_HOST "systemctl is-active gunicorn" && echo "Gunicorn: ACTIF" || echo "Gunicorn: INACTIF"
    echo
    
    # Test de connectivité
    echo "=== TESTS DE CONNECTIVITÉ ==="
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com | grep -q "200\|302"; then
        echo "Site web: ACCESSIBLE"
    else
        echo "Site web: INACCESSIBLE"
    fi
    echo
    
    # Espace disque
    echo "=== ESPACE DISQUE ==="
    ssh $PROD_USER@$PROD_HOST "df -h / | tail -1"
    echo
    
    echo "=== SYNCHRONISATION TERMINÉE ==="
    success "Le processus de synchronisation est terminé"
}

# Fonction de gestion des erreurs
handle_error() {
    local exit_code=$?
    local line_number=$1
    
    error "Erreur à la ligne $line_number (code: $exit_code)"
    echo
    warning "En cas de problème, vous pouvez utiliser le script de rollback:"
    echo "  ./rollback_production.sh list"
    echo "  ./rollback_production.sh complete BACKUP_DATE"
    echo
    exit $exit_code
}

# Fonction principale
main() {
    # Configuration du trap pour la gestion d'erreurs
    trap 'handle_error $LINENO' ERR
    
    log "=== DÉBUT DU WORKFLOW DE SYNCHRONISATION ==="
    log "Timestamp: $TIMESTAMP"
    
    # Vérification des prérequis
    check_prerequisites
    
    # Diagnostic préalable
    run_pre_diagnostic
    
    # Confirmation utilisateur
    get_user_confirmation
    
    # Exécution de la synchronisation
    run_synchronization
    
    # Validation post-synchronisation
    run_post_validation
    
    # Génération du rapport final
    generate_final_report
    
    log "=== WORKFLOW TERMINÉ AVEC SUCCÈS ==="
    success "La synchronisation dev → production est terminée avec succès"
}

# Exécution du script principal
main "$@" 