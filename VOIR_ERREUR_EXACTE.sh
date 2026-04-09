#!/bin/bash
# Afficher les dernières erreurs Gunicorn
echo "=== DERNIÈRES ERREURS GUNICORN ==="
tail -100 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log | grep -A 20 "Traceback\|Error\|Exception" | tail -50

echo ""
echo "=== TEST AVEC DEBUG TEMPORAIRE ==="
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate

# Test avec DEBUG=True temporairement pour voir l'erreur
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# Créer une fausse requête
factory = RequestFactory()
request = factory.get('/fr/')
request.user = AnonymousUser()
request.session = {}

try:
    from django.urls import resolve
    match = resolve('/fr/')
    print(f'URL résolue: {match.func}')
except Exception as e:
    print(f'Erreur URL: {e}')
"
