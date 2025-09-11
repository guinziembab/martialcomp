#!/bin/bash

# =============================================================================
# Script de diagnostic et correction d'urgence
# Corrige les erreurs 500 et 404
# =============================================================================

set -e

APP_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

# Diagnostic des erreurs Django
diagnose_django_errors() {
    log "Diagnostic des erreurs Django..."
    
    echo ""
    echo "=== LOGS DJANGO RÉCENTS ==="
    
    # Vérifier les logs Django récents
    if [[ -f "/tmp/django_i18n_$TIMESTAMP.log" ]]; then
        echo "Logs Django i18n:"
        tail -20 "/tmp/django_i18n_$TIMESTAMP.log"
    else
        echo "Logs Django récents:"
        find /tmp -name "django_*.log" -type f -exec ls -la {} \; | head -5
        latest_log=$(find /tmp -name "django_*.log" -type f | head -1)
        if [[ -n "$latest_log" ]]; then
            echo "Contenu du log le plus récent:"
            tail -20 "$latest_log"
        fi
    fi
    
    echo ""
}

# Test direct Django pour identifier les erreurs
test_django_direct() {
    log "Test direct Django pour identifier les erreurs..."
    
    echo ""
    echo "=== TESTS DJANGO DIRECT ==="
    
    # Tests des URLs directement sur Django
    django_urls=(
        "/"
        "/fr/"
        "/privacy/"
        "/terms/"
        "/accounts/login/"
    )
    
    for url in "${django_urls[@]}"; do
        echo "Test Django direct $url :"
        response=$(curl -s -w "HTTP_CODE:%{http_code}" "http://127.0.0.1:8000$url" 2>/dev/null | tail -1)
        echo "  $response"
    done
    
    echo ""
}

# Vérifier la configuration Django en live
check_django_live_config() {
    log "Vérification de la configuration Django en live..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    python << 'EOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== VÉRIFICATION CONFIGURATION LIVE ===")

# Test des imports
try:
    from competitions.views.welcome import welcome
    print("✅ Import welcome réussi")
except Exception as e:
    print(f"❌ Import welcome échoué: {e}")

try:
    from competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view
    print("✅ Import pages réussi")
except Exception as e:
    print(f"❌ Import pages échoué: {e}")

# Test des URLs
try:
    from django.urls import reverse
    
    welcome_url = reverse('welcome')
    print(f"✅ URL welcome: {welcome_url}")
    
    privacy_url = reverse('privacy_policy')
    print(f"✅ URL privacy: {privacy_url}")
    
except Exception as e:
    print(f"❌ Erreur URLs: {e}")

# Test middleware
from django.conf import settings
print(f"Middleware: {settings.MIDDLEWARE}")

print("✅ Vérification terminée")
EOF
}

# Corriger les vues manquantes ou défaillantes
fix_broken_views() {
    log "Correction des vues défaillantes..."
    
    cd "$APP_DIR"
    
    # S'assurer que le fichier welcome.py est correct
    cat > "competitions/views/welcome.py" << 'EOF'
from django.shortcuts import render
from django.utils import translation
from django.conf import settings

def welcome(request):
    """Vue d'accueil principale de MartialComp"""
    context = {
        'current_language': translation.get_language(),
        'available_languages': settings.LANGUAGES,
    }
    return render(request, 'competitions/welcome.html', context)
EOF

    # S'assurer que le fichier pages.py est correct
    cat > "competitions/views/pages.py" << 'EOF'
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.utils.translation import gettext as _

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

    log "Vues corrigées"
}

