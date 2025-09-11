#!/bin/bash

# Script de démarrage PostgreSQL + Django port 8080
# Résolution: connection to server at "localhost" (127.0.0.1), port 5432 failed

echo "🔧 DÉMARRAGE POSTGRESQL + DJANGO PORT 8080"
echo "=========================================="

PROJECT="/var/www/vhosts/martialcomp.com/httpdocs"
LOGS="/var/www/vhosts/martialcomp.com/logs"

# 1. Vérifier et démarrer PostgreSQL
echo "1. Vérification PostgreSQL..."

# Vérifier si PostgreSQL est installé
if command -v psql >/dev/null 2>&1; then
    echo "✅ PostgreSQL installé"
else
    echo "❌ PostgreSQL non installé"
    exit 1
fi

# Vérifier le statut du service
if systemctl is-active --quiet postgresql; then
    echo "✅ PostgreSQL déjà en cours d'exécution"
else
    echo "⚠️  PostgreSQL arrêté, démarrage..."
    systemctl start postgresql
    sleep 3
    
    if systemctl is-active --quiet postgresql; then
        echo "✅ PostgreSQL démarré avec succès"
    else
        echo "❌ Échec démarrage PostgreSQL"
        systemctl status postgresql
        exit 1
    fi
fi

# Activer PostgreSQL au démarrage
systemctl enable postgresql

# 2. Test de connexion PostgreSQL
echo "2. Test connexion PostgreSQL..."
if sudo -u postgres psql -c "SELECT version();" >/dev/null 2>&1; then
    echo "✅ Connexion PostgreSQL réussie"
else
    echo "❌ Problème de connexion PostgreSQL"
    echo "Tentative de diagnostic..."
    
    # Diagnostic PostgreSQL
    echo "Status: $(systemctl is-active postgresql)"
    echo "Logs PostgreSQL:"
    journalctl -u postgresql --no-pager -n 10
fi

# 3. Vérifier la base de données MartialComp
echo "3. Vérification base de données..."
cd "$PROJECT"
source venv/bin/activate

# Variables Django
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="$PROJECT"

# Test de connexion Django à la DB
echo "Test connexion Django..."
if python manage.py migrate --check >/dev/null 2>&1; then
    echo "✅ Connexion Django-PostgreSQL OK"
else
    echo "⚠️  Problème de connexion, tentative de migration..."
    python manage.py migrate
fi

# 4. Arrêter les processus Django existants
echo "4. Nettoyage processus Django..."
pkill -f "manage.py runserver" || true
fuser -k 8080/tcp || true
sleep 3

# 5. Ouvrir firewall
echo "5. Configuration firewall..."
iptables -I INPUT -p tcp --dport 8080 -j ACCEPT 2>/dev/null || true

# 6. Démarrage Django
echo "6. Démarrage Django sur port 8080..."
mkdir -p "$LOGS"

nohup python manage.py runserver 0.0.0.0:8080 > "$LOGS/django_8080_postgres.log" 2>&1 &
DJANGO_PID=$!

echo "Django PID: $DJANGO_PID"

# 7. Attendre et vérifier
echo "7. Vérification démarrage..."
sleep 15  # Plus de temps pour que PostgreSQL se connecte

# Test de connectivité
if curl -s http://localhost:8080/ >/dev/null 2>&1; then
    echo "✅ SUCCESS - MartialComp accessible !"
    echo ""
    echo "🌐 URLS D'ACCÈS:"
    echo "   - Principal: http://martialcomp.com:8080"
    echo "   - IP directe: http://212.227.78.104:8080"
    echo "   - Admin: http://martialcomp.com:8080/admin/"
    echo ""
    echo "📋 INFORMATIONS:"
    echo "   - Django PID: $DJANGO_PID"
    echo "   - PostgreSQL: $(systemctl is-active postgresql)"
    echo "   - Logs Django: $LOGS/django_8080_postgres.log"
    echo ""
    echo "🔍 TEST RAPIDE:"
    curl -I http://localhost:8080/ | head -3
    
else
    echo "❌ Django ne répond pas encore"
    echo "Logs Django:"
    tail -20 "$LOGS/django_8080_postgres.log"
    echo ""
    echo "Diagnostic:"
    echo "PostgreSQL: $(systemctl is-active postgresql)"
    echo "Processus Django: $(ps aux | grep manage.py | grep -v grep)"
    echo "Port 8080: $(netstat -tlnp | grep 8080)"
fi

echo ""
echo "✅ Script terminé" 