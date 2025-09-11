#!/bin/bash

# Script de démarrage Gunicorn pour production - Port 8002 uniquement
echo "🚀 Démarrage de Gunicorn sur le port 8002..."

# Tuer tous les processus gunicorn existants
pkill -f gunicorn
sleep 3

# Vérifier qu'aucun processus ne reste
if pgrep -f gunicorn > /dev/null; then
    echo "⚠️  Forçage de l'arrêt des processus gunicorn..."
    pkill -9 -f gunicorn
    sleep 2
fi

# Démarrer gunicorn sur le port 8002 uniquement
cd /var/www/vhosts/martialcomp.com/httpdocs
sudo -u www-data .venv/bin/gunicorn \
    --bind 127.0.0.1:8002 \
    --workers 2 \
    --timeout 30 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    config.wsgi:application \
    --daemon

echo "✅ Gunicorn démarré sur le port 8002"
echo "📊 Vérification des processus :"
ps aux | grep gunicorn | grep -v grep 