#!/bin/bash

# Script de Diagnostic Pré-Synchronisation
# MartialComp - Diagnostic Complet Avant Sync

set -e

# Configuration
PROJECT_NAME="martialcomp"
PROD_USER="root"
PROD_HOST="martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com"

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

# Fonction de diagnostic local
diagnostic_local() {
    log "=== DIAGNOSTIC ENVIRONNEMENT LOCAL ==="
    
    # Vérification de la structure du projet
    log "Vérification de la structure du projet..."
    if [ -f "manage.py" ]; then
        success "manage.py trouvé"
    else
        error "manage.py manquant"
        return 1
    fi
    
    # Vérification de l'environnement Python
    log "Vérification de l'environnement Python..."
    python --version
    which python
    
    # Vérification des dépendances
    log "Vérification des dépendances..."
    if [ -f "requirements.txt" ]; then
        success "requirements.txt trouvé"
        echo "Dépendances principales:"
        grep -E "^(Django|django-|gunicorn|psycopg2)" requirements.txt || echo "Aucune dépendance critique trouvée"
    else
        warning "requirements.txt manquant"
    fi
    
    # Test de l'application Django
    log "Test de l'application Django..."
    python manage.py check --deploy
    
    # Vérification des migrations
    log "Vérification des migrations..."
    python manage.py showmigrations
    
    # Vérification de la base de données locale
    log "Vérification de la base de données locale..."
    python manage.py dbshell -c "\dt" 2>/dev/null || warning "Impossible de vérifier la base locale"
    
    success "Diagnostic local terminé"
}

# Fonction de diagnostic production
diagnostic_production() {
    log "=== DIAGNOSTIC ENVIRONNEMENT PRODUCTION ==="
    
    # Test de connectivité
    log "Test de connectivité vers la production..."
    if ssh -o ConnectTimeout=10 $PROD_USER@$PROD_HOST "echo 'Connexion OK'" > /dev/null 2>&1; then
        success "Connexion à la production établie"
    else
        error "Impossible de se connecter à la production"
        return 1
    fi
    
    # Vérification de l'espace disque
    log "Vérification de l'espace disque..."
    ssh $PROD_USER@$PROD_HOST "df -h /"
    
    # Vérification de la structure du projet
    log "Vérification de la structure du projet sur la production..."
    ssh $PROD_USER@$PROD_HOST "ls -la $PROD_PATH/"
    
    # Vérification de l'environnement Python
    log "Vérification de l'environnement Python sur la production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python --version"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && which python"
    
    # Test de l'application Django
    log "Test de l'application Django sur la production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py check --deploy" || warning "Problèmes détectés sur la production"
    
    # Vérification des migrations
    log "Vérification des migrations sur la production..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py showmigrations" || warning "Erreur lors de la vérification des migrations"
    
    # Vérification des services
    log "Vérification des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl status nginx --no-pager -l"
    ssh $PROD_USER@$PROD_HOST "systemctl status gunicorn --no-pager -l" || warning "Gunicorn non configuré ou arrêté"
    
    # Vérification des logs
    log "Vérification des logs récents..."
    ssh $PROD_USER@$PROD_HOST "tail -20 /var/log/nginx/error.log" 2>/dev/null || warning "Logs Nginx non accessibles"
    ssh $PROD_USER@$PROD_HOST "tail -20 /var/log/gunicorn/error.log" 2>/dev/null || warning "Logs Gunicorn non accessibles"
    
    success "Diagnostic production terminé"
}

# Fonction de comparaison des configurations
compare_configs() {
    log "=== COMPARAISON DES CONFIGURATIONS ==="
    
    # Comparaison des fichiers de configuration
    log "Comparaison des fichiers de configuration..."
    
    # Vérification des différences dans les settings
    if [ -f "config/settings.py" ]; then
        log "Fichier settings.py local trouvé"
    fi
    
    if ssh $PROD_USER@$PROD_HOST "test -f $PROD_PATH/config/settings.py"; then
        log "Fichier settings.py production trouvé"
    else
        warning "Fichier settings.py manquant sur la production"
    fi
    
    # Vérification des variables d'environnement
    log "Vérification des variables d'environnement..."
    if [ -f ".env" ]; then
        echo "Variables d'environnement locales:"
        grep -v "^#" .env | grep -v "^$" || echo "Aucune variable trouvée"
    fi
    
    if ssh $PROD_USER@$PROD_HOST "test -f $PROD_PATH/.env"; then
        echo "Variables d'environnement production:"
        ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && grep -v '^#' .env | grep -v '^$'" || echo "Aucune variable trouvée"
    fi
    
    success "Comparaison des configurations terminée"
}

