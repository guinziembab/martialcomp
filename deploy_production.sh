#!/bin/bash
# ===========================================
# SCRIPT DE DÉPLOIEMENT MARTIALCOMP PRODUCTION
# Serveur: VPS Ionos - martialcomp.com
# ===========================================

set -e  # Arrêter le script en cas d'erreur

# Configuration
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups"
LOG_FILE="/var/www/vhosts/martialcomp.com/logs/deployment.log"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Fonction d'affichage coloré
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log "INFO: $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log "SUCCESS: $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log "WARNING: $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log "ERROR: $1"
}

# Vérification des prérequis
check_prerequisites() {
    print_status "Vérification des prérequis..."
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "Répertoire du projet non trouvé: $PROJECT_DIR"
        exit 1
    fi
    
    # Vérifier que l'environnement virtuel existe
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Environnement virtuel non trouvé: $VENV_DIR"
        exit 1
    fi
    
    # Vérifier les variables d'environnement critiques
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        print_error "Fichier .env non trouvé. Copiez .env.production vers .env"
        exit 1
    fi
    
    print_success "Prérequis vérifiés"
}

# Fonction de sauvegarde
backup_database() {
    print_status "Sauvegarde de la base de données..."
    
    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$BACKUP_DIR"
    
    # Charger les variables depuis .env
    source "$PROJECT_DIR/.env"
    
    pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        print_success "Base de données sauvegardée: $BACKUP_FILE"
    else
        print_error "Échec de la sauvegarde de la base de données"
        exit 1
    fi
}

# Mise à jour du code
update_code() {
    print_status "Mise à jour du code source..."
    
    cd "$PROJECT_DIR"
    
    # Sauvegarder les fichiers locaux importants
    cp .env .env.backup 2>/dev/null || true
    
    # Mettre à jour depuis Git
    git fetch origin
    git pull origin main
    
    # Restaurer le fichier .env si nécessaire
    if [ ! -f .env ] && [ -f .env.backup ]; then
        mv .env.backup .env
        print_warning "Fichier .env restauré depuis la sauvegarde"
    fi
    
    print_success "Code source mis à jour"
}

# Installation des dépendances
install_dependencies() {
    print_status "Installation/mise à jour des dépendances Python..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Mise à jour de pip
    pip install --upgrade pip
    
    # Installation des dépendances
    pip install -r requirements.txt
    
    print_success "Dépendances installées"
}

# Migrations de base de données
run_migrations() {
    print_status "Application des migrations de base de données..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Utiliser les settings de production
    export DJANGO_SETTINGS_MODULE="config.settings_production"
    
    # Vérifier les migrations
    python manage.py showmigrations --plan
    
    # Appliquer les migrations
    python manage.py migrate --no-input
    
    print_success "Migrations appliquées"
}

# Collecte des fichiers statiques
collect_static() {
    print_status "Collecte des fichiers statiques..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    export DJANGO_SETTINGS_MODULE="config.settings_production"
    
    python manage.py collectstatic --no-input --clear
    
    print_success "Fichiers statiques collectés"
}

# Compilation des traductions
compile_translations() {
    print_status "Compilation des traductions..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    export DJANGO_SETTINGS_MODULE="config.settings_production"
    
    if [ -d "locale" ]; then
        python manage.py compilemessages
        print_success "Traductions compilées"
    else
        print_warning "Répertoire locale non trouvé, traductions ignorées"
    fi
}

# Test de l'application
test_application() {
    print_status "Test de l'application..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    export DJANGO_SETTINGS_MODULE="config.settings_production"
    
    # Test de base - vérification de la configuration
    python manage.py check --deploy
    
    # Test de connexion à la base de données
    python manage.py dbshell --command="\q" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Tests de base réussis"
    else
        print_error "Échec des tests de base"
        exit 1
    fi
}

# Optimisation et nettoyage
optimize_deployment() {
    print_status "Optimisation du déploiement..."
    
    cd "$PROJECT_DIR"
    
    # Nettoyage des fichiers temporaires Python
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    
    # Nettoyage des logs anciens (garde les 30 derniers jours)
    find /var/www/vhosts/martialcomp.com/logs/ -name "*.log*" -mtime +30 -delete 2>/dev/null || true
    
    # Nettoyage des sauvegardes anciennes (garde les 30 dernières)
    find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete 2>/dev/null || true
    
    print_success "Optimisation terminée"
}

# Redémarrage des services
restart_services() {
    print_status "Redémarrage des services..."
    
    # Note: En utilisant Plesk, le redémarrage se fait via l'interface Plesk
    # ou en touchant le fichier wsgi.py pour forcer un reload
    touch "$PROJECT_DIR/config/wsgi.py"
    
    print_success "Signal de redémarrage envoyé (wsgi.py touched)"
    print_warning "Redémarrez manuellement l'application via Plesk si nécessaire"
}

# Vérification post-déploiement
post_deployment_check() {
    print_status "Vérification post-déploiement..."
    
    cd "$PROJECT_DIR"
    source "$VENV_DIR/bin/activate"
    
    export DJANGO_SETTINGS_MODULE="config.settings_production"
    
    # Vérifier que Django peut démarrer
    python -c "import django; django.setup(); print('Django configuration OK')"
    
    # Vérifier la connexion à la base de données
    python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); print('Database connection OK')"
    
    print_success "Vérifications post-déploiement réussies"
}

# Affichage de l'aide
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --full          Déploiement complet (par défaut)"
    echo "  --quick         Déploiement rapide (sans sauvegarde DB)"
    echo "  --migrations    Seulement les migrations"
    echo "  --static        Seulement les fichiers statiques"
    echo "  --help          Afficher cette aide"
    echo ""
}

# Fonction principale
main() {
    local mode="full"
    
    # Parse des arguments
    case "${1:-}" in
        --quick)
            mode="quick"
            ;;
        --migrations)
            mode="migrations"
            ;;
        --static)
            mode="static"
            ;;
        --help)
            show_help
            exit 0
            ;;
        --full|"")
            mode="full"
            ;;
        *)
            print_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
    
    print_status "=== DÉBUT DU DÉPLOIEMENT MARTIALCOMP ==="
    print_status "Mode: $mode"
    print_status "Timestamp: $(date)"
    
    # Créer le répertoire de logs si nécessaire
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Exécution selon le mode
    case "$mode" in
        "full")
            check_prerequisites
            backup_database
            update_code
            install_dependencies
            run_migrations
            collect_static
            compile_translations
            test_application
            optimize_deployment
            restart_services
            post_deployment_check
            ;;
        "quick")
            check_prerequisites
            update_code
            install_dependencies
            run_migrations
            collect_static
            restart_services
            post_deployment_check
            ;;
        "migrations")
            check_prerequisites
            run_migrations
            restart_services
            ;;
        "static")
            check_prerequisites
            collect_static
            restart_services
            ;;
    esac
    
    print_success "=== DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ==="
    print_status "Logs disponibles dans: $LOG_FILE"
    print_status "Site accessible sur: https://martialcomp.com"
}

# Point d'entrée
main "$@"