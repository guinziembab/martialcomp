#!/bin/bash
# =============================================================================
# TEST WSGI DIRECT - Identifier l'erreur exacte
# =============================================================================

APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"

cd $APP_DIR
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production
export PYTHONPATH=$APP_DIR

echo "=== TEST 1: Import WSGI application ==="
python -c "
import sys
print(f'Python: {sys.executable}')
print(f'Version: {sys.version}')
print()

try:
    print('Import config.wsgi...')
    from config.wsgi import application
    print('OK - WSGI application chargée')
except Exception as e:
    print(f'ERREUR: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "=== TEST 2: Charger Django complètement ==="
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    import django
    django.setup()
    print('Django setup OK')

    # Tester une requête simple
    from django.test import Client
    client = Client()

    print('Test requête /fr/ ...')
    response = client.get('/fr/', HTTP_HOST='martialcomp.com', secure=True)
    print(f'Status: {response.status_code}')

    if response.status_code >= 400:
        print(f'Content (first 500 chars):')
        content = response.content.decode('utf-8', errors='ignore')[:500]
        print(content)

except Exception as e:
    print(f'ERREUR: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "=== TEST 3: Vérifier SESSION_ENGINE actif ==="
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.conf import settings
print(f'SESSION_ENGINE: {settings.SESSION_ENGINE}')
print(f'SESSION_SERIALIZER: {getattr(settings, \"SESSION_SERIALIZER\", \"(non défini)\")}')
"

echo ""
echo "=== FIN DES TESTS ==="
