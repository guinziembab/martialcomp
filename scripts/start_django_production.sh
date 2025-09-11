#!/bin/bash

# Script de démarrage robuste de Django en production
echo "=== Démarrage de Django MartialComp en production ==="

# Variables
PROJECT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_DIR="$PROJECT_DIR/venv"
GUNICORN_PORT=8000
WORKERS=3

# Vérifications préliminaires
echo "1. Vérifications préliminaires..."

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    echo "❌ ERREUR: manage.py non trouvé dans $PROJECT_DIR"
    echo "Assurez-vous que l'application Django est bien déployée"
    exit 1
fi

cd "$PROJECT_DIR"

# Vérifier l'environnement virtuel
if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "⚠️  Environnement virtuel non trouvé, création..."
    python3 -m venv "$VENV_DIR"
fi

# Activer l'environnement virtuel
echo "2. Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"

# Installer/mettre à jour les dépendances
echo "3. Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || echo "⚠️  Fichier requirements.txt non trouvé"
pip install gunicorn psycopg2-binary

# Vérifier la configuration Django
echo "4. Vérification de la configuration Django..."
python manage.py check --deploy

if [ $? -ne 0 ]; then
    echo "⚠️  Avertissements de configuration détectés, mais on continue..."
fi

# Appliquer les migrations
echo "5. Application des migrations..."
python manage.py migrate

# Collecter les fichiers statiques
echo "6. Collecte des fichiers statiques..."
mkdir -p static
python manage.py collectstatic --noinput

# Créer les répertoires de logs
echo "7. Création des répertoires de logs..."
mkdir -p /var/log/gunicorn
chown www-data:www-data /var/log/gunicorn 2>/dev/null || true

# Arrêter les processus Django existants
echo "8. Arrêt des processus Django existants..."
pkill -f "manage.py runserver" || true
pkill -f "gunicorn.*martialcomp" || true

# Attendre un moment
sleep 3

# Vérifier si le port est libre
echo "9. Vérification du port $GUNICORN_PORT..."
if netstat -tlnp 2>/dev/null | grep ":$GUNICORN_PORT " > /dev/null; then
    echo "⚠️  Port $GUNICORN_PORT déjà utilisé, tentative d'arrêt du processus..."
    fuser -k $GUNICORN_PORT/tcp 2>/dev/null || true
    sleep 2
fi

# Créer le fichier de configuration gunicorn
echo "10. Configuration de gunicorn..."
cat > gunicorn.conf.py << EOF
# Configuration Gunicorn pour MartialComp
bind = "127.0.0.1:$GUNICORN_PORT"
workers = $WORKERS
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 60
keepalive = 2

# Logs
accesslog = "/var/log/gunicorn/martialcomp_access.log"
errorlog = "/var/log/gunicorn/martialcomp_error.log"
loglevel = "info"

# Processus
user = "www-data"
group = "www-data"
daemon = True
pidfile = "/var/run/gunicorn/martialcomp.pid"

# Performance
preload_app = True
EOF

# Créer le répertoire pour le fichier PID
mkdir -p /var/run/gunicorn
chown www-data:www-data /var/run/gunicorn 2>/dev/null || true

# Démarrer avec gunicorn
echo "11. Démarrage de gunicorn..."
gunicorn config.wsgi:application --config gunicorn.conf.py

# Vérifier que le processus est démarré
sleep 3
if pgrep -f "gunicorn.*martialcomp" > /dev/null; then
    echo "✅ Gunicorn démarré avec succès"
    
    # Test de santé
    echo "12. Test de santé de l'application..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$GUNICORN_PORT/fr/ 2>/dev/null || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Application Django répondant correctement (HTTP $HTTP_CODE)"
    else
        echo "⚠️  Application Django répond avec le code HTTP: $HTTP_CODE"
        echo "Vérifiez les logs: tail -f /var/log/gunicorn/martialcomp_error.log"
    fi
    
    # Afficher les informations de status
    echo ""
    echo "=== Status de l'application ==="
    echo "Processus gunicorn: $(pgrep -f "gunicorn.*martialcomp" | wc -l)"
    echo "Port d'écoute: $GUNICORN_PORT"
    echo "Workers: $WORKERS"
    echo "PID principal: $(pgrep -f "gunicorn.*martialcomp" | head -1)"
    echo "Logs d'accès: /var/log/gunicorn/martialcomp_access.log"
    echo "Logs d'erreur: /var/log/gunicorn/martialcomp_error.log"
    echo ""
    echo "✅ Django MartialComp démarré avec succès !"
    echo "L'application est accessible sur http://127.0.0.1:$GUNICORN_PORT"
    
else
    echo "❌ ERREUR: Impossible de démarrer gunicorn"
    echo "Vérifiez les logs d'erreur:"
    echo "tail -f /var/log/gunicorn/martialcomp_error.log"
    exit 1
fi