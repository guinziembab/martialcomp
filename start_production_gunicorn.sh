#!/bin/bash
# Script pour démarrer Gunicorn avec les bonnes variables d'environnement

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "Configuration et démarrage de Gunicorn en production..."

# 1. Créer un script de démarrage sur le serveur
ssh "$PRODUCTION_SERVER" "cat > $PRODUCTION_PATH/start_gunicorn.sh << 'EOF'
#!/bin/bash
cd /var/www/vhosts/martialcomp.com/httpdocs

# Définir les variables d'environnement
export DJANGO_ENV=production
export DJANGO_SETTINGS_MODULE=config.settings
export DB_NAME=martialcomp_db
export DB_USER=martialcomp_user
export DB_PASSWORD='AQWZSX123ok,'
export DB_HOST=localhost
export DB_PORT=5432

# Tuer les anciens processus
pkill -f gunicorn || true
sleep 2

# Démarrer Gunicorn
/var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --daemon \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    config.wsgi:application

echo 'Gunicorn démarré avec DJANGO_ENV=production'
EOF
chmod +x $PRODUCTION_PATH/start_gunicorn.sh"

# 2. Exécuter le script
echo "Démarrage de Gunicorn..."
ssh "$PRODUCTION_SERVER" "$PRODUCTION_PATH/start_gunicorn.sh"

# 3. Vérification
sleep 3
echo "Vérification..."
COUNT=$(ssh "$PRODUCTION_SERVER" "ps aux | grep gunicorn | grep -v grep | wc -l")
echo "Processus Gunicorn: $COUNT"

# 4. Test
echo "Test du site..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/fr/)
echo "Code HTTP: $HTTP_CODE"

echo "Script terminé!"