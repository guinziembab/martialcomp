#!/bin/bash

echo "🔍 DÉPANNAGE SERVEUR DJANGO"
echo "============================"

PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

# 1. Vérifier l'emplacement
echo "1️⃣ Vérification de l'emplacement..."
if [ -d "$PROJECT_DIR" ]; then
    echo "✅ Répertoire projet: $PROJECT_DIR"
    cd "$PROJECT_DIR"
else
    echo "❌ Répertoire projet non trouvé: $PROJECT_DIR"
    exit 1
fi

# 2. Vérifier les fichiers essentiels
echo "2️⃣ Vérification des fichiers essentiels..."
if [ -f "manage.py" ]; then
    echo "✅ manage.py trouvé"
else
    echo "❌ manage.py manquant"
fi

if [ -d "venv" ]; then
    echo "✅ Environnement virtuel trouvé"
else
    echo "❌ Environnement virtuel manquant"
fi

if [ -f "config/wsgi.py" ]; then
    echo "✅ config/wsgi.py trouvé"
else
    echo "❌ config/wsgi.py manquant"
fi

# 3. Vérifier les processus
echo "3️⃣ Vérification des processus..."
GUNICORN_COUNT=$(ps aux | grep gunicorn | grep -v grep | wc -l)
echo "Processus gunicorn actifs: $GUNICORN_COUNT"

NGINX_STATUS=$(systemctl is-active nginx 2>/dev/null || echo "inactive")
echo "Statut nginx: $NGINX_STATUS"

# 4. Vérifier les ports
echo "4️⃣ Vérification des ports..."
PORT_8000=$(netstat -tlnp 2>/dev/null | grep :8000 | wc -l)
echo "Port 8000 (Django): $PORT_8000 connexions"

PORT_80=$(netstat -tlnp 2>/dev/null | grep :80 | wc -l)
echo "Port 80 (HTTP): $PORT_80 connexions"

PORT_443=$(netstat -tlnp 2>/dev/null | grep :443 | wc -l)
echo "Port 443 (HTTPS): $PORT_443 connexions"

# 5. Test simple de Django
echo "5️⃣ Test Django simple..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python3 -c "import django; print('Django version:', django.get_version())" 2>/dev/null || echo "❌ Erreur import Django"
    python3 -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); import django; django.setup(); print('✅ Django setup OK')" 2>/dev/null || echo "❌ Erreur Django setup"
fi

# 6. Vérifier les logs récents
echo "6️⃣ Logs récents..."
if [ -f "/var/log/gunicorn/error.log" ]; then
    echo "--- Dernières erreurs gunicorn ---"
    tail -n 5 /var/log/gunicorn/error.log
fi

if [ -f "/var/log/nginx/martialcomp_error.log" ]; then
    echo "--- Dernières erreurs nginx ---"
    tail -n 5 /var/log/nginx/martialcomp_error.log
fi

echo ""
echo "============================"
echo "🔧 COMMANDES DE CORRECTION"
echo "============================"
echo "Pour redémarrage complet:"
echo "  ./safe_server_restart.sh"
echo ""
echo "Pour redémarrage simple:"
echo "  pkill -f gunicorn"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --daemon"
echo "  systemctl restart nginx"