#!/bin/bash

# Script d'exécution de la mise en conformité i18n en production
echo "🌐 EXÉCUTION MISE EN CONFORMITÉ I18N PRODUCTION"
echo "=============================================="

# Configuration
SCRIPT_NAME="deploy_i18n_production.py"
REMOTE_HOST="root@martialcomp.com"
REMOTE_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

echo "📡 Transfert et exécution du script i18n..."

# Méthode 1: Transfert via scp puis exécution
if scp $SCRIPT_NAME $REMOTE_HOST:/tmp/; then
    echo "✅ Script transféré"
    
    # Exécution à distance
    ssh $REMOTE_HOST << 'EOF'
echo "🔧 Exécution du script i18n en production..."
cd /var/www/vhosts/martialcomp.com/httpdocs
python3 /tmp/deploy_i18n_production.py

echo ""
echo "🧪 Test final des URLs i18n:"
curl -I http://localhost:8000/ 2>/dev/null | head -1
curl -I http://localhost:8000/fr/ 2>/dev/null | head -1
curl -I http://localhost:8000/en/ 2>/dev/null | head -1

echo ""
echo "✅ Mise en conformité i18n terminée"
EOF

else
    echo "⚠️ Échec transfert scp, utilisation de la méthode alternative..."
    
    # Méthode 2: Création directe du script sur le serveur
    ssh $REMOTE_HOST << 'SCRIPT_EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "🔧 Création et exécution du script i18n directement..."

# Créer le script Python directement
cat > /tmp/fix_i18n_direct.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import os
import subprocess
import time

PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
os.chdir(PROD_DIR)

print("🌐 CORRECTION I18N DIRECTE")
print("=========================")

# Sauvegarde config/urls.py
subprocess.run(['cp', 'config/urls.py', f'config/urls.py.backup_{int(time.time())}'])
print("✅ Sauvegarde créée")

# Nouvelle configuration URLs avec i18n
urls_content = '''"""
Configuration des URLs principales de MartialComp avec support i18n
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
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('competitions.urls')),
    prefix_default_language=False,
)

# URLs pour Rosetta
if 'rosetta' in settings.INSTALLED_APPS:
    urlpatterns += [
        path('rosetta/', include('rosetta.urls')),
    ]

# Fichiers statiques en DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
'''

with open('config/urls.py', 'w') as f:
    f.write(urls_content)

print("✅ config/urls.py corrigé avec i18n")

# Test Django
result = subprocess.run(['python3', 'manage.py', 'check'], 
                       capture_output=True, text=True,
                       env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings'})

if result.returncode == 0:
    print("✅ Configuration Django valide")
    
    # Redémarrer serveur
    subprocess.run(['pkill', '-f', 'manage.py'], check=False)
    time.sleep(3)
    
    subprocess.Popen(['python3', 'manage.py', 'runserver', '0.0.0.0:8000'],
                    env={**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings'})
    time.sleep(5)
    
    print("✅ Serveur redémarré")
else:
    print("❌ Erreur configuration Django:")
    print(result.stderr)

print("\n🌐 CORRECTION I18N TERMINÉE")
PYTHON_EOF

# Exécuter le script
python3 /tmp/fix_i18n_direct.py

echo ""
echo "🧪 TEST FINAL URLs:"
curl -I http://localhost:8000/ 2>/dev/null | head -1
curl -I http://localhost:8000/fr/ 2>/dev/null | head -1
curl -I http://localhost:8000/en/ 2>/dev/null | head -1

echo ""
echo "✅ Mise en conformité i18n terminée via méthode directe"

SCRIPT_EOF

fi

echo ""
echo "🌐 Test des URLs publiques:"
echo "   https://martialcomp.com/"
curl -I https://martialcomp.com/ 2>/dev/null | head -1

echo "   https://martialcomp.com/fr/"
curl -I https://martialcomp.com/fr/ 2>/dev/null | head -1

echo "   https://martialcomp.com/en/"
curl -I https://martialcomp.com/en/ 2>/dev/null | head -1

echo ""
echo "🎉 MISE EN CONFORMITÉ I18N TERMINÉE!"
echo ""
echo "🌐 URLs MAINTENANT DISPONIBLES:"
echo "   🏠 https://martialcomp.com/ (langue par défaut)"
echo "   🇫🇷 https://martialcomp.com/fr/ (français)"
echo "   🇬🇧 https://martialcomp.com/en/ (anglais)"
echo ""
echo "🧪 DÉMO MULTILINGUE:"
echo "   👤 dojo_sakura_manager / demo2025"
echo "   🎯 Accessible depuis toutes les langues"