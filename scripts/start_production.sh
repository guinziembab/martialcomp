#!/bin/bash

# Script de démarrage de MartialComp en production
echo "=== Démarrage de MartialComp en production ==="

# Variables
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="$PROJECT_DIR/venv"
GUNICORN_PORT=8000

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    echo "Erreur: manage.py non trouvé dans $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

# Activer l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"

# Installer gunicorn si nécessaire
if ! command -v gunicorn &> /dev/null; then
    echo "Installation de gunicorn..."
    pip install gunicorn
fi

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate

# Arrêter les processus Django existants
echo "Arrêt des processus Django existants..."
pkill -f "manage.py runserver" || true
pkill -f "gunicorn" || true

# Attendre un moment
sleep 2

# Démarrer avec gunicorn
echo "Démarrage de gunicorn sur le port $GUNICORN_PORT..."
gunicorn config.wsgi:application \
    --bind 0.0.0.0:$GUNICORN_PORT \
    --workers 3 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 60 \
    --keep-alive 2 \
    --user www-data \
    --group www-data \
    --log-level info \
    --access-logfile /var/log/gunicorn/martialcomp_access.log \
    --error-logfile /var/log/gunicorn/martialcomp_error.log \
    --daemon

echo "=== MartialComp démarré avec succès ==="
echo "L'application est accessible sur http://localhost:$GUNICORN_PORT"
echo "Logs d'accès: /var/log/gunicorn/martialcomp_access.log"
echo "Logs d'erreur: /var/log/gunicorn/martialcomp_error.log"