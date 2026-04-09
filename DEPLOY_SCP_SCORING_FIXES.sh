#!/bin/bash
# =============================================================================
# DEPLOY VIA SCP - Corrections Scoring MartialComp
# Date: 2025-12-20
# Compte SSH: martialcomp-production
# =============================================================================

# Configuration
SSH_ALIAS="martialcomp-production"
REMOTE_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

echo "==========================================="
echo "DEPLOIEMENT VIA SCP"
echo "Compte: $SSH_ALIAS"
echo "==========================================="
echo ""

# =============================================================================
# ÉTAPE 1: TRANSFERT DES FICHIERS
# =============================================================================

echo "=== COMMANDES SCP À EXÉCUTER ==="
echo ""

echo "# 1. Fichier technical_scoring.py (vue principale)"
echo "scp apps/competitions/views/technical_scoring.py $SSH_ALIAS:$REMOTE_DIR/apps/competitions/views/"
echo ""

echo "# 2. Template scoring_history.html (affichage colonnes juges)"
echo "scp apps/competitions/templates/competitions/technical_scoring/scoring_history.html $SSH_ALIAS:$REMOTE_DIR/apps/competitions/templates/competitions/technical_scoring/"
echo ""

echo "# 3. Template categories.html (page catégories)"
echo "scp apps/competitions/templates/competitions/technical_scoring/categories.html $SSH_ALIAS:$REMOTE_DIR/apps/competitions/templates/competitions/technical_scoring/"
echo ""

echo "# 4. Fichier custom_filters.py (filtres template)"
echo "scp apps/competitions/templatetags/custom_filters.py $SSH_ALIAS:$REMOTE_DIR/apps/competitions/templatetags/"
echo ""

echo "# 5. Script de redémarrage"
echo "scp COMMANDES_RESTART_GUNICORN.sh $SSH_ALIAS:$REMOTE_DIR/"
echo ""

echo "==========================================="
echo ""

# =============================================================================
# ÉTAPE 2: COMMANDES À EXÉCUTER SUR LE SERVEUR
# =============================================================================

echo "=== APRÈS TRANSFERT, SE CONNECTER AU SERVEUR ==="
echo ""
echo "ssh $SSH_ALIAS"
echo ""
echo "=== PUIS EXÉCUTER CES COMMANDES ==="
echo ""
cat << 'REMOTE_COMMANDS'
# Aller dans le répertoire de l'application
cd /var/www/vhosts/martialcomp.com/httpdocs

# Nettoyer les caches Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

# Vider le cache Redis
redis-cli FLUSHALL 2>/dev/null || echo "Redis non disponible"

# Activer l'environnement virtuel
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

# Tester les imports
python -c "
import django
django.setup()
from apps.competitions.views.technical_scoring import scoring_history, scoring_categories
from apps.competitions.templatetags.custom_filters import dict_keys, get_item
print('Imports OK')
"

# Redémarrer Gunicorn
pkill -9 -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2

# Lancer Gunicorn
/var/www/vhosts/martialcomp.com/venv/bin/gunicorn config.wsgi:application \
    --bind 127.0.0.1:8888 \
    --workers 2 \
    --timeout 120 \
    --chdir /var/www/vhosts/martialcomp.com/httpdocs \
    --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log \
    --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log \
    --capture-output \
    --daemon

sleep 3

# Vérifier que Gunicorn tourne
ps aux | grep gunicorn | grep -v grep

# Test HTTP
curl -sL -w "HTTP Code: %{http_code}\n" -o /dev/null \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/'

echo "DÉPLOIEMENT TERMINÉ"
REMOTE_COMMANDS

echo ""
echo "==========================================="
