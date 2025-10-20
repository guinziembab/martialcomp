#!/bin/bash
# Script pour démarrer le serveur de développement

echo "🚀 Démarrage du serveur de développement MartialComp..."
echo "================================================"

# Activer l'environnement virtuel
source venv_regen/bin/activate

# Vérifier Redis
echo "🔍 Vérification de Redis..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis est actif"
else
    echo "⚠️  Redis n'est pas actif. Démarrage..."
    sudo service redis-server start
fi

# Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate

# Démarrer le serveur
echo ""
echo "🌐 Démarrage du serveur sur http://127.0.0.1:8000"
echo "🔌 WebSocket disponible sur ws://127.0.0.1:8000/ws/"
echo ""
echo "URLs importantes:"
echo "- Page d'accueil: http://127.0.0.1:8000/fr/"
echo "- Test WebSocket: http://127.0.0.1:8000/fr/competitions/websocket-test/"
echo "- Admin: http://127.0.0.1:8000/admin/"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo "================================================"

# Démarrer avec runserver (supporte WebSocket avec Channels)
python manage.py runserver 0.0.0.0:8000