# Fonction de vérification des migrations
check_migrations() {
    log "=== VÉRIFICATION DES MIGRATIONS ==="
    
    # Migrations locales
    log "Migrations locales:"
    python manage.py showmigrations
    
    # Migrations production
    log "Migrations production:"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py showmigrations" || warning "Erreur lors de la vérification des migrations production"
    
    # Identification des migrations manquantes
    log "Identification des migrations manquantes..."
    python manage.py showmigrations > /tmp/local_migrations.txt
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && python manage.py showmigrations" > /tmp/prod_migrations.txt 2>/dev/null || echo "Erreur migrations production" > /tmp/prod_migrations.txt
    
    echo "Différences dans les migrations:"
    diff /tmp/local_migrations.txt /tmp/prod_migrations.txt || echo "Aucune différence détectée"
    
    # Nettoyage
    rm -f /tmp/local_migrations.txt /tmp/prod_migrations.txt
    
    success "Vérification des migrations terminée"
}

# Fonction de test de connectivité HTTP
test_http_connectivity() {
    log "=== TEST DE CONNECTIVITÉ HTTP ==="
    
    # Test de connectivité vers le site
    log "Test de connectivité vers martialcomp.com..."
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com | grep -q "200\|302"; then
        success "Site accessible via HTTPS"
    else
        warning "Problème d'accessibilité HTTPS détecté"
    fi
    
    # Test de connectivité vers le port 8001 (Gunicorn)
    log "Test de connectivité vers le port 8001..."
    if curl -s -o /dev/null -w "%{http_code}" http://martialcomp.com:8001 | grep -q "200\|302"; then
        success "Gunicorn accessible sur le port 8001"
    else
        warning "Gunicorn non accessible sur le port 8001"
    fi
    
    success "Tests de connectivité HTTP terminés"
}

# Fonction de rapport final
generate_report() {
    log "=== RAPPORT FINAL ==="
    
    echo
    echo "=== RÉSUMÉ DU DIAGNOSTIC ==="
    echo "Timestamp: $(date)"
    echo "Environnement local: $(python --version 2>&1)"
    echo "Connexion production: $([ -n "$(ssh -o ConnectTimeout=5 $PROD_USER@$PROD_HOST 'echo OK' 2>/dev/null)" ] && echo "OK" || echo "ÉCHEC")"
    echo "Espace disque production: $(ssh $PROD_USER@$PROD_HOST 'df / | tail -1 | awk "{print \$5}"' 2>/dev/null || echo "N/A")"
    echo "Services production:"
    echo "  - Nginx: $(ssh $PROD_USER@$PROD_HOST 'systemctl is-active nginx' 2>/dev/null || echo "N/A")"
    echo "  - Gunicorn: $(ssh $PROD_USER@$PROD_HOST 'systemctl is-active gunicorn' 2>/dev/null || echo "N/A")"
    echo
    echo "=== RECOMMANDATIONS ==="
    echo "1. Vérifier l'espace disque avant la synchronisation"
    echo "2. Créer un backup complet avant toute modification"
    echo "3. Tester les migrations sur un environnement de test"
    echo "4. Vérifier les configurations de sécurité"
    echo
}

# Fonction principale
main() {
    log "=== DÉBUT DU DIAGNOSTIC PRÉ-SYNCHRONISATION ==="
    
    # Vérification des prérequis
    if ! command -v ssh &> /dev/null; then
        error "ssh n'est pas installé"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        warning "curl n'est pas installé - tests HTTP limités"
    fi
    
    # Exécution des diagnostics
    diagnostic_local
    diagnostic_production
    compare_configs
    check_migrations
    test_http_connectivity
    generate_report
    
    log "=== DIAGNOSTIC TERMINÉ ==="
    success "Diagnostic complet terminé. Vérifiez le rapport ci-dessus avant de procéder à la synchronisation."
}

# Exécution du script principal
main "$@" 