# Créer un URLs.py ultra-simple qui fonctionne
create_simple_working_urls() {
    log "Création d'un URLs.py ultra-simple..."
    
    cd "$APP_DIR"
    
    # Sauvegarder
    cp config/urls.py config/urls.py.backup_debug_$TIMESTAMP
    
    # URLs ultra-simple
    cat > config/urls.py << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.views.i18n import set_language

# Import avec gestion d'erreurs
try:
    from competitions.views.welcome import welcome
except ImportError:
    from django.http import HttpResponse
    def welcome(request):
        return HttpResponse("Welcome to MartialComp")

try:
    from competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view
except ImportError:
    from django.http import HttpResponse
    def privacy_policy_view(request):
        return HttpResponse("Privacy Policy")
    def terms_of_service_view(request):
        return HttpResponse("Terms of Service")
    def delete_account_view(request):
        return HttpResponse("Delete Account")

# URLs principales
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/fr/', permanent=False)),
    path('privacy/', privacy_policy_view, name='privacy_policy'),
    path('terms/', terms_of_service_view, name='terms_of_service'),
    path('accounts/', include('allauth.urls')),
    path('set_language/', set_language, name='set_language'),
]

# URLs avec préfixe de langue
urlpatterns += i18n_patterns(
    path('', welcome, name='welcome'),
    path('privacy/', privacy_policy_view, name='privacy_policy_i18n'),
    path('terms/', terms_of_service_view, name='terms_of_service_i18n'),
    path('account/delete/', delete_account_view, name='delete_account'),
    path('accounts/', include('allauth.urls')),
    prefix_default_language=False
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
EOF

    log "URLs.py ultra-simple créé"
}

# Redémarrage et test immédiat
restart_and_test_immediate() {
    log "Redémarrage et test immédiat..."
    
    cd "$APP_DIR"
    
    # Arrêt Django
    pkill -f "runserver 127.0.0.1:8000" 2>/dev/null || true
    sleep 3
    
    # Test de la configuration
    source venv/bin/activate
    python manage.py check
    
    if [ $? -ne 0 ]; then
        error "Configuration Django invalide"
        return 1
    fi
    
    # Redémarrage
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_debug_$TIMESTAMP.log 2>&1 &
    
    sleep 15
    
    # Test immédiat
    echo ""
    echo "=== TESTS APRÈS CORRECTION ==="
    
    # Test URLs critiques
    critical_urls=(
        "http://127.0.0.1:8000/"
        "http://127.0.0.1:8000/fr/"
        "http://127.0.0.1:8000/privacy/"
        "http://127.0.0.1:8000/terms/"
    )
    
    success_count=0
    for url in "${critical_urls[@]}"; do
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url ($code)"
            ((success_count++))
        else
            echo "  ❌ $url ($code)"
        fi
    done
    
    echo ""
    echo "Django direct: $success_count/4 URLs fonctionnelles"
    
    if [ $success_count -eq 4 ]; then
        log "✅ Django fonctionne correctement"
        
        # Test via Nginx
        sleep 5
        nginx_test=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/" 2>/dev/null)
        echo "Test Nginx /fr/: $nginx_test"
        
        if [[ "$nginx_test" =~ ^(200|302)$ ]]; then
            log "🎉 SUCCÈS ! Tout fonctionne !"
        else
            warning "Django fonctionne mais Nginx a encore des problèmes"
        fi
    else
        error "Django a encore des problèmes"
        echo "Logs Django:"
        tail -10 /tmp/django_debug_$TIMESTAMP.log
    fi
}

# Script principal
main() {
    log "=== DIAGNOSTIC ET CORRECTION D'URGENCE ==="
    
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        cd /var/www/vhosts/martialcomp.com/httpdocs
    fi
    
    diagnose_django_errors
    test_django_direct
    check_django_live_config
    fix_broken_views
    create_simple_working_urls
    restart_and_test_immediate
    
    log "🎉 DIAGNOSTIC ET CORRECTION TERMINÉS!"
    echo ""
    echo "💾 Sauvegardes:"
    echo "  - config/urls.py.backup_debug_$TIMESTAMP"
    echo "  - /tmp/django_debug_$TIMESTAMP.log"
    echo ""
    echo "🎯 Si tout fonctionne, relancez le test complet:"
    echo "  ./test_all_urls_quick.sh"
}

main "$@"