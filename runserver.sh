#!/bin/bash
# Démarrage rapide du serveur

echo "🚀 Démarrage rapide du serveur MartialComp..."
source venv_regen/bin/activate

# Vérifier si daphne est installé
if command -v daphne &> /dev/null
then
    echo "✅ Utilisation de Daphne (WebSocket optimisé)"
    echo "🌐 Serveur disponible sur http://127.0.0.1:8000"
    daphne -b 0.0.0.0 -p 8000 config.asgi:application
else
    echo "📌 Utilisation du serveur Django standard"
    echo "🌐 Serveur disponible sur http://127.0.0.1:8000"
    python manage.py runserver 0.0.0.0:8000
fi