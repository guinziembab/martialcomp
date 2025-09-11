#!/bin/bash

################################################################################
# SCRIPT RAPIDE - CORRECTION PRODUCTION MARTIALCOMP
# Utilise ce script si vous êtes directement sur le serveur de production
################################################################################

set -e

# Configuration (à adapter selon votre serveur)
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

fix_production_directly() {
    info "🔧 Correction directe en production..."
    
    cd "$PRODUCTION_PATH"
    
    # Sauvegarde rapide
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    cp -r competitions/views/ "/tmp/views_backup_$TIMESTAMP/" 2>/dev/null || true
    
    # Correction du fichier views/__init__.py si corrompu
    if ! python3 -c "import ast; ast.parse(open('competitions/views/__init__.py').read())"; then
        warning "Fichier views/__init__.py corrompu - reconstruction..."
        
        cat > competitions/views/__init__.py << 'VIEW_INIT_EOF'
# Importer toutes les vues pour qu'elles soient accessibles depuis competitions.views

# Vues d'authentification
from .auth import logout_view, login_view, signup_view

# Vues d'accueil
from .welcome import welcome
from .home import home
from .register_view import register_view

# Vues de dashboard (structure modulaire)
from .dashboard.base import dashboard
from .dashboard.admin import admin_dashboard
from .dashboard.club import club_dashboard
from .dashboard.referee import referee_dashboard
from .dashboard.participant import participant_dashboard
from .dashboard.spectator import spectator_dashboard
from .dashboard.pro import dashboard_pro
from .dashboard.manager import manager_dashboard
from .dashboard.federations import federation_dashboard

# Vues pratiquant
from .practitioner_dashboard import (
    dashboard,
    profile,
    activities,
    grades,
    competitions,
    memberships,
    statistics
)

# Alias pour la compatibilité
practitioner_dashboard = dashboard
practitioner_profile = profile

__all__ = [
    'logout_view', 'login_view', 'signup_view',
    'welcome', 'home', 'register_view',
    'dashboard', 'admin_dashboard', 'club_dashboard',
    'profile', 'activities', 'grades', 'competitions',
    'memberships', 'statistics',
    'practitioner_dashboard', 'practitioner_profile'
]
VIEW_INIT_EOF
        
        success "Fichier views/__init__.py reconstruit"
    fi
    
    # Correction des redirect() dans practitioner_dashboard.py
    if [ -f "competitions/views/practitioner_dashboard.py" ]; then
        info "Correction des redirect() dans practitioner_dashboard.py..."
        
        sed -i "s/reverse('practitioner_profile')/reverse('competitions:practitioner:profile')/g" competitions/views/practitioner_dashboard.py
        sed -i "s/reverse('practitioner_dashboard')/reverse('competitions:practitioner:dashboard')/g" competitions/views/practitioner_dashboard.py
        sed -i 's/reverse("practitioner_profile")/reverse("competitions:practitioner:profile")/g' competitions/views/practitioner_dashboard.py
        sed -i 's/reverse("practitioner_dashboard")/reverse("competitions:practitioner:dashboard")/g' competitions/views/practitioner_dashboard.py
        
        success "Redirects corrigés"
    fi
    
    # Test de syntaxe
    if python3 -m py_compile competitions/views/__init__.py; then
        success "Syntaxe views/__init__.py valide"
    else
        error "Syntaxe views/__init__.py invalide"
    fi
}

restart_django_production() {
    info "🔄 Redémarrage Django production..."
    
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    
    # Arrêter Django
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
    
    # Redémarrer
    nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_fixed_prod.log 2>&1 &
    sleep 5
    
    if pgrep -f "runserver" > /dev/null; then
        success "Django redémarré"
    else
        error "Échec redémarrage Django"
    fi
}

test_production_working() {
    info "🧪 Test du fonctionnement..."
    
    # Test local
    if curl -s -f "http://localhost:8000/" > /dev/null; then
        success "Site répond en local"
    else
        warning "Site ne répond pas en local"
    fi
    
    # Test profil practitioner
    status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/practitioner/profile/" 2>/dev/null)
    if [[ "$status" =~ ^(200|301|302)$ ]]; then
        success "Profil practitioner accessible (statut: $status)"
    else
        warning "Profil practitioner non accessible (statut: $status)"
    fi
    
    info "Logs récents:"
    tail -5 /tmp/django_fixed_prod.log 2>/dev/null || echo "Pas de logs"
}

main() {
    info "🚨 CORRECTION RAPIDE PRODUCTION"
    info "==============================="
    
    if [ ! -d "$PRODUCTION_PATH" ]; then
        error "Chemin production non trouvé: $PRODUCTION_PATH"
    fi
    
    fix_production_directly
    restart_django_production
    test_production_working
    
    success "🎉 CORRECTION TERMINÉE"
    info "======================================"
    info "URLs à tester:"
    info "• https://martialcomp.com/fr/competitions/practitioner/profile/"
    info "• https://martialcomp.com/fr/competitions/club/dashboard/"
    info ""
    info "Si problèmes persistent:"
    info "• tail -f /tmp/django_fixed_prod.log"
    info "• Sauvegarde dans: /tmp/views_backup_$(date +%Y%m%d)_*/"
}

main "$@"