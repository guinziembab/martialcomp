#!/bin/bash

################################################################################
# DÉPLOIEMENT PRODUCTION - CORRECTION DASHBOARDS MARTIALCOMP
################################################################################

set -e

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"
BACKUP_PATH="/var/www/vhosts/martialcomp.com/backups/dashboard_fix"
VENV_PATH="/var/www/vhosts/martialcomp.com/httpdocs/venv"

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

create_production_backup() {
    info "💾 Sauvegarde complète de la production..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$BACKUP_PATH/$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder les fichiers critiques
    cp -r "$PRODUCTION_PATH/competitions/views/" "$BACKUP_DIR/views_backup/"
    cp -r "$PRODUCTION_PATH/competitions/templates/" "$BACKUP_DIR/templates_backup/"
    cp "$PRODUCTION_PATH/config/settings.py" "$BACKUP_DIR/"
    cp "$PRODUCTION_PATH/config/urls.py" "$BACKUP_DIR/"
    
    success "Sauvegarde créée: $BACKUP_DIR"
    echo "$BACKUP_DIR" > /tmp/production_backup_path
}

deploy_corrected_views() {
    info "🚀 Déploiement des vues corrigées..."
    
    # Copier les fichiers __init__.py corrigés
    cp "$LOCAL_PATH/competitions/views/__init__.py" "$PRODUCTION_PATH/competitions/views/"
    cp "$LOCAL_PATH/competitions/views/club/__init__.py" "$PRODUCTION_PATH/competitions/views/club/"
    
    # Copier les vues practitioner corrigées
    if [ -f "$LOCAL_PATH/competitions/views/practitioner_dashboard.py" ]; then
        cp "$LOCAL_PATH/competitions/views/practitioner_dashboard.py" "$PRODUCTION_PATH/competitions/views/"
    fi
    
    success "Vues déployées"
}

deploy_corrected_templates() {
    info "📄 Déploiement des templates corrigés..."
    
    # Copier les templates practitioner si modifiés
    if [ -d "$LOCAL_PATH/competitions/templates/competitions/practitioner/" ]; then
        cp -r "$LOCAL_PATH/competitions/templates/competitions/practitioner/" "$PRODUCTION_PATH/competitions/templates/competitions/"
    fi
    
    success "Templates déployés"
}

deploy_settings_if_needed() {
    info "⚙️ Vérification des settings..."
    
    # Comparer les settings locaux et production
    if ! diff -q "$LOCAL_PATH/config/settings.py" "$PRODUCTION_PATH/config/settings.py" > /dev/null; then
        warning "Les settings diffèrent - déploiement conditionnel"
        
        # Copier seulement si les settings locaux sont valides
        if python3 -m py_compile "$LOCAL_PATH/config/settings.py"; then
            cp "$LOCAL_PATH/config/settings.py" "$PRODUCTION_PATH/config/"
            success "Settings mis à jour"
        else
            warning "Settings locaux invalides - conservation des settings production"
        fi
    else
        info "Settings identiques - pas de mise à jour nécessaire"
    fi
}

verify_production_syntax() {
    info "🧪 Vérification syntaxe en production..."
    
    cd "$PRODUCTION_PATH"
    
    # Test de syntaxe Python sur les fichiers critiques
    if python3 -m py_compile competitions/views/__init__.py; then
        success "Syntaxe views/__init__.py valide"
    else
        error "Syntaxe views/__init__.py invalide"
    fi
    
    if python3 -m py_compile competitions/views/club/__init__.py; then
        success "Syntaxe club/__init__.py valide"
    else
        error "Syntaxe club/__init__.py invalide"
    fi
    
    if python3 -m py_compile config/settings.py; then
        success "Syntaxe settings.py valide"
    else
        error "Syntaxe settings.py invalide"
    fi
}

restart_production_django() {
    info "🔄 Redémarrage Django en production..."
    
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    
    # Arrêter tous les processus Django
    pkill -f "python.*manage.py" || true
    pkill -f "runserver" || true
    pkill -f "gunicorn" || true
    sleep 3
    
    # Vérifier la configuration Django
    if python manage.py check --deploy; then
        success "Configuration Django valide"
    else
        error "Configuration Django invalide"
    fi
    
    # Collecter les fichiers statiques
    python manage.py collectstatic --noinput || warning "Erreur collectstatic"
    
    # Redémarrer avec gunicorn (production)
    nohup gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 > /tmp/gunicorn_production.log 2>&1 &
    
    sleep 5
    
    if pgrep -f "gunicorn" > /dev/null; then
        success "Gunicorn démarré en production"
    else
        warning "Gunicorn non démarré - tentative avec runserver"
        nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_production.log 2>&1 &
        sleep 3
        
        if pgrep -f "runserver" > /dev/null; then
            success "Django runserver démarré"
        else
            error "Échec du démarrage Django"
        fi
    fi
}

test_production_urls() {
    info "🧪 Test des URLs en production..."
    
    # Test des URLs critiques
    local urls=(
        "https://martialcomp.com/"
        "https://martialcomp.com/fr/competitions/practitioner/profile/"
        "https://martialcomp.com/fr/competitions/club/dashboard/"
        "https://martialcomp.com/fr/competitions/practitioner/dashboard/"
    )
    
    for url in "${urls[@]}"; do
        local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        
        if [[ "$status" =~ ^(200|301|302)$ ]]; then
            success "$url (statut: $status)"
        else
            warning "$url non accessible (statut: $status)"
        fi
    done
}

rollback_if_needed() {
    if [ -f /tmp/production_backup_path ]; then
        local backup_dir=$(cat /tmp/production_backup_path)
        
        warning "Rollback disponible si nécessaire:"
        echo "# Restaurer les vues:"
        echo "cp -r $backup_dir/views_backup/* $PRODUCTION_PATH/competitions/views/"
        echo "# Restaurer les templates:"
        echo "cp -r $backup_dir/templates_backup/* $PRODUCTION_PATH/competitions/templates/"
        echo "# Restaurer settings:"
        echo "cp $backup_dir/settings.py $PRODUCTION_PATH/config/"
    fi
}

main() {
    info "🚀 DÉPLOIEMENT PRODUCTION - CORRECTIONS DASHBOARDS"
    info "================================================="
    
    create_production_backup
    deploy_corrected_views
    deploy_corrected_templates
    deploy_settings_if_needed
    verify_production_syntax
    restart_production_django
    test_production_urls
    rollback_if_needed
    
    success "🎉 DÉPLOIEMENT TERMINÉ"
    info "================================================="
    info "URLs à tester:"
    info "• https://martialcomp.com/fr/competitions/practitioner/profile/"
    info "• https://martialcomp.com/fr/competitions/club/dashboard/"
    info "• https://martialcomp.com/fr/competitions/practitioner/dashboard/"
    info ""
    info "Logs:"
    info "• tail -f /tmp/gunicorn_production.log"
    info "• tail -f /tmp/django_production.log"
}

main "$@"