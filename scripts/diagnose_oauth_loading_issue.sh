#!/bin/bash

# =============================================================================
# DIAGNOSTIC DES PAGES OAUTH NON CHARGÉES - MARTIALCOMP
# =============================================================================

set -e

echo "🔍 Diagnostic des pages OAuth Google/Facebook non chargées..."
echo "📅 $(date)"

cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

# =============================================================================
# 1. TESTS DE CONNECTIVITÉ DIRECTS
# =============================================================================

echo "🧪 Tests de connectivité OAuth..."

echo "📡 Test Google OAuth:"
curl -s -I "https://martialcomp.com/accounts/google/login/" || echo "❌ Erreur Google OAuth"

echo "📡 Test Facebook OAuth:"
curl -s -I "https://martialcomp.com/accounts/facebook/login/" || echo "❌ Erreur Facebook OAuth"

# =============================================================================
# 2. VÉRIFICATION DES TEMPLATES
# =============================================================================

echo "📁 Vérification des templates OAuth..."

# Vérifier l'existence des templates
echo "🔍 Templates Google:"
ls -la competitions/templates/socialaccount/providers/google/ 2>/dev/null || echo "❌ Dossier Google manquant"

echo "🔍 Templates Facebook:"
ls -la competitions/templates/socialaccount/providers/facebook/ 2>/dev/null || echo "❌ Dossier Facebook manquant"

# =============================================================================
# 3. VÉRIFICATION DES URLS DJANGO-ALLAUTH
# =============================================================================

echo "🔗 Vérification des URLs django-allauth..."

python manage.py shell << 'PYTHON_EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from django.urls import reverse
    from allauth.socialaccount import providers
    
    print("📊 Providers disponibles:")
    for provider_id in providers.registry.provider_map.keys():
        print(f"  - {provider_id}")
    
    # Test des URLs
    try:
        google_url = reverse('google_login')
        print(f"✅ URL Google: {google_url}")
    except Exception as e:
        print(f"❌ URL Google: {e}")
    
    try:
        facebook_url = reverse('facebook_login')
        print(f"✅ URL Facebook: {facebook_url}")
    except Exception as e:
        print(f"❌ URL Facebook: {e}")
        
except Exception as e:
    print(f"❌ Erreur d'importation: {e}")
PYTHON_EOF

# =============================================================================
# 4. VÉRIFICATION BASE DE DONNÉES SOCIAL APPS
# =============================================================================

echo "🗄️ Vérification des applications sociales en base..."

python manage.py shell << 'PYTHON_EOF'
try:
    from allauth.socialaccount.models import SocialApp
    
    apps = SocialApp.objects.all()
    print(f"📊 Applications sociales configurées: {apps.count()}")
    
    for app in apps:
        print(f"  - {app.provider}: {app.name} (ID: {app.client_id[:10]}...)")
        sites = app.sites.all()
        print(f"    Sites: {[site.domain for site in sites]}")
        
    if apps.count() == 0:
        print("❌ Aucune application sociale configurée!")
        
except Exception as e:
    print(f"❌ Erreur base de données: {e}")
PYTHON_EOF

# =============================================================================
# 5. VÉRIFICATION CONFIGURATION SETTINGS
# =============================================================================

echo "⚙️ Vérification configuration settings..."

python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from django.conf import settings
    
    print('📊 INSTALLED_APPS (allauth):')
    for app in settings.INSTALLED_APPS:
        if 'allauth' in app:
            print(f'  ✅ {app}')
    
    print(f'📊 SITE_ID: {getattr(settings, \"SITE_ID\", \"Non défini\")}')
    
    print('📊 AUTHENTICATION_BACKENDS:')
    for backend in getattr(settings, 'AUTHENTICATION_BACKENDS', []):
        print(f'  - {backend}')
        
except Exception as e:
    print(f'❌ Erreur settings: {e}')
"

# =============================================================================
# 6. TEST DES LOGS PASSENGER
# =============================================================================

echo "📝 Vérification des logs Passenger..."

if [[ -f "/tmp/passenger_debug.log" ]]; then
    echo "📋 Dernières lignes du log Passenger:"
    tail -20 /tmp/passenger_debug.log
else
    echo "❌ Pas de log Passenger trouvé"
fi

# =============================================================================
# 7. TESTS AVEC DJANGO RUNSERVER (FALLBACK)
# =============================================================================

echo "🚀 Test avec runserver Django..."

echo "🔧 Lancement temporaire du serveur Django..."
timeout 10 python manage.py runserver 0.0.0.0:8001 &
SERVER_PID=$!
sleep 3

echo "📡 Test des URLs avec runserver:"
curl -s -I "http://localhost:8001/accounts/google/login/" || echo "❌ Erreur runserver Google"
curl -s -I "http://localhost:8001/accounts/facebook/login/" || echo "❌ Erreur runserver Facebook"

# Arrêter le serveur de test
kill $SERVER_PID 2>/dev/null || true

# =============================================================================
# 8. CRÉATION DES TEMPLATES MANQUANTS
# =============================================================================

echo "🔧 Création des templates OAuth si manquants..."

# Créer les dossiers
mkdir -p competitions/templates/socialaccount/providers/google/
mkdir -p competitions/templates/socialaccount/providers/facebook/

# Template Google
if [[ ! -f "competitions/templates/socialaccount/providers/google/login.html" ]]; then
    echo "🎨 Création template Google..."
    cat > competitions/templates/socialaccount/providers/google/login.html << 'GOOGLE_TEMPLATE_EOF'
{% extends "account/base.html" %}
{% load i18n %}

{% block head_title %}{% trans "Google Sign In" %}{% endblock %}

