#!/bin/bash

################################################################################
# SCRIPT DE DEBUG ET CORRECTION DÉPLOIEMENT
################################################################################

REMOTE_SERVER="martialcomp.com"
REMOTE_USER="root"

info() {
    echo -e "\033[0;34mℹ️ $1\033[0m"
}

success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

warning() {
    echo -e "\033[1;33m⚠️ $1\033[0m"
}

debug_server_state() {
    info "🔍 Diagnostic du serveur..."
    
    ssh $REMOTE_USER@$REMOTE_SERVER << 'EOF'
echo "📁 Contenu de /tmp :"
ls -la /tmp/ | grep martial

echo ""
echo "📦 Vérification du fichier transféré :"
if [ -f "/tmp/martialcomp_fixes_20250623_172300.tar.gz" ]; then
    echo "✅ Fichier trouvé"
    echo "📊 Taille : $(du -h /tmp/martialcomp_fixes_20250623_172300.tar.gz)"
    
    echo ""
    echo "🧪 Test d'extraction :"
    cd /tmp
    tar -tzf martialcomp_fixes_20250623_172300.tar.gz | head -5
    
    echo ""
    echo "📂 Tentative d'extraction :"
    tar -xzf martialcomp_fixes_20250623_172300.tar.gz
    
    echo ""
    echo "📁 Vérification extraction :"
    ls -la | grep martial
    
else
    echo "❌ Fichier non trouvé"
fi
EOF
}

manual_installation() {
    info "🔧 Installation manuelle étape par étape..."
    
    ssh $REMOTE_USER@$REMOTE_SERVER << 'EOF'
echo "🚀 Début installation manuelle..."

cd /tmp

# Vérifier le fichier
if [ ! -f "martialcomp_fixes_20250623_172300.tar.gz" ]; then
    echo "❌ Fichier package non trouvé"
    exit 1
fi

# Extraction
echo "📦 Extraction du package..."
tar -xzf martialcomp_fixes_20250623_172300.tar.gz

# Vérifier l'extraction
if [ ! -d "martialcomp_deployment_20250623_172300" ]; then
    echo "❌ Répertoire d'extraction non trouvé"
    ls -la | grep martial
    exit 1
fi

echo "✅ Extraction réussie"

# Aller dans le répertoire
cd martialcomp_deployment_20250623_172300

# Rendre exécutable le script
chmod +x install_on_server.sh

echo "🎯 Contenu du répertoire :"
ls -la

echo ""
echo "🚀 Lancement de l'installation..."
./install_on_server.sh
EOF
}

quick_fix() {
    info "⚡ Correction rapide directe..."
    
    ssh $REMOTE_USER@$REMOTE_SERVER << 'EOF'
echo "🔧 Correction directe en production..."

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/httpdocs/venv"

# Vérifier les chemins
if [ ! -d "$PRODUCTION_PATH" ]; then
    echo "❌ Chemin production non trouvé: $PRODUCTION_PATH"
    echo "📁 Recherche du bon chemin..."
    find /var -name "manage.py" 2>/dev/null | head -3
    exit 1
fi

cd "$PRODUCTION_PATH"

# Sauvegarde rapide
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
cp -r competitions/views/ "/tmp/views_backup_$TIMESTAMP/" 2>/dev/null || true

# Correction du fichier views/__init__.py
echo "🔧 Correction du fichier views/__init__.py..."

cat > competitions/views/__init__.py << 'VIEW_INIT_EOF'
# Importer toutes les vues pour qu'elles soient accessibles depuis competitions.views

# Vues d'authentification
from .auth import logout_view, login_view, signup_view

# Vues d'accueil
from .welcome import welcome
from .home import home

# Vues de dashboard
from .dashboard.base import dashboard
from .dashboard.admin import admin_dashboard
from .dashboard.club import club_dashboard

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
    'welcome', 'home',
    'dashboard', 'admin_dashboard', 'club_dashboard',
    'profile', 'activities', 'grades', 'competitions',
    'memberships', 'statistics',
    'practitioner_dashboard', 'practitioner_profile'
]
VIEW_INIT_EOF

