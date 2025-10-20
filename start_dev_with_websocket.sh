#!/bin/bash
# Script pour démarrer le serveur de développement avec support WebSocket

echo "🚀 Démarrage du serveur MartialComp avec WebSocket..."
echo "================================================"

# Activer l'environnement virtuel
source venv_regen/bin/activate

# Vérifier Redis
echo "🔍 Vérification de Redis..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis est actif"
else
    echo "⚠️  Redis n'est pas actif. Redis est requis pour WebSocket!"
    echo "Démarrez Redis avec: sudo service redis-server start"
    exit 1
fi

# Migrer la base de données
echo "🔄 Application des migrations..."
python manage.py migrate

echo ""
echo "🌐 Démarrage du serveur Django avec Channels..."
echo "📍 Adresse: http://127.0.0.1:8888"
echo ""
echo "URLs disponibles:"
echo "- Test WebSocket: http://127.0.0.1:8888/fr/competitions/websocket-test/"
echo "- Admin: http://127.0.0.1:8888/admin/"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo "================================================"
echo ""

# Utiliser runserver standard - Channels s'intègre automatiquement
python manage.py runserver 0.0.0.0:8888