#!/bin/bash
# Déploiement rapide MartialComp sur port 8080 - Ionos
# Solution immédiate pour port 80 non disponible

set -e

echo "🚀 DÉPLOIEMENT MARTIALCOMP - PORT 8080"
echo "======================================"

PROJECT="/var/www/vhosts/martialcomp.com/httpdocs"
LOGS="/var/www/vhosts/martialcomp.com/logs"

# Préparation
mkdir -p "$LOGS" && chown -R www-data:www-data "$LOGS"
cd "$PROJECT"

# Arrêt processus existants
pkill -f "manage.py runserver" || true
pkill -f "gunicorn" || true
fuser -k 8080/tcp || true
sleep 3

# Activation environnement
source venv/bin/activate

# Variables Django
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT"

# Firewall
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
iptables-save > /etc/iptables/rules.v4 2>/dev/null || true

# Collecte statiques
python manage.py collectstatic --noinput --clear

# Démarrage Django
nohup python manage.py runserver 0.0.0.0:8080 > "$LOGS/django_8080.log" 2>&1 &
PID=$!

sleep 8

# Vérification
if curl -s http://localhost:8080/ >/dev/null; then
    echo "✅ SUCCESS - Django démarré sur port 8080"
    echo "🌐 URL: http://martialcomp.com:8080"
    echo "📋 PID: $PID"
    echo "📄 Logs: $LOGS/django_8080.log"
    echo "🔍 Test externe: curl -I http://martialcomp.com:8080/"
else
    echo "❌ ERREUR - Django ne répond pas"
    echo "Logs:"
    tail -20 "$LOGS/django_8080.log"
    exit 1
fi 