echo "✅ Fichier views/__init__.py reconstruit"

# Correction des redirect() dans practitioner_dashboard.py
if [ -f "competitions/views/practitioner_dashboard.py" ]; then
    echo "🔧 Correction des URLs dans practitioner_dashboard.py..."
    
    sed -i "s/reverse('practitioner_profile')/reverse('competitions:practitioner:profile')/g" competitions/views/practitioner_dashboard.py
    sed -i "s/reverse('practitioner_dashboard')/reverse('competitions:practitioner:dashboard')/g" competitions/views/practitioner_dashboard.py
    sed -i 's/reverse("practitioner_profile")/reverse("competitions:practitioner:profile")/g' competitions/views/practitioner_dashboard.py
    sed -i 's/reverse("practitioner_dashboard")/reverse("competitions:practitioner:dashboard")/g' competitions/views/practitioner_dashboard.py
    
    echo "✅ URLs corrigées"
fi

# Test de syntaxe
echo "🧪 Test de syntaxe..."
if python3 -m py_compile competitions/views/__init__.py; then
    echo "✅ Syntaxe valide"
else
    echo "❌ Erreur syntaxe"
    exit 1
fi

# Redémarrage Django
echo "🔄 Redémarrage Django..."
source "$VENV_PATH/bin/activate" || echo "⚠️ Venv non trouvé"

pkill -f "python.*manage.py" || true
pkill -f "runserver" || true
pkill -f "gunicorn" || true
sleep 3

# Test configuration
if python manage.py check; then
    echo "✅ Configuration Django valide"
else
    echo "❌ Configuration Django invalide"
    python manage.py check
    exit 1
fi

# Redémarrer
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_fixed_manual.log 2>&1 &
sleep 5

if pgrep -f "runserver" > /dev/null; then
    echo "✅ Django redémarré avec succès"
    
    # Test rapide
    if curl -s -f "http://localhost:8000/" > /dev/null; then
        echo "✅ Site accessible en local"
    else
        echo "⚠️ Site potentiellement inaccessible"
    fi
else
    echo "❌ Échec redémarrage Django"
    tail -10 /tmp/django_fixed_manual.log
fi

echo ""
echo "🎯 Installation terminée !"
echo "📋 URLs à tester :"
echo "• https://martialcomp.com/"
echo "• https://martialcomp.com/fr/competitions/practitioner/profile/"
echo "• https://martialcomp.com/fr/competitions/club/dashboard/"
echo ""
echo "📁 Sauvegarde dans: /tmp/views_backup_$TIMESTAMP/"
EOF
}

test_deployment() {
    info "🧪 Test du déploiement..."
    
    sleep 5
    
    echo "🌐 Test des URLs principales :"
    
    # Test page d'accueil
    if curl -s -f "https://martialcomp.com/" > /dev/null; then
        success "Page d'accueil accessible"
    else
        warning "Page d'accueil inaccessible"
    fi
    
    # Test profil practitioner
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/practitioner/profile/" 2>/dev/null)
    if [[ "$status" =~ ^(200|301|302)$ ]]; then
        success "Profil practitioner accessible (statut: $status)"
    else
        warning "Profil practitioner non accessible (statut: $status)"
    fi
}

main() {
    echo "🚨 DEBUG ET CORRECTION DÉPLOIEMENT MARTIALCOMP"
    echo "============================================="
    
    case "${1:-debug}" in
        "debug"|"-d")
            debug_server_state
            ;;
        "manual"|"-m")
            manual_installation
            test_deployment
            ;;
        "quick"|"-q")
            quick_fix
            test_deployment
            ;;
        *)
            echo "Usage: $0 [debug|manual|quick]"
            echo ""
            echo "debug  - Diagnostique l'état du serveur"
            echo "manual - Installation manuelle du package"
            echo "quick  - Correction rapide directe"
            ;;
    esac
}

main "$@"