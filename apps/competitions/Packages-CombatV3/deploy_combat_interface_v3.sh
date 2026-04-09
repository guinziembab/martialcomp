#!/bin/bash

################################################################################
# Script de déploiement : Interface de Combat V3
# MartialComp - Mise à jour de l'interface de combat
# 
# Usage: ./deploy_combat_interface_v3.sh [--production]
#
# Options:
#   --production    Déploie en production (avec validations strictes)
#   --staging       Déploie en staging (par défaut)
#   --rollback      Restaure l'ancienne version
#   --help          Affiche l'aide
################################################################################

set -e  # Arrêt sur erreur

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ROOT="/home/martialcomp"
APP_DIR="${PROJECT_ROOT}/apps/competitions"
TEMPLATES_DIR="${APP_DIR}/templates/competitions"
STATIC_DIR="${PROJECT_ROOT}/static"
BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
VENV_DIR="${PROJECT_ROOT}/venv"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Mode de déploiement
MODE="staging"

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# ============================================================================
# GESTION DES ARGUMENTS
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            MODE="production"
            shift
            ;;
        --staging)
            MODE="staging"
            shift
            ;;
        --rollback)
            MODE="rollback"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --production    Déploie en production"
            echo "  --staging       Déploie en staging (défaut)"
            echo "  --rollback      Restaure l'ancienne version"
            echo "  --help          Affiche cette aide"
            exit 0
            ;;
        *)
            print_error "Option inconnue: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# VÉRIFICATIONS PRÉLIMINAIRES
# ============================================================================

check_requirements() {
    print_header "Vérifications préliminaires"
    
    # Vérifier que nous sommes dans le bon répertoire
    if [ ! -d "$PROJECT_ROOT" ]; then
        print_error "Répertoire projet introuvable: $PROJECT_ROOT"
        exit 1
    fi
    
    # Vérifier que l'environnement virtuel existe
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Environnement virtuel introuvable: $VENV_DIR"
        exit 1
    fi
    
    # Vérifier que les fichiers sources existent
    if [ ! -f "interface_combat_v3_improved.html" ]; then
        print_error "Fichier source introuvable: interface_combat_v3_improved.html"
        exit 1
    fi
    
    if [ ! -f "combat_api_views.py" ]; then
        print_error "Fichier API introuvable: combat_api_views.py"
        exit 1
    fi
    
    print_success "Vérifications préliminaires OK"
}

# ============================================================================
# BACKUP DE L'EXISTANT
# ============================================================================

create_backup() {
    print_header "Création du backup"
    
    # Créer le répertoire de backup
    mkdir -p "$BACKUP_DIR"
    
    # Backup des templates
    if [ -f "${TEMPLATES_DIR}/interface_combat_v2.html" ]; then
        cp "${TEMPLATES_DIR}/interface_combat_v2.html" "${BACKUP_DIR}/"
        print_success "Template sauvegardé"
    fi
    
    # Backup des views
    if [ -f "${APP_DIR}/views.py" ]; then
        cp "${APP_DIR}/views.py" "${BACKUP_DIR}/"
        print_success "Views sauvegardées"
    fi
    
    # Backup de la base de données
    print_info "Backup de la base de données..."
    cd "$PROJECT_ROOT"
    source "${VENV_DIR}/bin/activate"
    python manage.py dumpdata competitions > "${BACKUP_DIR}/db_backup.json"
    print_success "Base de données sauvegardée"
    
    echo ""
    print_success "Backup créé dans: $BACKUP_DIR"
}

# ============================================================================
# DÉPLOIEMENT DES FICHIERS
# ============================================================================

deploy_files() {
    print_header "Déploiement des fichiers"
    
    # 1. Déployer le nouveau template
    print_info "Déploiement du template..."
    cp interface_combat_v3_improved.html "${TEMPLATES_DIR}/interface_combat_v3.html"
    
    # En production, remplacer directement v2
    if [ "$MODE" == "production" ]; then
        cp interface_combat_v3_improved.html "${TEMPLATES_DIR}/interface_combat_v2.html"
        print_success "Template déployé en production (remplace v2)"
    else
        print_success "Template déployé en staging (v3)"
    fi
    
    # 2. Déployer les vues API
    print_info "Déploiement des vues API..."
    
    # Vérifier si le fichier existe déjà
    if [ -f "${APP_DIR}/combat_api_views.py" ]; then
        print_warning "combat_api_views.py existe déjà. Fusion nécessaire."
        cp combat_api_views.py "${APP_DIR}/combat_api_views_new.py"
        print_info "Nouveau fichier créé: combat_api_views_new.py"
        print_warning "Merci de fusionner manuellement les fichiers"
    else
        cp combat_api_views.py "${APP_DIR}/"
        print_success "Vues API déployées"
    fi
    
    # 3. Déployer les URLs API
    print_info "Déploiement des URLs API..."
    cp combat_api_urls.py "${APP_DIR}/"
    print_success "URLs API déployées"
    
    # 4. Créer le répertoire des drapeaux si nécessaire
    print_info "Configuration des drapeaux..."
    mkdir -p "${STATIC_DIR}/images/flags"
    print_success "Répertoire drapeaux créé"
}

