#!/bin/bash

# Script de Rollback Production
# MartialComp - Restauration en Cas de Problème

set -e

# Configuration
PROJECT_NAME="martialcomp"
PROD_USER="root"
PROD_HOST="martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com"
BACKUP_DIR="/root/martialcomp_backups"

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

# Fonction de liste des backups disponibles
list_backups() {
    log "=== BACKUPS DISPONIBLES ==="
    
    if ssh $PROD_USER@$PROD_HOST "test -d $BACKUP_DIR"; then
        ssh $PROD_USER@$PROD_HOST "ls -la $BACKUP_DIR/"
        echo
        echo "Backups par date:"
        ssh $PROD_USER@$PROD_HOST "ls -la $BACKUP_DIR/" | grep "^d" | awk '{print $9}' | sort -r
    else
        error "Aucun backup trouvé dans $BACKUP_DIR"
        return 1
    fi
}

# Fonction de restauration complète
restore_complete_backup() {
    local backup_date="$1"
    local backup_path="$BACKUP_DIR/$backup_date"
    
    log "=== RESTAURATION COMPLÈTE ==="
    log "Backup à restaurer: $backup_date"
    
    # Vérification de l'existence du backup
    if ! ssh $PROD_USER@$PROD_HOST "test -d $backup_path"; then
        error "Backup $backup_date n'existe pas"
        return 1
    fi
    
    # Confirmation de l'utilisateur
    echo
    warning "ATTENTION: Cette opération va remplacer complètement l'environnement de production"
    echo "Backup à restaurer: $backup_date"
    echo "Chemin: $backup_path"
    echo
    read -p "Êtes-vous sûr de vouloir continuer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restauration annulée par l'utilisateur"
        return 1
    fi
    
    # Arrêt des services
    log "Arrêt des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl stop nginx"
    ssh $PROD_USER@$PROD_HOST "systemctl stop gunicorn" || true
    
    # Sauvegarde de l'état actuel
    log "Sauvegarde de l'état actuel..."
    ssh $PROD_USER@$PROD_HOST "mkdir -p $BACKUP_DIR/rollback_$(date +%Y%m%d_%H%M%S)"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/rollback_$(date +%Y%m%d_%H%M%S)/current_state.tar.gz ."
    
    # Restauration du backup
    log "Restauration du backup..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && rm -rf * .* 2>/dev/null || true"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -xzf $backup_path/*.tar.gz"
    
    # Redémarrage des services
    log "Redémarrage des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl start nginx"
    ssh $PROD_USER@$PROD_HOST "systemctl start gunicorn" || warning "Gunicorn non configuré"
    
    success "Restauration complète terminée"
}

# Fonction de restauration partielle (code uniquement)
restore_code_only() {
    local backup_date="$1"
    local backup_path="$BACKUP_DIR/$backup_date"
    
    log "=== RESTAURATION PARTIELLE (CODE UNIQUEMENT) ==="
    log "Backup à restaurer: $backup_date"
    
    # Vérification de l'existence du backup
    if ! ssh $PROD_USER@$PROD_HOST "test -d $backup_path"; then
        error "Backup $backup_date n'existe pas"
        return 1
    fi
    
    # Confirmation de l'utilisateur
    echo
    warning "Cette opération va restaurer uniquement le code source"
    echo "Backup à restaurer: $backup_date"
    echo
    read -p "Continuer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restauration annulée par l'utilisateur"
        return 1
    fi
    
    # Sauvegarde de l'état actuel
    log "Sauvegarde de l'état actuel..."
    ssh $PROD_USER@$PROD_HOST "mkdir -p $BACKUP_DIR/rollback_$(date +%Y%m%d_%H%M%S)"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/rollback_$(date +%Y%m%d_%H%M%S)/current_code.tar.gz ."
    
    # Restauration du code (excluant les fichiers de config)
    log "Restauration du code source..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -xzf $backup_path/*.tar.gz --exclude='*.env' --exclude='config/production.py' --exclude='vhost.conf'"
    
    # Redémarrage des services
    log "Redémarrage des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl restart nginx"
    ssh $PROD_USER@$PROD_HOST "systemctl restart gunicorn" || warning "Gunicorn non configuré"
    
    success "Restauration partielle terminée"
}

# Fonction de restauration de la base de données
restore_database() {
    local backup_date="$1"
    local backup_path="$BACKUP_DIR/$backup_date"
    
    log "=== RESTAURATION DE LA BASE DE DONNÉES ==="
    log "Backup à restaurer: $backup_date"
    
    # Vérification de l'existence du backup
    if ! ssh $PROD_USER@$PROD_HOST "test -d $backup_path"; then
        error "Backup $backup_date n'existe pas"
        return 1
    fi
    
    # Confirmation de l'utilisateur
    echo
    warning "ATTENTION: Cette opération va restaurer la base de données"
    echo "Toutes les données actuelles seront perdues"
    echo
    read -p "Êtes-vous sûr de vouloir continuer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Restauration annulée par l'utilisateur"
        return 1
    fi
    
    # Sauvegarde de la base actuelle
    log "Sauvegarde de la base actuelle..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 > /tmp/current_db_backup.json"
    
    # Restauration de la base
    log "Restauration de la base de données..."
    if ssh $PROD_USER@$PROD_HOST "test -f $backup_path/database_backup.sql"; then
        ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py dbshell < $backup_path/database_backup.sql"
    elif ssh $PROD_USER@$PROD_HOST "test -f $backup_path/database_backup.json"; then
        ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py loaddata $backup_path/database_backup.json"
    else
        warning "Aucun fichier de backup de base de données trouvé"
    fi
    
    success "Restauration de la base de données terminée"
}

# Fonction de test après restauration
test_restoration() {
    log "=== TEST APRÈS RESTAURATION ==="
    
    # Test de connectivité
    log "Test de connectivité..."
    if ssh -o ConnectTimeout=10 $PROD_USER@$PROD_HOST "echo 'Connexion OK'" > /dev/null 2>&1; then
        success "Connexion à la production établie"
    else
        error "Impossible de se connecter à la production"
        return 1
    fi
    
    # Test de l'application Django
    log "Test de l'application Django..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py check --deploy" || warning "Problèmes détectés"
    
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
    
    success "Tests de restauration terminés"
}

# Fonction d'aide
show_help() {
    echo "Usage: $0 [OPTION] [BACKUP_DATE]"
    echo
    echo "Options:"
    echo "  list                    Lister les backups disponibles"
    echo "  complete BACKUP_DATE    Restauration complète"
    echo "  code BACKUP_DATE        Restauration du code uniquement"
    echo "  db BACKUP_DATE          Restauration de la base de données uniquement"
    echo "  test                    Tester la restauration"
    echo "  help                    Afficher cette aide"
    echo
    echo "Exemples:"
    echo "  $0 list"
    echo "  $0 complete 20250630_212938"
    echo "  $0 code 20250630_212938"
    echo "  $0 db 20250630_212938"
    echo "  $0 test"
}

# Fonction principale
main() {
    case "${1:-help}" in
        "list")
            list_backups
            ;;
        "complete")
            if [ -z "$2" ]; then
                error "Date de backup requise"
                show_help
                exit 1
            fi
            restore_complete_backup "$2"
            test_restoration
            ;;
        "code")
            if [ -z "$2" ]; then
                error "Date de backup requise"
                show_help
                exit 1
            fi
            restore_code_only "$2"
            test_restoration
            ;;
        "db")
            if [ -z "$2" ]; then
                error "Date de backup requise"
                show_help
                exit 1
            fi
            restore_database "$2"
            test_restoration
            ;;
        "test")
            test_restoration
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Exécution du script principal
main "$@" 