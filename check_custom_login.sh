#!/bin/bash
# Vérifier la vue custom_login qui pourrait causer le problème

echo "================================================"
echo "🔍 ANALYSE CUSTOM LOGIN VIEW"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification de custom_login.py..."
echo "====================================="
if [ -f "apps/competitions/views/custom_login.py" ]; then
    echo "📋 Contenu de custom_login.py (lignes avec redirect):"
    grep -n -A3 -B3 "redirect.*spectator\|role_map" apps/competitions/views/custom_login.py | head -30
fi

echo ""
echo "2️⃣ Vérification des URLs de login..."
echo "===================================="
echo "📋 URLs liées au login:"
grep -r "login" config/urls.py | grep -v "static\|media"
grep -r "custom_login" apps/competitions/urls/ --include="*.py"

echo ""
echo "3️⃣ Quelle vue est réellement utilisée pour le login..."
echo "====================================================="
python3 -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
from django.urls import reverse, resolve

# Résoudre l'URL de login
try:
    login_url = reverse('account_login')
    match = resolve(login_url)
    print(f'URL de login: {login_url}')
    print(f'Vue utilisée: {match.func.__module__}.{match.func.__name__}')
except Exception as e:
    print(f'Erreur: {e}')
"

echo ""
echo "4️⃣ Désactivation temporaire de custom_login si utilisé..."
echo "========================================================"
# Si custom_login interfère, on peut le commenter temporairement
if grep -q "custom_login" apps/competitions/urls/__init__.py; then
    echo "⚠️  custom_login trouvé dans les URLs"
    echo "Sauvegarde et commentaire..."
    cp apps/competitions/urls/__init__.py apps/competitions/urls/__init__.py.backup_custom_login
    sed -i 's/.*custom_login.*/# &/' apps/competitions/urls/__init__.py
    echo "✅ custom_login commenté temporairement"
else
    echo "✅ custom_login n'est pas dans les URLs principales"
fi

echo ""
echo "5️⃣ Vérification de la redirection après login dans allauth..."
echo "==========================================================="
echo "📋 Configuration LOGIN_REDIRECT_URL:"
grep -n "LOGIN_REDIRECT_URL" config/settings/*.py

echo ""
echo "6️⃣ Test direct de la logique après authentification..."
echo "====================================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from allauth.account.adapter import get_adapter

User = get_user_model()
user = User.objects.filter(username='DT_bguinziemba').first()

if user:
    print(f"🧪 Test de redirection pour {user.username}:")
    
    # Simuler une requête
    from django.test import RequestFactory
    factory = RequestFactory()
    request = factory.get('/')
    request.user = user
    
    # Obtenir l'adapter allauth
    adapter = get_adapter(request)
    
    # Obtenir l'URL de redirection
    redirect_url = adapter.get_login_redirect_url(request)
    print(f"✅ URL de redirection allauth: {redirect_url}")
    
    # Vérifier aussi LOGIN_REDIRECT_URL
    print(f"✅ LOGIN_REDIRECT_URL dans settings: {settings.LOGIN_REDIRECT_URL}")
PYEOF

echo ""
echo "7️⃣ Redémarrage si modifications..."
echo "=================================="
if [ -f "apps/competitions/urls/__init__.py.backup_custom_login" ]; then
    sudo systemctl restart martialcomp
    echo "✅ Service redémarré après modifications"
fi

echo ""
echo "================================================"
echo "📊 RÉSUMÉ"
echo "================================================"
echo ""
echo "Le problème semble venir de custom_login.py qui"
echo "redirige vers spectator par défaut."
echo ""
echo "Solutions possibles:"
echo "1. Désactiver custom_login temporairement"
echo "2. Modifier LOGIN_REDIRECT_URL dans settings"
echo "3. Corriger la logique dans custom_login.py"

REMOTE_COMMANDS