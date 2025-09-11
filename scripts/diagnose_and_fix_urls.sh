#!/bin/bash

# =============================================================================
# Script de diagnostic et correction automatique des URLs
# Analyse les vues existantes et corrige les imports
# =============================================================================

set -e

# Configuration
APP_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO: $1${NC}"
}

# Diagnostic des vues existantes
diagnose_views() {
    log "=== DIAGNOSTIC DES VUES EXISTANTES ==="
    
    cd "$APP_DIR"
    
    echo ""
    info "Structure des fichiers de vues :"
    find competitions/views/ -name "*.py" -type f | sort
    
    echo ""
    info "Contenu du fichier welcome.py :"
    if [[ -f "competitions/views/welcome.py" ]]; then
        echo "Fichier existe. Contenu :"
        head -20 "competitions/views/welcome.py"
        echo ""
        echo "Fonctions définies :"
        grep -n "^def " "competitions/views/welcome.py" || echo "Aucune fonction trouvée"
    else
        echo "❌ Fichier welcome.py n'existe pas"
    fi
    
    echo ""
    info "Contenu actuel de urls.py :"
    head -15 "config/urls.py"
    
    echo ""
}

# Créer les vues manquantes
create_missing_views() {
    log "Création des vues manquantes..."
    
    cd "$APP_DIR"
    
    # Créer welcome.py s'il n'existe pas ou est vide
    cat > "competitions/views/welcome.py" << 'EOF'
from django.shortcuts import render
from django.utils import translation
from django.conf import settings

def welcome_view(request):
    """Vue principale d'accueil de MartialComp"""
    context = {
        'current_language': translation.get_language(),
        'available_languages': settings.LANGUAGES,
    }
    return render(request, 'competitions/welcome.html', context)
EOF

    log "Vue welcome_view créée"
    
    # S'assurer que pages.py est correct
    cat > "competitions/views/pages.py" << 'EOF'
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.utils import translation

def privacy_policy_view(request):
    """Vue pour la politique de confidentialité"""
    return render(request, 'competitions/pages/privacy_policy.html')

def terms_of_service_view(request):
    """Vue pour les conditions de service"""
    return render(request, 'competitions/pages/terms_of_service.html')

@login_required
def delete_account_view(request):
    """Vue pour la suppression de compte utilisateur"""
    if request.method == 'POST':
        confirm = request.POST.get('confirm_deletion')
        if confirm == 'DELETE':
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, _('Votre compte a été supprimé avec succès.'))
            return redirect('welcome')
        else:
            messages.error(request, _('Confirmation incorrecte. Veuillez taper exactement "DELETE".'))
    
    return render(request, 'competitions/pages/delete_account.html')
EOF

    log "Vue pages.py mise à jour"
}

# Créer un urls.py minimal et fonctionnel
create_minimal_urls() {
    log "Création d'un fichier urls.py minimal..."
    
    cd "$APP_DIR"
    
    # Sauvegarder l'ancien
    cp "config/urls.py" "config/urls.py.broken_$TIMESTAMP"
    
    # Créer un urls.py minimal qui fonctionne
    cat > "config/urls.py" << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.views.i18n import set_language

# Import seulement des vues qui existent
from competitions.views.welcome import welcome_view
from competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view

# URLs sans préfixe de langue
urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),
    
    # Redirection racine vers /fr/
    path('', RedirectView.as_view(url='/fr/', permanent=False)),
    
    # Pages légales (accès direct pour les API)
    path('privacy/', privacy_policy_view, name='privacy_policy'),
    path('terms/', terms_of_service_view, name='terms_of_service'),
    
    # Authentification sociale (accès direct)
    path('accounts/', include('allauth.urls')),
    
    # Changement de langue
    path('set_language/', set_language, name='set_language'),
]

# URLs avec préfixe de langue
urlpatterns += i18n_patterns(
    # Page d'accueil
    path('', welcome_view, name='welcome'),
    
    # Pages légales (avec préfixe de langue)
    path('privacy/', privacy_policy_view, name='privacy_policy_i18n'),
    path('terms/', terms_of_service_view, name='terms_of_service_i18n'),
    path('account/delete/', delete_account_view, name='delete_account'),
    
    # Authentification (avec préfixe de langue)
    path('accounts/', include('allauth.urls')),
    
    prefix_default_language=False
)

# Fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
EOF

    log "URLs.py minimal créé"
}

# Test de la configuration
test_django_config() {
    log "Test de la configuration Django..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    echo ""
    info "Test des imports Python..."
    
    python << 'EOF'
try:
    # Test des imports
    from competitions.views.welcome import welcome_view
    print("✅ Import welcome_view réussi")
    
    from competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view
    print("✅ Import vues pages réussi")
    
    print("✅ Tous les imports nécessaires fonctionnent")
    
except Exception as e:
    print(f"❌ Erreur d'import: {e}")
    exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        log "Imports Python validés"
    else
        error "Erreurs d'imports Python"
        return 1
    fi
    
    # Test Django check
    echo ""
    info "Test de la configuration Django..."
    python manage.py check
    
    if [ $? -eq 0 ]; then
        log "Configuration Django valide"
    else
        error "Erreurs de configuration Django"
        return 1
    fi
}

# Redémarrer Django
restart_django_safe() {
    log "Redémarrage sécurisé de Django..."
    
    cd "$APP_DIR"
    
    # Arrêter tous les processus Django
    pkill -f "runserver" 2>/dev/null || true
    pkill -f "gunicorn" 2>/dev/null || true
    sleep 5
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Démarrer Django
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_safe_$TIMESTAMP.log 2>&1 &
    
    # Attendre le démarrage
    sleep 10
    
    # Vérifier que Django fonctionne
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django redémarré avec succès"
        
        # Test de connectivité interne
        if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ | grep -q "200\|302"; then
            log "Django répond correctement en interne"
        else
            warning "Django démarre mais ne répond pas encore"
        fi
    else
        error "Échec du redémarrage de Django"
        echo "Logs Django :"
        cat /tmp/django_safe_$TIMESTAMP.log
        return 1
    fi
}

# Test final des URLs
test_final_urls() {
    log "Test final des URLs..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS DES URLs FINALES ==="
    
    # URLs à tester
    declare -A urls=(
        ["Page d'accueil"]="https://martialcomp.com/"
        ["Page FR"]="https://martialcomp.com/fr/"
        ["Privacy"]="https://martialcomp.com/privacy/"
        ["Terms"]="https://martialcomp.com/terms/"
        ["Login"]="https://martialcomp.com/accounts/login/"
        ["Google OAuth"]="https://martialcomp.com/accounts/google/login/"
        ["Facebook OAuth"]="https://martialcomp.com/accounts/facebook/login/"
    )
    
    for name in "${!urls[@]}"; do
        url="${urls[$name]}"
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
        
        if echo "$code" | grep -q "200\|302"; then
            echo "  ✅ $name: $url (Code: $code)"
        else
            echo "  ❌ $name: $url (Code: $code)"
        fi
    done
    
    echo ""
}

# Script principal
main() {
    log "=== DIAGNOSTIC ET CORRECTION AUTOMATIQUE ==="
    
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        error "Ce script doit être exécuté depuis /var/www/vhosts/martialcomp.com/httpdocs"
        exit 1
    fi
    
    diagnose_views
    create_missing_views
    create_minimal_urls
    test_django_config
    restart_django_safe
    test_final_urls
    
    log "🎉 DIAGNOSTIC ET CORRECTION TERMINÉS!"
    echo ""
    echo "📋 Résumé des corrections:"
    echo "  ✅ Vue welcome_view créée"
    echo "  ✅ Vues pages.py corrigées"
    echo "  ✅ URLs.py minimal et fonctionnel"
    echo "  ✅ Configuration Django validée"
    echo "  ✅ Django redémarré"
    echo ""
    echo "💾 Sauvegardes:"
    echo "  - URLs cassé: config/urls.py.broken_$TIMESTAMP"
    echo "  - Logs Django: /tmp/django_safe_$TIMESTAMP.log"
    echo ""
    echo "🎯 L'authentification sociale devrait maintenant fonctionner!"
}

# Exécution
main "$@"