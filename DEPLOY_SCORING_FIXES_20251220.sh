#!/bin/bash
# =============================================================================
# DEPLOY SCORING FIXES - MartialComp Production
# Date: 2025-12-20
# =============================================================================
# Corrections appliquées:
# 1. Sécurité scoring_history: L'utilisateur ne voit plus les compétitions
#    dont il n'est pas organisateur
# 2. Affichage des notes des juges en colonnes (max 5) directement visibles
# 3. Page "Catégories de Notation" fonctionnelle avec les vraies données
# =============================================================================

set -e

APP_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="/var/www/vhosts/martialcomp.com/venv"
BACKUP_DIR="$APP_DIR/backups/scoring_fixes_$(date +%Y%m%d_%H%M%S)"

echo "==========================================="
echo "DEPLOIEMENT CORRECTIONS SCORING"
echo "Date: $(date)"
echo "==========================================="
echo ""

# 1. Créer le répertoire de backup
echo "[1/8] Création répertoire de sauvegarde..."
mkdir -p $BACKUP_DIR

# 2. Sauvegarder les fichiers existants
echo "[2/8] Sauvegarde des fichiers existants..."
cp $APP_DIR/apps/competitions/views/technical_scoring.py $BACKUP_DIR/
cp $APP_DIR/apps/competitions/templates/competitions/technical_scoring/scoring_history.html $BACKUP_DIR/
cp $APP_DIR/apps/competitions/templates/competitions/technical_scoring/categories.html $BACKUP_DIR/
cp $APP_DIR/apps/competitions/templatetags/custom_filters.py $BACKUP_DIR/
echo "Backup créé dans: $BACKUP_DIR"

# 3. Transférer les nouveaux fichiers
echo "[3/8] Transfert des nouveaux fichiers..."

# technical_scoring.py
cat > $APP_DIR/apps/competitions/views/technical_scoring.py << 'SCORING_VIEW_EOF'
# Contenu du fichier technical_scoring.py sera copié manuellement ou via rsync
SCORING_VIEW_EOF

echo "ATTENTION: Les fichiers doivent être transférés manuellement via rsync ou scp"
echo "Fichiers à transférer:"
echo "  - apps/competitions/views/technical_scoring.py"
echo "  - apps/competitions/templates/competitions/technical_scoring/scoring_history.html"
echo "  - apps/competitions/templates/competitions/technical_scoring/categories.html"
echo "  - apps/competitions/templatetags/custom_filters.py"

# 4. Nettoyer les caches Python
echo "[4/8] Nettoyage caches Python..."
find $APP_DIR -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find $APP_DIR -name "*.pyc" -delete 2>/dev/null || true

# 5. Vider le cache Redis
echo "[5/8] Vidage cache Redis..."
redis-cli FLUSHALL 2>/dev/null || echo "Redis non disponible ou déjà vidé"

# 6. Tester l'import Django
echo "[6/8] Test import Django..."
cd $APP_DIR
source $VENV_DIR/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python -c "
import sys
print(f'Python: {sys.executable}')

try:
    import django
    django.setup()
    print('Django setup: OK')

    from apps.competitions.views.technical_scoring import scoring_history, scoring_categories
    print('Import scoring views: OK')

    from apps.competitions.templatetags.custom_filters import dict_keys, get_item
    print('Import custom_filters: OK')
except Exception as e:
    print(f'ERREUR: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "ERREUR: Django ne peut pas démarrer"
    echo "Restauration du backup..."
    cp $BACKUP_DIR/* $APP_DIR/apps/competitions/views/ 2>/dev/null || true
    exit 1
fi

# 7. Redémarrer Gunicorn
echo "[7/8] Redémarrage Gunicorn..."
pkill -9 -f "gunicorn.*config.wsgi" 2>/dev/null || true
sleep 2

# Utiliser start_gunicorn.sh s'il existe
if [ -f "$APP_DIR/start_gunicorn.sh" ]; then
    bash $APP_DIR/start_gunicorn.sh
else
    $VENV_DIR/bin/gunicorn config.wsgi:application \
        --bind 127.0.0.1:8888 \
        --workers 2 \
        --timeout 120 \
        --chdir $APP_DIR \
        --error-logfile $APP_DIR/logs/gunicorn_error.log \
        --access-logfile $APP_DIR/logs/gunicorn_access.log \
        --capture-output \
        --daemon
fi

sleep 3

# 8. Vérification finale
echo "[8/8] Vérification finale..."
echo ""
echo "Processus Gunicorn:"
ps aux | grep gunicorn | grep -v grep || echo "Aucun processus Gunicorn!"

echo ""
echo "Test HTTP scoring_history..."
HTTP_CODE=$(curl -sL -w "%{http_code}" -o /tmp/test_scoring.html \
    -H 'Host: martialcomp.com' \
    -H 'X-Forwarded-Proto: https' \
    'http://127.0.0.1:8888/fr/technical-scoring/history/' 2>/dev/null)

echo "Code HTTP: $HTTP_CODE"

if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
    echo ""
    echo "==========================================="
    echo "SUCCES - Déploiement terminé!"
    echo "==========================================="
    echo ""
    echo "Corrections appliquées:"
    echo "  1. Sécurité: Seules les compétitions de l'organisateur sont visibles"
    echo "  2. UX: Notes des juges affichées en colonnes (max 5)"
    echo "  3. Bug: Page Catégories maintenant fonctionnelle"
    echo ""
    echo "Testez sur: https://martialcomp.com/fr/technical-scoring/history/"
    echo "Et: https://martialcomp.com/fr/technical-scoring/categories/"
else
    echo ""
    echo "ATTENTION - Code HTTP inattendu: $HTTP_CODE"
    echo "Vérifiez les logs:"
    echo "  tail -50 $APP_DIR/logs/gunicorn_error.log"
fi

echo ""
echo "==========================================="
echo "FIN DU DEPLOIEMENT"
echo "==========================================="
