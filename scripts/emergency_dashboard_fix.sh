#!/bin/bash

echo "🚨 DIAGNOSTIC D'URGENCE - PAGES BLANCHES DASHBOARDS"
echo "=================================================="

# Vérifier les logs Django
echo "📋 Vérification des logs Django..."
tail -20 /tmp/django.log

echo ""
echo "📋 Vérification des erreurs récentes..."
grep -i error /tmp/django.log | tail -10

echo ""
echo "📋 Test des URLs principales..."
echo "1. Test dashboard practitioner:"
curl -s -I https://martialcomp.com/fr/practitioner/dashboard/ | head -5

echo ""
echo "2. Test dashboard club:"
curl -s -I https://martialcomp.com/fr/club/dashboard/ | head -5

echo ""
echo "3. Test dashboard federation:"
curl -s -I https://martialcomp.com/fr/federation/dashboard/ | head -5

echo ""
echo "📋 Vérification de la configuration Django..."
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

echo "Test de la configuration Django:"
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from django.conf import settings
    print('✅ Django configuration OK')
    print(f'USE_I18N: {settings.USE_I18N}')
    print(f'LANGUAGE_CODE: {settings.LANGUAGE_CODE}')
    print(f'INSTALLED_APPS count: {len(settings.INSTALLED_APPS)}')
    
    # Test des URLs
    from django.urls import reverse
    print('✅ URL resolution test...')
    
except Exception as e:
    print(f'❌ Error: {e}')
"

echo ""
echo "📋 Vérification des templates..."
if [ -d "competitions/templates" ]; then
    echo "✅ Templates directory exists"
    echo "Dashboard templates:"
    find competitions/templates -name "*dashboard*" | head -5
else
    echo "❌ Templates directory missing"
fi

echo ""
echo "📋 Vérification des middlewares..."
python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
print('Middlewares configured:')
for i, mw in enumerate(settings.MIDDLEWARE):
    print(f'{i+1}. {mw}')
"