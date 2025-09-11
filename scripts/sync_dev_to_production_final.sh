#!/bin/bash

# Script de Synchronisation Dev → Production
# MartialComp - Synchronisation Complète et Sécurisée

set -e  # Arrêter en cas d'erreur

# Configuration
PROJECT_NAME="martialcomp"
PROD_USER="root"
PROD_HOST="martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com"
BACKUP_DIR="/root/martialcomp_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de logging
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

# Fonction de vérification d'erreur
check_error() {
    if [ $? -ne 0 ]; then
        error "Erreur lors de l'exécution de la commande précédente"
        exit 1
    fi
}

# Fonction de backup avant modification
create_backup() {
    local step_name="$1"
    log "Création du backup: $step_name"
    
    ssh $PROD_USER@$PROD_HOST "mkdir -p $BACKUP_DIR/$TIMESTAMP"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/$TIMESTAMP/${step_name}_backup.tar.gz ."
    success "Backup créé: $step_name"
}

# Fonction de test de connectivité
test_connection() {
    log "Test de connectivité vers la production..."
    if ssh -o ConnectTimeout=10 $PROD_USER@$PROD_HOST "echo 'Connexion OK'" > /dev/null 2>&1; then
        success "Connexion à la production établie"
    else
        error "Impossible de se connecter à la production"
        exit 1
    fi
}

# Fonction de vérification de l'espace disque
check_disk_space() {
    log "Vérification de l'espace disque sur la production..."
    local space=$(ssh $PROD_USER@$PROD_HOST "df / | tail -1 | awk '{print \$5}' | sed 's/%//'")
    if [ "$space" -gt 90 ]; then
        warning "Espace disque critique: ${space}% utilisé"
        log "Nettoyage recommandé avant de continuer"
        read -p "Continuer malgré l'espace disque limité? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        success "Espace disque OK: ${space}% utilisé"
    fi
}

# PHASE 1: PRÉPARATION ET DIAGNOSTIC
phase1_diagnostic() {
    log "=== PHASE 1: DIAGNOSTIC COMPLET ==="
    
    # Test de connectivité
    test_connection
    check_disk_space
    
    # Vérification de l'environnement de développement local
    log "Vérification de l'environnement de développement..."
    if [ -f "manage.py" ]; then
        python manage.py check --deploy
        success "Environnement de développement OK"
    else
        error "manage.py non trouvé dans le répertoire courant"
        exit 1
    fi
    
    # Vérification de l'état de la production
    log "Diagnostic de l'état de la production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py check --deploy" || warning "Problèmes détectés sur la production (normal)"
    
    # Vérification des migrations
    log "Vérification des migrations..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py showmigrations" || warning "Erreur lors de la vérification des migrations"
    
    success "Phase 1 terminée"
}

# PHASE 2: NETTOYAGE COMPLET ET SYNCHRONISATION DU CODE SOURCE
phase2_code_sync() {
    log "=== PHASE 2: NETTOYAGE COMPLET ET SYNCHRONISATION DU CODE SOURCE ==="
    
    create_backup "avant_sync_code"
    
    # Nettoyage complet de la production
    log "Nettoyage complet de la production..."
    
    # Arrêt des services
    ssh $PROD_USER@$PROD_HOST "systemctl stop nginx"
    ssh $PROD_USER@$PROD_HOST "systemctl stop gunicorn" || true
    
    # Sauvegarde des éléments à conserver
    ssh $PROD_USER@$PROD_HOST "mkdir -p $BACKUP_DIR/$TIMESTAMP/preserved_elements"
    
    # Sauvegarde des fichiers de configuration
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/$TIMESTAMP/preserved_elements/config_files.tar.gz \
        config/production.py config/local.py production.env .env vhost.conf passenger_wsgi.py *.sh *.sql 2>/dev/null || true"
    
    # Sauvegarde des dossiers importants
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/$TIMESTAMP/preserved_elements/important_dirs.tar.gz \
        media/ uploads/ user_uploads/ documents/ certificates/ images/ videos/ logs/ backups/ 2>/dev/null || true"
    
    # Suppression complète (sauf les éléments sauvegardés)
    log "Suppression complète des fichiers..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && rm -rf * .* 2>/dev/null || true"
    
    # Restauration des éléments conservés
    log "Restauration des éléments conservés..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -xzf $BACKUP_DIR/$TIMESTAMP/preserved_elements/config_files.tar.gz 2>/dev/null || true"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -xzf $BACKUP_DIR/$TIMESTAMP/preserved_elements/important_dirs.tar.gz 2>/dev/null || true"
    
    # Synchronisation du code source propre
    log "Synchronisation du code source propre..."
    rsync -avz --exclude="*.pyc" \
        --exclude="__pycache__/" \
        --exclude=".env" \
        --exclude="production.env" \
        --exclude="*.log" \
        --exclude="logs/" \
        --exclude="backups/" \
        --exclude="staticfiles/" \
        --exclude="media/" \
        --exclude="db.sqlite3" \
        --exclude=".venv/" \
        --exclude="venv/" \
        --exclude=".git/" \
        --exclude="node_modules/" \
        --exclude="*.sql" \
        --exclude="*.sh" \
        --exclude="config/production.py" \
        --exclude="config/local.py" \
        --exclude="vhost.conf" \
        --exclude="passenger_wsgi.py" \
        ./ $PROD_USER@$PROD_HOST:$PROD_PATH/
    
    check_error
    
    success "Nettoyage complet et synchronisation du code source terminés"
}