{% block content %}
<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h2 class="auth-title">{% trans "Sign in with Google" %}</h2>
            <p class="auth-subtitle">{% trans "Connect your Google account to MartialComp" %}</p>
        </div>

        <div class="oauth-provider-card google">
            <div class="provider-icon">
                <svg width="24" height="24" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
            </div>
            
            <div class="provider-info">
                <h3>{% trans "Google Account" %}</h3>
                <p>{% trans "Use your Google account for quick and secure access" %}</p>
            </div>
        </div>

        <form method="post" action="{% url 'google_login' %}">
            {% csrf_token %}
            <button type="submit" class="btn btn-google">
                <span class="btn-icon">🚀</span>
                {% trans "Continue with Google" %}
            </button>
        </form>

        <div class="auth-features">
            <div class="feature-item">
                <span class="feature-icon">🔒</span>
                <span>{% trans "Secure OAuth2 authentication" %}</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">⚡</span>
                <span>{% trans "Quick access without passwords" %}</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🛡️</span>
                <span>{% trans "Protected by Google security" %}</span>
            </div>
        </div>

        <div class="auth-footer">
            <p>{% trans "By continuing, you agree to our" %} 
               <a href="#" class="link">{% trans "Terms of Service" %}</a> 
               {% trans "and" %} 
               <a href="#" class="link">{% trans "Privacy Policy" %}</a>
            </p>
        </div>
    </div>
</div>
GOOGLE_TEMPLATE_EOF
fi

# Template Facebook
if [[ ! -f "competitions/templates/socialaccount/providers/facebook/login.html" ]]; then
    echo "🎨 Création template Facebook..."
    cat > competitions/templates/socialaccount/providers/facebook/login.html << 'FACEBOOK_TEMPLATE_EOF'
{% extends "account/base.html" %}
{% load i18n %}

{% block head_title %}{% trans "Facebook Sign In" %}{% endblock %}

{% block content %}
<div class="auth-container">
    <div class="auth-card">
        <div class="auth-header">
            <h2 class="auth-title">{% trans "Sign in with Facebook" %}</h2>
            <p class="auth-subtitle">{% trans "Connect your Facebook account to MartialComp" %}</p>
        </div>

        <div class="oauth-provider-card facebook">
            <div class="provider-icon">
                <svg width="24" height="24" viewBox="0 0 24 24">
                    <path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                </svg>
            </div>
            
            <div class="provider-info">
                <h3>{% trans "Facebook Account" %}</h3>
                <p>{% trans "Use your Facebook account for quick and secure access" %}</p>
            </div>
        </div>

        <form method="post" action="{% url 'facebook_login' %}">
            {% csrf_token %}
            <button type="submit" class="btn btn-facebook">
                <span class="btn-icon">📘</span>
                {% trans "Continue with Facebook" %}
            </button>
        </form>

        <div class="auth-features">
            <div class="feature-item">
                <span class="feature-icon">🔒</span>
                <span>{% trans "Secure OAuth2 authentication" %}</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">⚡</span>
                <span>{% trans "Quick access without passwords" %}</span>
            </div>
            <div class="feature-item">
                <span class="feature-icon">🛡️</span>
                <span>{% trans "Protected by Facebook security" %}</span>
            </div>
        </div>

        <div class="auth-footer">
            <p>{% trans "By continuing, you agree to our" %} 
               <a href="#" class="link">{% trans "Terms of Service" %}</a> 
               {% trans "and" %} 
               <a href="#" class="link">{% trans "Privacy Policy" %}</a>
            </p>
        </div>
    </div>
</div>
FACEBOOK_TEMPLATE_EOF
fi

echo "✅ Templates OAuth créés"

# =============================================================================
# 9. CORRECTION DES PERMISSIONS
# =============================================================================

echo "🔐 Correction des permissions..."

chown -R www-data:www-data competitions/templates/ 2>/dev/null || true
chmod -R 644 competitions/templates/ 2>/dev/null || true
find competitions/templates/ -type d -exec chmod 755 {} \; 2>/dev/null || true

# =============================================================================
# 10. REDÉMARRAGE PASSENGER
# =============================================================================

echo "🔄 Redémarrage Passenger..."

touch passenger_wsgi.py
sleep 2

# =============================================================================
# 11. TESTS FINAUX
# =============================================================================

echo "🧪 Tests finaux après correction..."

sleep 5

echo "📡 Test final Google:"
curl -s -o /dev/null -w "Status: %{http_code}\n" "https://martialcomp.com/accounts/google/login/" || echo "Erreur persiste"

echo "📡 Test final Facebook:"
curl -s -o /dev/null -w "Status: %{http_code}\n" "https://martialcomp.com/accounts/facebook/login/" || echo "Erreur persiste"

# =============================================================================
# 12. RAPPORT FINAL
# =============================================================================

echo ""
echo "🎯 DIAGNOSTIC OAUTH TERMINÉ"
echo ""
echo "📊 ACTIONS EFFECTUÉES:"
echo "  ✅ Tests de connectivité"
echo "  ✅ Vérification templates"
echo "  ✅ Vérification URLs django-allauth"
echo "  ✅ Vérification base de données"
echo "  ✅ Vérification configuration"
echo "  ✅ Création templates manquants"
echo "  ✅ Correction permissions"
echo "  ✅ Redémarrage Passenger"
echo ""
echo "🔗 TESTER MAINTENANT:"
echo "  • https://martialcomp.com/accounts/google/login/"
echo "  • https://martialcomp.com/accounts/facebook/login/"
echo ""
echo "📝 LOGS DISPONIBLES:"
echo "  • /tmp/passenger_debug.log"
echo "  • /var/log/nginx/error.log"
echo "  • /var/log/apache2/error.log"
echo ""
echo "🎉 Diagnostic terminé: $(date)"