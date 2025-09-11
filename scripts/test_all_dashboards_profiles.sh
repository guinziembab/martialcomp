#!/bin/bash

################################################################################
# SCRIPT DE TEST - ACCESSIBILITÉ DES PROFILS DANS TOUS LES DASHBOARDS
################################################################################

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
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
}

info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

test_url_accessibility() {
    local url=$1
    local description=$2
    
    # Test avec localhost (sans authentification)
    local status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$url" 2>/dev/null)
    
    if [[ "$status" =~ ^(200|301|302)$ ]]; then
        success "$description accessible (statut: $status)"
        return 0
    else
        warning "$description non accessible (statut: $status)"
        return 1
    fi
}

test_dashboard_structure() {
    local dashboard_path=$1
    local dashboard_name=$2
    
    info "🔍 Test du dashboard $dashboard_name..."
    
    # URLs principales à tester
    local urls=(
        "$dashboard_path/"
        "$dashboard_path/profile/"
        "$dashboard_path/settings/"
    )
    
    local accessible_count=0
    local total_count=${#urls[@]}
    
    for url in "${urls[@]}"; do
        if test_url_accessibility "$url" "  $dashboard_name - $url"; then
            ((accessible_count++))
        fi
    done
    
    echo "  📊 Résultat: $accessible_count/$total_count URLs accessibles"
    echo ""
}

verify_template_structure() {
    info "🔧 Vérification de la structure des templates..."
    
    cd "$PRODUCTION_PATH"
    
    # Vérifier les templates practitioner
    info "Templates practitioner:"
    if [ -d "competitions/templates/competitions/practitioner/" ]; then
        find competitions/templates/competitions/practitioner/ -name "*.html" -exec basename {} \; | sort
    else
        warning "Répertoire templates practitioner non trouvé"
    fi
    
    echo ""
    
    # Vérifier les templates club
    info "Templates club:"
    if [ -d "competitions/templates/competitions/club/" ]; then
        find competitions/templates/competitions/club/ -name "*.html" -exec basename {} \; | sort
    else
        warning "Répertoire templates club non trouvé"
    fi
    
    echo ""
    
    # Vérifier les templates federation
    info "Templates federation:"
    if [ -d "competitions/templates/competitions/federation/" ]; then
        find competitions/templates/competitions/federation/ -name "*.html" -exec basename {} \; | sort
    else
        warning "Répertoire templates federation non trouvé"
    fi
    
    echo ""
}

check_profile_related_views() {
    info "🔍 Vérification des vues liées aux profils..."
    
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    
    # Lister toutes les URLs disponibles
    python manage.py show_urls 2>/dev/null | grep -E "(profile|dashboard)" || echo "Commande show_urls non disponible"
    
    # Alternative : vérifier les URLs dans le code
    echo ""
    info "URLs contenant 'profile' dans competitions/urls.py:"
    grep -n "profile" competitions/urls.py 2>/dev/null || echo "Aucune URL profile trouvée"
    
    echo ""
    info "URLs contenant 'dashboard' dans competitions/urls.py:"
    grep -n "dashboard" competitions/urls.py 2>/dev/null || echo "Aucune URL dashboard trouvée"
}

test_django_admin_access() {
    info "🔐 Test d'accès à l'administration Django..."
    
    test_url_accessibility "/admin/" "Administration Django"
    test_url_accessibility "/admin/competitions/" "Admin - Competitions"
    test_url_accessibility "/admin/auth/user/" "Admin - Utilisateurs"
}

generate_test_report() {
    info "📋 Génération du rapport de test..."
    
    local report_file="/tmp/dashboard_profile_test_report.txt"
    
    cat > "$report_file" << EOF
RAPPORT DE TEST - ACCESSIBILITÉ DES PROFILS DASHBOARDS
======================================================
Date: $(date)
Serveur: martialcomp.com
Status Django: $(pgrep -f runserver > /dev/null && echo "✅ Actif" || echo "❌ Inactif")

URLS TESTÉES:
EOF
    
    echo "📄 Rapport généré: $report_file"
    info "Contenu du rapport:"
    cat "$report_file"
}

main() {
    info "🚀 TEST COMPLET - ACCESSIBILITÉ PROFILS DASHBOARDS"
    info "=================================================="
    
    # Vérifier que Django fonctionne
    if ! pgrep -f "runserver" > /dev/null; then
        error "Django n'est pas en cours d'exécution"
        exit 1
    fi
    
    success "Django actif - début des tests"
    echo ""
    
    # Test des différents dashboards
    test_dashboard_structure "/fr/competitions/practitioner" "Practitioner"
    test_dashboard_structure "/fr/competitions/club" "Club"
    test_dashboard_structure "/fr/competitions/federation" "Federation"
    test_dashboard_structure "/fr/competitions/coach" "Coach"
    test_dashboard_structure "/fr/competitions/judge" "Judge"
    
    # Tests supplémentaires
    verify_template_structure
    check_profile_related_views
    test_django_admin_access
    
    # URLs spécifiques connues
    info "🎯 Test des URLs spécifiques connues:"
    test_url_accessibility "/fr/competitions/practitioner/profile/" "Profil Practitioner"
    test_url_accessibility "/fr/competitions/club/dashboard/" "Dashboard Club"
    test_url_accessibility "/fr/competitions/federations/dashboard/" "Dashboard Federation"
    
    success "🎉 TESTS TERMINÉS"
    info "=================================================="
    info "Si des dashboards ne sont pas accessibles, vérifiez:"
    info "• Les templates existent dans competitions/templates/"
    info "• Les URLs sont définies dans competitions/urls.py"
    info "• Les vues correspondantes existent"
    info "• L'authentification utilisateur est configurée"
}

main "$@"