#!/bin/bash
# Script simplifié de synchronisation

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "Synchronisation simplifiée de la production..."
echo "Date: $(date)"
echo ""

# 1. Arrêter Gunicorn
echo "1. Arrêt de Gunicorn..."
ssh "$PRODUCTION_SERVER" "pkill -f gunicorn || true"

# 2. Synchroniser uniquement le dossier apps
echo "2. Synchronisation du dossier apps..."
rsync -avz --delete \
    --exclude='*.pyc' \
    --exclude='__pycache__/' \
    --exclude='migrations/__pycache__/' \
    --exclude='*.backup*' \
    "$PROJECT_ROOT/apps/" \
    "$PRODUCTION_SERVER:$PRODUCTION_PATH/apps/"

# 3. Synchroniser le dossier config (sauf production.py)
echo "3. Synchronisation du dossier config..."
rsync -avz \
    --exclude='*.pyc' \
    --exclude='__pycache__/' \
    --exclude='settings/production.py' \
    --exclude='settings/local.py' \
    "$PROJECT_ROOT/config/" \
    "$PRODUCTION_SERVER:$PRODUCTION_PATH/config/"

# 4. Synchroniser les templates
echo "4. Synchronisation des templates..."
rsync -avz --delete \
    "$PROJECT_ROOT/templates/" \
    "$PRODUCTION_SERVER:$PRODUCTION_PATH/templates/"

# 5. Synchroniser locale
echo "5. Synchronisation des traductions..."
rsync -avz \
    --exclude='*.po~' \
    --exclude='*.mo' \
    "$PROJECT_ROOT/locale/" \
    "$PRODUCTION_SERVER:$PRODUCTION_PATH/locale/"

# 6. Compiler les messages
echo "6. Compilation des messages..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py compilemessages --ignore=venv"

# 7. Collecter les fichiers statiques
echo "7. Collecte des fichiers statiques..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py collectstatic --noinput"

# 8. Redémarrer Gunicorn
echo "8. Redémarrage de Gunicorn..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && /var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 --daemon config.wsgi:application"

# 9. Recharger nginx
echo "9. Rechargement de nginx..."
ssh "$PRODUCTION_SERVER" "sudo systemctl reload nginx"

# 10. Test
echo "10. Test du site..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/)
echo "Statut HTTP: $HTTP_STATUS"

echo "Synchronisation terminée!"