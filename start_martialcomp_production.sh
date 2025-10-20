#!/bin/bash

# Script de démarrage de MartialComp en production
# Utilise Gunicorn avec Apache comme proxy

set -e

echo "=============================================="
echo "DÉMARRAGE DE MARTIALCOMP EN PRODUCTION"
echo "=============================================="
echo

# Configuration
HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"
VENV="/var/www/vhosts/martialcomp.com/apps/martialcomp/venv"
GUNICORN_PID="/var/run/gunicorn_martialcomp.pid"
GUNICORN_LOG_DIR="/var/log/gunicorn"

# Vérifier qu'on est sur le serveur de production
if [ ! -d "$HTTPDOCS" ]; then
    echo "❌ Ce script doit être exécuté sur le serveur de production"
    exit 1
fi

# Aller dans le répertoire du projet
cd "$HTTPDOCS"

# Vérifier l'environnement virtuel
if [ ! -f "$VENV/bin/python" ]; then
    echo "❌ Environnement virtuel non trouvé: $VENV"
    exit 1
fi

echo "✅ Environnement virtuel trouvé"

# Créer le répertoire de logs si nécessaire
sudo mkdir -p "$GUNICORN_LOG_DIR"
sudo chown www-data:www-data "$GUNICORN_LOG_DIR"

# Arrêter Gunicorn s'il est déjà en cours d'exécution
if [ -f "$GUNICORN_PID" ]; then
    echo "🔄 Arrêt de Gunicorn existant..."
    if kill -0 $(cat "$GUNICORN_PID") 2>/dev/null; then
        kill $(cat "$GUNICORN_PID")
        sleep 2
    fi
    rm -f "$GUNICORN_PID"
fi

# Tuer tous les processus Gunicorn existants
echo "🧹 Nettoyage des processus Gunicorn existants..."
pkill -f "gunicorn.*martialcomp" || true
sleep 2

# Vérifier que le port 8000 est libre
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    echo "⚠️  Le port 8000 est déjà utilisé"
    echo "📋 Processus utilisant le port 8000:"
    netstat -tlnp 2>/dev/null | grep ":8000 "
    echo
    echo "🔄 Tentative de libération du port..."
    fuser -k 8000/tcp 2>/dev/null || true
    sleep 2
fi

# Démarrer Gunicorn
echo "🚀 Démarrage de Gunicorn..."
echo "   - Host: 127.0.0.1:8000"
echo "   - Workers: 3"
echo "   - Timeout: 120s"
echo "   - Logs: $GUNICORN_LOG_DIR/"
echo

# Démarrer Gunicorn en arrière-plan
nohup "$VENV/bin/gunicorn" \
    --bind 127.0.0.1:8000 \
    --workers 3 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --preload \
    --pid "$GUNICORN_PID" \
    --access-logfile "$GUNICORN_LOG_DIR/martialcomp_access.log" \
    --error-logfile "$GUNICORN_LOG_DIR/martialcomp_error.log" \
    --log-level info \
    config.wsgi:application \
    > "$GUNICORN_LOG_DIR/gunicorn_startup.log" 2>&1 &

# Attendre le démarrage
echo "⏳ Attente du démarrage de Gunicorn..."
sleep 5

# Vérifier que Gunicorn fonctionne
if [ -f "$GUNICORN_PID" ] && kill -0 $(cat "$GUNICORN_PID") 2>/dev/null; then
    echo "✅ Gunicorn démarré avec succès (PID: $(cat $GUNICORN_PID))"
else
    echo "❌ Échec du démarrage de Gunicorn"
    echo "📋 Logs d'erreur:"
    cat "$GUNICORN_LOG_DIR/gunicorn_startup.log" 2>/dev/null || echo "Aucun log disponible"
    exit 1
fi

# Test de connectivité
echo "🔍 Test de connectivité..."
if curl -s -f http://127.0.0.1:8000/fr/ > /dev/null; then
    echo "✅ Application accessible sur http://127.0.0.1:8000"
else
    echo "⚠️  Application non accessible sur le port 8000"
fi

# Vérifier Apache
echo "🔍 Vérification d'Apache..."
if systemctl is-active --quiet apache2; then
    echo "✅ Apache est actif"
else
    echo "⚠️  Apache n'est pas actif"
    echo "🔄 Démarrage d'Apache..."
    sudo systemctl start apache2
fi

# Test final
echo "🌐 Test final de l'application..."
if curl -s -f https://martialcomp.com/fr/ > /dev/null; then
    echo "✅ Site accessible via HTTPS: https://martialcomp.com"
else
    echo "⚠️  Site non accessible via HTTPS"
fi

echo
echo "=============================================="
echo "RÉSUMÉ DU DÉMARRAGE"
echo "=============================================="
echo "✅ Gunicorn: $(cat $GUNICORN_PID 2>/dev/null || echo 'Non démarré')"
echo "✅ Apache: $(systemctl is-active apache2 2>/dev/null || echo 'Inactif')"
echo "✅ Site: https://martialcomp.com"
echo
echo "📋 Commandes utiles:"
echo "   - Arrêter: pkill -f 'gunicorn.*martialcomp'"
echo "   - Logs: tail -f $GUNICORN_LOG_DIR/martialcomp_error.log"
echo "   - Statut: ps aux | grep gunicorn"
echo
echo "🎉 MartialComp est maintenant en ligne!"