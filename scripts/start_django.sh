#!/bin/bash
# Script de démarrage Django avec configuration production

cd /var/www/vhosts/martialcomp.com/httpdocs

export DJANGO_SETTINGS_MODULE=config.settings.production
export DB_NAME=martialcomp_db
export DB_USER=martialcomp_user
export DB_PASSWORD='AQWZSX123ok,'
export DB_HOST=localhost
export DB_PORT=5432

echo "🚀 Démarrage Django..."
echo "📁 Répertoire: $(pwd)"
echo "⚙️ Settings: $DJANGO_SETTINGS_MODULE"
echo "🗃️ DB: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"

python3 manage.py runserver 0.0.0.0:8080 --noreload 
# Script de démarrage Django avec configuration production

cd /var/www/vhosts/martialcomp.com/httpdocs

export DJANGO_SETTINGS_MODULE=config.settings.production
export DB_NAME=martialcomp_db
export DB_USER=martialcomp_user
export DB_PASSWORD='AQWZSX123ok,'
export DB_HOST=localhost
export DB_PORT=5432

echo "🚀 Démarrage Django..."
echo "📁 Répertoire: $(pwd)"
echo "⚙️ Settings: $DJANGO_SETTINGS_MODULE"
echo "🗃️ DB: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"

python3 manage.py runserver 0.0.0.0:8080 --noreload 