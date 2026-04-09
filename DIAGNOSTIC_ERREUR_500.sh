#!/bin/bash
# =============================================================================
# DIAGNOSTIC ERREUR 500 - MartialComp Production
# =============================================================================
# Date: 2025-12-20
# Objectif: Identifier la cause exacte de l'erreur 500
# =============================================================================

set -e

APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"
LOGS_DIR="/var/www/vhosts/martialcomp.com/httpdocs/logs"

echo "=========================================="
echo "DIAGNOSTIC ERREUR 500 - MartialComp"
echo "=========================================="
echo ""

# 1. Vérifier les processus Gunicorn
echo "[1/7] Vérification des processus Gunicorn..."
ps aux | grep gunicorn | grep -v grep || echo "Aucun processus Gunicorn"
echo ""

# 2. Vérifier les dernières erreurs Gunicorn
echo "[2/7] Dernières erreurs Gunicorn..."
if [ -f "$LOGS_DIR/gunicorn_error.log" ]; then
    tail -100 "$LOGS_DIR/gunicorn_error.log" | grep -i "error\|exception\|traceback" || echo "Pas d'erreurs récentes"
else
    echo "Fichier log non trouvé: $LOGS_DIR/gunicorn_error.log"
fi
echo ""

# 3. Tester l'import Django
echo "[3/7] Test d'import Django..."
cd "$APP_DIR"
source "$VENV_DIR/bin/activate"
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
try:
    import django
    django.setup()
    print('✓ Django OK')
except Exception as e:
    print(f'✗ Erreur Django: {e}')
    import traceback
    traceback.print_exc()
"
echo ""

# 4. Tester la connexion base de données
echo "[4/7] Test connexion base de données..."
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    print('✓ Base de données OK')
except Exception as e:
    print(f'✗ Erreur DB: {e}')
"
echo ""

# 5. Tester Redis
echo "[5/7] Test connexion Redis..."
python -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
from django.core.cache import cache
try:
    cache.set('test_key', 'test_value', 10)
    result = cache.get('test_key')
    if result == 'test_value':
        print('✓ Redis OK')
    else:
        print(f'✗ Redis: valeur inattendue: {result}')
except Exception as e:
    print(f'✗ Erreur Redis: {e}')
"
echo ""

# 6. Test d'une requête simple
echo "[6/7] Test requête HTTP locale..."
HTTP_CODE=$(curl -sL -w "%{http_code}" -o /tmp/martialcomp_test.html \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/' 2>/dev/null)
echo "Code HTTP: $HTTP_CODE"
if [ "$HTTP_CODE" = "500" ]; then
    echo "Contenu de la réponse 500:"
    head -50 /tmp/martialcomp_test.html
fi
echo ""

# 7. Logs d'erreur Django
echo "[7/7] Derniers logs Django..."
if [ -f "/var/log/django/martialcomp.log" ]; then
    tail -50 /var/log/django/martialcomp.log
else
    echo "Fichier log Django non trouvé"
fi

echo ""
echo "=========================================="
echo "FIN DU DIAGNOSTIC"
echo "=========================================="