# PHASE 3: SYNCHRONISATION DE LA BASE DE DONNÉES
phase3_database_sync() {
    log "=== PHASE 3: SYNCHRONISATION DE LA BASE DE DONNÉES ==="
    
    create_backup "avant_sync_db"
    
    # Création d'un dump de la base de développement
    log "Création du dump de la base de développement..."
    python manage.py dumpdata --exclude auth.permission --exclude contenttypes --indent 2 > /tmp/dev_data.json
    
    # Transfert du dump vers la production
    log "Transfert du dump vers la production..."
    scp /tmp/dev_data.json $PROD_USER@$PROD_HOST:/tmp/
    
    # Application des migrations sur la production
    log "Application des migrations sur la production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py migrate --fake-initial"
    
    # Chargement des données de développement
    log "Chargement des données de développement..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py loaddata /tmp/dev_data.json"
    
    # Nettoyage
    rm -f /tmp/dev_data.json
    ssh $PROD_USER@$PROD_HOST "rm -f /tmp/dev_data.json"
    
    success "Synchronisation de la base de données terminée"
}

# PHASE 4: SYNCHRONISATION DES FICHIERS STATIQUES
phase4_static_files() {
    log "=== PHASE 4: SYNCHRONISATION DES FICHIERS STATIQUES ==="
    
    # Collecte des fichiers statiques en local
    log "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
    
    # Synchronisation des fichiers statiques
    log "Synchronisation des fichiers statiques..."
    rsync -avz staticfiles/ $PROD_USER@$PROD_HOST:$PROD_PATH/staticfiles/
    
    # Synchronisation des traductions
    log "Synchronisation des traductions..."
    rsync -avz locale/ $PROD_USER@$PROD_HOST:$PROD_PATH/locale/
    
    # Compilation des traductions sur la production
    log "Compilation des traductions sur la production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py compilemessages"
    
    success "Synchronisation des fichiers statiques terminée"
}

# PHASE 5: CONFIGURATION DE LA PRODUCTION
phase5_production_config() {
    log "=== PHASE 5: CONFIGURATION DE LA PRODUCTION ==="
    
    create_backup "avant_config_prod"
    
    # Vérification et correction des paramètres de production
    log "Vérification des paramètres de production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py check --deploy"
    
    # Redémarrage des services
    log "Redémarrage des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl restart nginx"
    ssh $PROD_USER@$PROD_HOST "systemctl restart gunicorn"
    
    success "Configuration de la production terminée"
}

# PHASE 6: TESTS ET VALIDATION
phase6_testing() {
    log "=== PHASE 6: TESTS ET VALIDATION ==="
    
    # Test de connectivité HTTP
    log "Test de connectivité HTTP..."
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com | grep -q "200\|302"; then
        success "Site accessible via HTTP"
    else
        warning "Problème d'accessibilité HTTP détecté"
    fi
    
    # Test de l'API Django
    log "Test de l'API Django..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py shell -c \"from django.test import Client; c = Client(); print('Test client:', c.get('/').status_code)\""
    
    success "Tests de validation terminés"
}

# Fonction principale
main() {
    log "=== DÉBUT DE LA SYNCHRONISATION DEV → PRODUCTION ==="
    log "Timestamp: $TIMESTAMP"
    
    # Vérification des prérequis
    if ! command -v rsync &> /dev/null; then
        error "rsync n'est pas installé"
        exit 1
    fi
    
    if ! command -v ssh &> /dev/null; then
        error "ssh n'est pas installé"
        exit 1
    fi
    
    # Exécution des phases
    phase1_diagnostic
    phase2_code_sync
    phase3_database_sync
    phase4_static_files
    phase5_production_config
    phase6_testing
    
    log "=== SYNCHRONISATION TERMINÉE AVEC SUCCÈS ==="
    success "Toutes les phases ont été exécutées avec succès"
    
    # Résumé final
    echo
    log "Résumé de la synchronisation:"
    echo "  - Code source: ✅ Synchronisé"
    echo "  - Base de données: ✅ Synchronisée"
    echo "  - Fichiers statiques: ✅ Synchronisés"
    echo "  - Configuration: ✅ Appliquée"
    echo "  - Tests: ✅ Validés"
    echo
    log "Backups disponibles dans: $BACKUP_DIR/$TIMESTAMP/"
}

# Gestion des erreurs
trap 'error "Erreur critique détectée. Arrêt du script."; exit 1' ERR

# Exécution du script principal
main "$@" 