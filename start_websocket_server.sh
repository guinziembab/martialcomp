#!/bin/bash
# Script pour démarrer le serveur avec support WebSocket complet

echo "🚀 Démarrage du serveur MartialComp avec support WebSocket..."
echo "================================================"

# Activer l'environnement virtuel
source venv_regen/bin/activate

# Vérifier Redis
echo "🔍 Vérification de Redis..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis est actif"
else
    echo "⚠️  Redis n'est pas actif. Tentative de démarrage..."
    sudo service redis-server start
    sleep 2
    redis-cli ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Redis démarré avec succès"
    else
        echo "❌ Impossible de démarrer Redis"
        exit 1
    fi
fi

# Vérifier l'installation de daphne
echo "🔍 Vérification de Daphne..."
python -c "import daphne" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installation de Daphne..."
    pip install daphne
fi

# Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate

# Démarrer le serveur avec Daphne
echo ""
echo "🌐 Démarrage du serveur sur http://127.0.0.1:8888"
echo "🔌 WebSocket disponible sur ws://127.0.0.1:8888/ws/"
echo ""
echo "URLs importantes:"
echo "- Page d'accueil: http://127.0.0.1:8888/fr/"
echo "- Test WebSocket: http://127.0.0.1:8888/fr/competitions/websocket-test/"
echo "- Admin: http://127.0.0.1:8888/admin/"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo "================================================"

# Démarrer avec Daphne (supporte nativement WebSocket)
python -m daphne -b 0.0.0.0 -p 8888 config.asgi:application