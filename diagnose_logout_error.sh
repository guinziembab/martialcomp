#!/bin/bash
# Script pour diagnostiquer l'erreur de logout

echo "================================================"
echo "🔍 DIAGNOSTIC ERREUR LOGOUT"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification des logs d'erreur récents..."
echo "=============================================="
echo "📋 Dernières erreurs Gunicorn:"
tail -20 logs/gunicorn_error.log | grep -A5 -B5 "logout\|500\|ERROR"

echo ""
echo "📋 Logs Django (si disponibles):"
if [ -f logs/django.log ]; then
    tail -20 logs/django.log | grep -A5 -B5 "logout\|500\|ERROR"
fi

echo ""
echo "2️⃣ Vérification de la configuration des URLs..."
echo "==============================================="
echo "📋 URLs dans config/urls.py:"
grep -n "logout" config/urls.py

echo ""
echo "📋 Configuration allauth:"
grep -A5 -B5 "ACCOUNT_LOGOUT" config/settings/base.py

echo ""
echo "3️⃣ Vérification du template logout..."
echo "======================================"
echo "📋 Recherche du template logout:"
find . -name "*logout*" -type f | grep -E "\.html$|\.py$" | grep -v "__pycache__" | grep -v "venv" | head -10

echo ""
echo "4️⃣ Vérification de la vue logout..."
echo "====================================="
if [ -f apps/competitions/templates/account/logout.html ]; then
    echo "✅ Template logout trouvé"
    head -20 apps/competitions/templates/account/logout.html
else
    echo "❌ Template logout non trouvé dans apps/competitions/templates/account/"
fi

echo ""
echo "5️⃣ Test de la configuration Django..."
echo "======================================"
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 -c "
from django.conf import settings
print('ACCOUNT_LOGOUT_ON_GET:', getattr(settings, 'ACCOUNT_LOGOUT_ON_GET', 'Non défini'))
print('LOGIN_URL:', getattr(settings, 'LOGIN_URL', '/accounts/login/'))
print('LOGOUT_REDIRECT_URL:', getattr(settings, 'LOGOUT_REDIRECT_URL', 'Non défini'))
"

echo ""
echo "================================================"
echo "✅ DIAGNOSTIC TERMINÉ"
echo "================================================"
REMOTE_COMMANDS