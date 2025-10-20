#!/bin/bash
# Diagnostic de l'erreur 500 sur la page d'accueil

echo "================================================"
echo "🔍 DIAGNOSTIC ERREUR 500 - PAGE D'ACCUEIL"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Dernières erreurs dans les logs..."
echo "======================================"
echo "📋 Erreurs Django récentes:"
tail -30 logs/django.log | grep -A5 -B2 "ERROR\|500\|Internal Server Error"

echo ""
echo "📋 Erreurs Gunicorn récentes:"
tail -30 logs/gunicorn_error.log | grep -A5 -B2 "ERROR\|500\|Traceback"

echo ""
echo "2️⃣ Vérification de la configuration..."
echo "======================================="
echo "📋 URLs principales:"
grep -n "path('fr/'" config/urls.py || echo "Pattern 'fr/' non trouvé directement"
grep -n "i18n_patterns" config/urls.py

echo ""
echo "3️⃣ Vérification des vues..."
echo "============================"
echo "📋 Vue home/welcome:"
find apps -name "*.py" -type f -exec grep -l "def welcome\|class WelcomeView\|def home" {} \; | grep -v __pycache__ | head -5

echo ""
echo "4️⃣ Test rapide Django..."
echo "========================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 -c "
import django
django.setup()
from django.urls import reverse
try:
    # Tester la résolution d'URL
    print('Test des URLs principales:')
    urls_to_test = ['welcome', 'home', 'competitions:home']
    for url_name in urls_to_test:
        try:
            url = reverse(url_name)
            print(f'  ✅ {url_name} -> {url}')
        except Exception as e:
            print(f'  ❌ {url_name}: {str(e)}')
except Exception as e:
    print(f'Erreur: {e}')
"

echo ""
echo "5️⃣ Vérification des imports..."
echo "=============================="
python3 -c "
try:
    from apps.competitions.views import home
    print('✅ Import views.home réussi')
except Exception as e:
    print(f'❌ Erreur import views.home: {e}')

try:
    from config.urls import urlpatterns
    print('✅ Import urls réussi')
except Exception as e:
    print(f'❌ Erreur import urls: {e}')
"

echo ""
echo "6️⃣ Derniers logs Apache..."
echo "=========================="
tail -20 /var/log/apache2/error.log | grep -A3 -B3 "martialcomp"

REMOTE_COMMANDS