# ============================================================================
# PRÉPARATION DES DRAPEAUX
# ============================================================================

setup_flags() {
    print_header "Configuration des drapeaux"
    
    FLAGS_DIR="${STATIC_DIR}/images/flags"
    
    print_info "Téléchargement des drapeaux depuis flagcdn.com..."
    
    # Liste des codes pays principaux
    COUNTRIES=(
        "FR" "BE" "DE" "IT" "ES" "GB" "NL" "PT" "CH" "AT"
        "US" "CA" "BR" "AR" "MX" "CN" "JP" "KR" "IN" "TH"
        "AU" "NZ" "ZA" "EG" "MA" "DZ" "TN" "SN" "CI"
    )
    
    for country in "${COUNTRIES[@]}"; do
        # Télécharger le drapeau (format 256x192)
        wget -q "https://flagcdn.com/256x192/${country,,}.png" -O "${FLAGS_DIR}/${country}.png" 2>/dev/null || true
        
        if [ -f "${FLAGS_DIR}/${country}.png" ]; then
            echo -n "."
        else
            print_warning "Échec téléchargement: $country"
        fi
    done
    
    echo ""
    print_success "Drapeaux téléchargés"
    
    # Créer un drapeau par défaut
    if [ ! -f "${FLAGS_DIR}/default.png" ]; then
        # Créer une image par défaut avec ImageMagick si disponible
        if command -v convert &> /dev/null; then
            convert -size 256x192 xc:gray "${FLAGS_DIR}/default.png"
            print_success "Drapeau par défaut créé"
        else
            print_warning "ImageMagick non installé. Drapeau par défaut non créé."
        fi
    fi
}

# ============================================================================
# MISE À JOUR DE LA BASE DE DONNÉES
# ============================================================================

update_database() {
    print_header "Mise à jour de la base de données"
    
    cd "$PROJECT_ROOT"
    source "${VENV_DIR}/bin/activate"
    
    # Vérifier si des migrations sont nécessaires
    print_info "Vérification des migrations..."
    python manage.py makemigrations
    
    # Appliquer les migrations
    print_info "Application des migrations..."
    python manage.py migrate
    
    print_success "Base de données mise à jour"
}

# ============================================================================
# COLLECTE DES FICHIERS STATIQUES
# ============================================================================

collect_static() {
    print_header "Collecte des fichiers statiques"
    
    cd "$PROJECT_ROOT"
    source "${VENV_DIR}/bin/activate"
    
    print_info "Collecte en cours..."
    python manage.py collectstatic --noinput
    
    print_success "Fichiers statiques collectés"
}

# ============================================================================
# TESTS
# ============================================================================

run_tests() {
    print_header "Exécution des tests"
    
    cd "$PROJECT_ROOT"
    source "${VENV_DIR}/bin/activate"
    
    # Tests unitaires
    print_info "Tests unitaires..."
    python manage.py test apps.competitions.test_combat_api --verbosity=2 || true
    
    # Vérification des templates
    print_info "Vérification des templates..."
    python manage.py check
    
    print_success "Tests terminés"
}

# ============================================================================
# REDÉMARRAGE DES SERVICES
# ============================================================================

restart_services() {
    print_header "Redémarrage des services"
    
    if [ "$MODE" == "production" ]; then
        # Redémarrer Gunicorn/uWSGI
        print_info "Redémarrage de Gunicorn..."
        sudo systemctl restart gunicorn || print_warning "Échec redémarrage Gunicorn"
        
        # Redémarrer Nginx
        print_info "Redémarrage de Nginx..."
        sudo systemctl restart nginx || print_warning "Échec redémarrage Nginx"
        
        # Redémarrer Redis (pour le cache)
        print_info "Redémarrage de Redis..."
        sudo systemctl restart redis || print_warning "Échec redémarrage Redis"
    else
        # En staging, juste le serveur de développement
        print_info "Relancer le serveur de développement manuellement"
    fi
    
    print_success "Services redémarrés"
}

# ============================================================================
# ROLLBACK
# ============================================================================

