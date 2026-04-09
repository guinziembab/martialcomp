#!/bin/bash
# =============================================================================
# DIAGNOSTIC ENVIRONNEMENT GUNICORN - MartialComp
# =============================================================================
# Ce script identifie les différences entre l'environnement CLI et Gunicorn
# =============================================================================

APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"

echo "==========================================="
echo "DIAGNOSTIC ENVIRONNEMENT GUNICORN"
echo "==========================================="
echo ""

# 1. Vérifier quel Python est utilisé
echo "[1/8] Vérification des binaires Python..."
echo "Python du venv:"
ls -la $VENV_DIR/bin/python*
echo ""
echo "Gunicorn shebang:"
head -1 $VENV_DIR/bin/gunicorn
echo ""

# 2. Vérifier le sys.path Python
echo "[2/8] sys.path du Python venv..."
$VENV_DIR/bin/python -c "import sys; print('\n'.join(sys.path))"
echo ""

# 3. Vérifier la version Django
echo "[3/8] Version Django installée..."
$VENV_DIR/bin/python -c "import django; print(f'Django {django.VERSION}')"
echo ""

# 4. Vérifier l'emplacement du module sessions
echo "[4/8] Emplacement django.contrib.sessions..."
$VENV_DIR/bin/python -c "
import django.contrib.sessions
print(f'Package: {django.contrib.sessions.__file__}')
import os
sessions_dir = os.path.dirname(django.contrib.sessions.__file__)
print(f'Contenu du dossier:')
for f in os.listdir(sessions_dir):
    print(f'  {f}')
"
echo ""

# 5. Vérifier spécifiquement le serializers.py
echo "[5/8] Vérification serializers.py..."
$VENV_DIR/bin/python -c "
import os
import django.contrib.sessions
sessions_dir = os.path.dirname(django.contrib.sessions.__file__)
serializers_path = os.path.join(sessions_dir, 'serializers.py')
if os.path.exists(serializers_path):
    print(f'EXISTE: {serializers_path}')
    print(f'Taille: {os.path.getsize(serializers_path)} bytes')
else:
    print(f'MANQUANT: {serializers_path}')
"
echo ""

# 6. Tester l'import direct
echo "[6/8] Test import JSONSerializer..."
$VENV_DIR/bin/python -c "
try:
    from django.contrib.sessions.serializers import JSONSerializer
    print('OK - JSONSerializer importé avec succès')
except Exception as e:
    print(f'ERREUR: {e}')
"
echo ""

# 7. Vérifier les permissions du venv
echo "[7/8] Permissions du venv..."
ls -la $VENV_DIR/lib/python3.*/site-packages/django/contrib/sessions/ | head -10
echo ""

# 8. Tester Gunicorn en mode synchrone (pas daemon)
echo "[8/8] Test Gunicorn en mode foreground (5 secondes)..."
cd $APP_DIR
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production
export PYTHONPATH=$APP_DIR

# Arrêter les instances existantes
pkill -9 -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2

# Lancer en foreground avec timeout
timeout 5 $VENV_DIR/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 1 \
    --timeout 120 \
    --chdir $APP_DIR \
    --pythonpath $APP_DIR \
    --log-level debug \
    --error-logfile - \
    --access-logfile - 2>&1 | head -100

echo ""
echo "==========================================="
echo "FIN DU DIAGNOSTIC"
echo "==========================================="
