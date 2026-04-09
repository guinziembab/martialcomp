#!/bin/bash
# =============================================================================
# DÉPLOIEMENT FIX SCORING_HISTORY - ERREUR 500
# =============================================================================
# Date: 2025-12-20
# Problème: Erreur 500 sur /fr/competitions/technical-scoring/history/4/
# Solution: Protection des imports et requêtes avec try/except
# =============================================================================

set -e

echo "==========================================="
echo "FIX SCORING_HISTORY - DÉPLOIEMENT"
echo "==========================================="

# Variables
APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"
LOGS_DIR="/var/www/vhosts/martialcomp.com/httpdocs/logs"

# =============================================================================
# ÉTAPE 1: Backup de l'ancien fichier
# =============================================================================
echo ""
echo "[1/5] Backup du fichier actuel..."
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
cp "$APP_DIR/apps/competitions/views/technical_scoring.py" "$APP_DIR/apps/competitions/views/technical_scoring.py.backup_$BACKUP_DATE" 2>/dev/null || true
echo "✓ Backup créé: technical_scoring.py.backup_$BACKUP_DATE"

# =============================================================================
# ÉTAPE 2: Nettoyage des caches Python
# =============================================================================
echo ""
echo "[2/5] Nettoyage des caches Python..."
find $APP_DIR -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find $APP_DIR -name "*.pyc" -delete 2>/dev/null || true
echo "✓ Caches nettoyés"

# =============================================================================
# ÉTAPE 3: Vérifier la syntaxe du fichier
# =============================================================================
echo ""
echo "[3/5] Vérification de la syntaxe Python..."
source "$VENV_DIR/bin/activate"
python -m py_compile "$APP_DIR/apps/competitions/views/technical_scoring.py"
echo "✓ Syntaxe valide"

# =============================================================================
# ÉTAPE 4: Redémarrer Gunicorn
# =============================================================================
echo ""
echo "[4/5] Redémarrage de Gunicorn..."

# Arrêter Gunicorn
pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2

# Vérifier que le port est libre
fuser -k 8888/tcp 2>/dev/null || true
sleep 1

# Démarrer Gunicorn
cd $APP_DIR
export DJANGO_SETTINGS_MODULE="config.settings.production"
export PYTHONPATH="$APP_DIR:$APP_DIR/apps"

"$VENV_DIR/bin/gunicorn" config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 3 \
    --timeout 120 \
    --chdir $APP_DIR \
    --pythonpath "$APP_DIR,$APP_DIR/apps" \
    --access-logfile $LOGS_DIR/gunicorn_access.log \
    --error-logfile $LOGS_DIR/gunicorn_error.log \
    --capture-output \
    --enable-stdio-inheritance \
    -c /dev/null \
    --daemon

echo "Attente du démarrage (5 secondes)..."
sleep 5

# =============================================================================
# ÉTAPE 5: Vérification
# =============================================================================
echo ""
echo "[5/5] Vérification..."

# Vérifier que Gunicorn tourne
if pgrep -f "gunicorn.*config.wsgi" > /dev/null; then
    echo "✓ Gunicorn est en cours d'exécution"
else
    echo "✗ ERREUR: Gunicorn n'a pas démarré!"
    tail -50 $LOGS_DIR/gunicorn_error.log
    exit 1
fi

# Test de la page scoring_history
echo ""
echo "Test de la page scoring_history..."
HTTP_CODE=$(curl -sL -w "%{http_code}" -o /dev/null \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/competitions/technical-scoring/history/4/' 2>/dev/null)

echo "Code HTTP scoring_history: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo ""
    echo "==========================================="
    echo "✓ SUCCÈS! La page scoring_history fonctionne!"
    echo "==========================================="
    echo ""
    echo "Testez: https://martialcomp.com/fr/competitions/technical-scoring/history/4/"
else
    echo ""
    echo "==========================================="
    echo "⚠ Code HTTP: $HTTP_CODE"
    echo "==========================================="
    echo ""
    echo "=== Dernières erreurs Gunicorn ==="
    tail -50 $LOGS_DIR/gunicorn_error.log
fi
