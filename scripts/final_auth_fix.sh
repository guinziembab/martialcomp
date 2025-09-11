#!/bin/bash

# =============================================================================
# Script de correction finale pour l'authentification
# Approche simple et directe
# =============================================================================

set -e

# Configuration
APP_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs
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

# Correction simple du fichier urls.py
fix_urls_simple() {
    log "Correction simple du fichier urls.py..."
    
    cd "$APP_DIR"
    
    # Sauvegarder
    cp "config/urls.py" "config/urls.py.backup_final_$TIMESTAMP"
    
    # Le fichier welcome.py a une fonction 'welcome', pas 'welcome_view'
    # Créer un urls.py qui utilise la fonction existante
    cat > "config/urls.py" << 'EOF'
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.views.i18n import set_language

# Import des vues existantes (nom correct: welcome, pas welcome_view)
from competitions.views.welcome import welcome
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
    # Page d'accueil (utilise la fonction 'welcome' existante)
    path('', welcome, name='welcome'),
    
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

    log "URLs.py corrigé avec les noms de fonctions existants"
}

# Test rapide de la syntaxe Django
test_django_syntax() {
    log "Test rapide de la syntaxe Django..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Test basique sans configuration complète
    python -c "
import os
import sys
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    
    # Test des imports
    from competitions.views.welcome import welcome
    print('✅ Import welcome réussi')
    
    from competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view
    print('✅ Import pages réussi')
    
    print('✅ Configuration Django OK')
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        log "Syntaxe Django validée"
    else
        error "Erreurs de syntaxe Django"
        return 1
    fi
}

# Redémarrage simple de Django
restart_django_simple() {
    log "Redémarrage simple de Django..."
    
    cd "$APP_DIR"
    
    # Arrêter tout
    pkill -f "runserver" 2>/dev/null || true
    sleep 3
    
    # Activer venv et démarrer
    source venv/bin/activate
    
    # Démarrer en arrière-plan
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_final_$TIMESTAMP.log 2>&1 &
    
    # Attendre
    sleep 15
    
    # Vérifier
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django démarré"
        
        # Test simple de connectivité
        sleep 5
        if curl -s http://127.0.0.1:8000/ | grep -q "html\|<!DOCTYPE\|<title>" 2>/dev/null; then
            log "Django répond avec du HTML"
        else
            warning "Django démarre mais répond étrangement"
        fi
    else
        error "Échec du démarrage Django"
        echo "Dernières lignes du log :"
        tail -20 /tmp/django_final_$TIMESTAMP.log
        return 1
    fi
}

# Test final simple
test_final_simple() {
    log "Test final simple..."
    
    echo ""
    echo "=== TESTS SIMPLES DES URLs ==="
    
    # Test seulement les URLs principales
    urls=(
        "https://martialcomp.com/"
        "https://martialcomp.com/fr/"
        "https://martialcomp.com/privacy/"
        "https://martialcomp.com/terms/"
        "https://martialcomp.com/accounts/login/"
    )
    
    for url in "${urls[@]}"; do
        code=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "timeout")
        
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url (Code: $code)"
        else
            echo "  ❌ $url (Code: $code)"
        fi
    done
    
    echo ""
}

# Vérifier la connectivité Nginx
test_nginx_proxy() {
    log "Test de la connectivité Nginx..."
    
    echo ""
    echo "=== TEST DE LA CHAÎNE NGINX -> DJANGO ==="
    
    # Test direct Django
    django_code=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "failed")
    echo "  Django direct (127.0.0.1:8000): $django_code"
    
    # Test via Nginx
    nginx_code=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ 2>/dev/null || echo "failed")
    echo "  Nginx proxy (https://martialcomp.com): $nginx_code"
    
    if [[ "$django_code" =~ ^(200|302)$ ]] && [[ "$nginx_code" =~ ^(200|302)$ ]]; then
        log "✅ Chaîne Nginx -> Django fonctionnelle"
    elif [[ "$django_code" =~ ^(200|302)$ ]] && [[ ! "$nginx_code" =~ ^(200|302)$ ]]; then
        warning "Django fonctionne mais problème de proxy Nginx"
    else
        error "Problème au niveau de Django"
    fi
    
    echo ""
}

# Script principal
main() {
    log "=== CORRECTION FINALE AUTHENTIFICATION ==="
    
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        error "Ce script doit être exécuté depuis /var/www/vhosts/martialcomp.com/httpdocs"
        exit 1
    fi
    
    fix_urls_simple
    test_django_syntax
    restart_django_simple
    test_nginx_proxy
    test_final_simple
    
    log "🎉 CORRECTION FINALE TERMINÉE!"
    echo ""
    echo "📋 Résumé:"
    echo "  ✅ URLs.py corrigé avec les bonnes fonctions"
    echo "  ✅ Django redémarré"
    echo "  ✅ Tests de connectivité effectués"
    echo ""
    echo "💾 Logs et sauvegardes:"
    echo "  - Backup URLs: config/urls.py.backup_final_$TIMESTAMP"
    echo "  - Log Django: /tmp/django_final_$TIMESTAMP.log"
    echo ""
    
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        echo "🎯 Django est démarré. Testez: https://martialcomp.com/"
        echo ""
        echo "🔐 URLs d'authentification:"
        echo "  - Connexion: https://martialcomp.com/accounts/login/"
        echo "  - Google: https://martialcomp.com/accounts/google/login/"
        echo "  - Facebook: https://martialcomp.com/accounts/facebook/login/"
    else
        echo "❌ Django ne répond pas - Vérifiez les logs"
    fi
}

# Exécution
main "$@"