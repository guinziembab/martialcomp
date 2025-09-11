#!/bin/bash

# Script de déploiement de la correction i18n à distance
echo "🌐 DÉPLOIEMENT CORRECTION I18N À DISTANCE"
echo "========================================"

# Configuration
REMOTE_HOST="root@martialcomp.com"
REMOTE_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

echo "📡 Connexion au serveur de production..."

# Créer le script de correction directement sur le serveur
ssh $REMOTE_HOST << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "🔧 CORRECTION I18N URLS EN DIRECT"
echo "=================================="

# Sauvegarder le fichier actuel
cp config/urls.py config/urls.py.i18n_backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Sauvegarde créée"

# Créer la configuration i18n corrigée
cat > config/urls.py << 'URLS_EOF'
"""
Configuration des URLs principales de MartialComp avec i18n
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.contrib.auth import views as auth_views

# URLs sans préfixe de langue
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('set_language/', set_language, name='set_language'),
]

# URLs avec traduction i18n
urlpatterns += i18n_patterns(
    # Authentification (sans préfixe de langue aussi pour compatibilité)
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Application competitions
    path('', include('competitions.urls')),
    
    prefix_default_language=False,
)

# URLs pour Rosetta (traductions)
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('rosetta/', include('rosetta.urls')),
    ]

# URLs pour les fichiers media et static en mode DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
URLS_EOF

echo "✅ Configuration i18n appliquée"

# Vérifier la syntaxe Django
echo "🔍 Vérification Django..."
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings

python3 manage.py check
if [ $? -eq 0 ]; then
    echo "✅ Configuration Django valide"
    
    # Redémarrer le serveur
    echo "🔄 Redémarrage du serveur..."
    pkill -f "manage.py"
    sleep 3
    
    # Démarrer le serveur en arrière-plan
    nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_i18n.log 2>&1 &
    sleep 5
    
    # Tester les URLs
    echo "🧪 Test des URLs i18n..."
    
    curl -I -s http://localhost:8000/ | head -n 1
    curl -I -s http://localhost:8000/fr/ | head -n 1
    curl -I -s http://localhost:8000/en/ | head -n 1
    
    echo "✅ Correction i18n terminée"
    echo ""
    echo "🌐 URLs MAINTENANT DISPONIBLES:"
    echo "   🏠 https://martialcomp.com/ (redirige vers langue par défaut)"
    echo "   🇫🇷 https://martialcomp.com/fr/ (français)"
    echo "   🇬🇧 https://martialcomp.com/en/ (anglais)"
    echo "   🔑 https://martialcomp.com/login/ (connexion)"
    
else
    echo "❌ Erreur de configuration Django"
    echo "📋 Consultation des logs:"
    python3 manage.py check 2>&1 | tail -10
fi

EOF

echo "✅ Script de correction i18n exécuté"
echo ""
echo "🌐 Test des URLs corrigées:"
echo "   curl -I https://martialcomp.com/fr/"
echo "   curl -I https://martialcomp.com/en/"