rollback() {
    print_header "ROLLBACK : Restauration de l'ancienne version"
    
    # Trouver le dernier backup
    LATEST_BACKUP=$(ls -td ${PROJECT_ROOT}/backups/*/ | head -1)
    
    if [ -z "$LATEST_BACKUP" ]; then
        print_error "Aucun backup trouvé"
        exit 1
    fi
    
    print_info "Restauration depuis: $LATEST_BACKUP"
    
    # Restaurer le template
    if [ -f "${LATEST_BACKUP}/interface_combat_v2.html" ]; then
        cp "${LATEST_BACKUP}/interface_combat_v2.html" "${TEMPLATES_DIR}/"
        print_success "Template restauré"
    fi
    
    # Restaurer les views
    if [ -f "${LATEST_BACKUP}/views.py" ]; then
        cp "${LATEST_BACKUP}/views.py" "${APP_DIR}/"
        print_success "Views restaurées"
    fi
    
    # Restaurer la base de données
    if [ -f "${LATEST_BACKUP}/db_backup.json" ]; then
        cd "$PROJECT_ROOT"
        source "${VENV_DIR}/bin/activate"
        python manage.py loaddata "${LATEST_BACKUP}/db_backup.json"
        print_success "Base de données restaurée"
    fi
    
    # Redémarrer les services
    restart_services
    
    print_success "Rollback terminé avec succès"
}

# ============================================================================
# VALIDATION POST-DÉPLOIEMENT
# ============================================================================

validate_deployment() {
    print_header "Validation du déploiement"
    
    # Vérifier que les fichiers sont bien en place
    local errors=0
    
    if [ ! -f "${TEMPLATES_DIR}/interface_combat_v3.html" ]; then
        print_error "Template v3 introuvable"
        ((errors++))
    else
        print_success "Template v3 OK"
    fi
    
    if [ ! -f "${APP_DIR}/combat_api_views.py" ]; then
        print_error "API views introuvables"
        ((errors++))
    else
        print_success "API views OK"
    fi
    
    if [ ! -f "${APP_DIR}/combat_api_urls.py" ]; then
        print_error "API URLs introuvables"
        ((errors++))
    else
        print_success "API URLs OK"
    fi
    
    if [ ! -d "${STATIC_DIR}/images/flags" ]; then
        print_warning "Répertoire drapeaux manquant"
    else
        flag_count=$(ls -1 "${STATIC_DIR}/images/flags/"*.png 2>/dev/null | wc -l)
        print_success "Drapeaux: $flag_count fichiers"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "Validation échouée avec $errors erreur(s)"
        return 1
    else
        print_success "Validation réussie !"
        return 0
    fi
}

# ============================================================================
# GÉNÉRATION DU RAPPORT
# ============================================================================

generate_report() {
    print_header "Génération du rapport de déploiement"
    
    REPORT_FILE="${BACKUP_DIR}/deployment_report.txt"
    
    cat > "$REPORT_FILE" <<EOF
================================================================================
RAPPORT DE DÉPLOIEMENT - Interface Combat V3
================================================================================

Date: $(date)
Mode: $MODE
Utilisateur: $(whoami)
Serveur: $(hostname)

FICHIERS DÉPLOYÉS:
------------------
- Template: ${TEMPLATES_DIR}/interface_combat_v3.html
- API Views: ${APP_DIR}/combat_api_views.py
- API URLs: ${APP_DIR}/combat_api_urls.py

BACKUP:
-------
Emplacement: $BACKUP_DIR
Fichiers sauvegardés:
$(ls -lh "$BACKUP_DIR")

DRAPEAUX:
---------
Nombre de drapeaux: $(ls -1 "${STATIC_DIR}/images/flags/"*.png 2>/dev/null | wc -l)

PROCHAINES ÉTAPES:
------------------
1. Vérifier que l'interface fonctionne correctement
2. Tester le bouton "Refresh" avec un combat actif
3. Vérifier l'affichage des drapeaux et logos
4. Tester la navigation vers "Gestion Poule"
5. Valider le mode plein écran

ROLLBACK:
---------
Pour revenir à l'ancienne version:
./deploy_combat_interface_v3.sh --rollback

================================================================================
EOF

    print_success "Rapport généré: $REPORT_FILE"
    cat "$REPORT_FILE"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    print_header "🥋 DÉPLOIEMENT INTERFACE COMBAT V3"
    echo ""
    print_info "Mode: $MODE"
    echo ""
    
    # Si rollback, exécuter uniquement cette fonction
    if [ "$MODE" == "rollback" ]; then
        rollback
        exit 0
    fi
    
    # Sinon, déploiement complet
    check_requirements
    echo ""
    
    create_backup
    echo ""
    
    deploy_files
    echo ""
    
    setup_flags
    echo ""
    
    update_database
    echo ""
    
    collect_static
    echo ""
    
    if [ "$MODE" == "production" ]; then
        run_tests
        echo ""
    fi
    
    restart_services
    echo ""
    
    if validate_deployment; then
        echo ""
        generate_report
        echo ""
        print_success "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
        echo ""
        print_info "L'interface de combat V3 est maintenant active."
        print_info "Accédez à un combat pour voir les améliorations."
    else
        echo ""
        print_error "⚠️  DÉPLOIEMENT TERMINÉ AVEC DES AVERTISSEMENTS"
        print_info "Consultez les messages ci-dessus pour plus de détails."
    fi
}

# Exécution
main "$@"
