#!/bin/bash

# Script pour démarrer le serveur Django en arrière-plan
echo "🚀 Démarrage du serveur Django..."

# Tuer tout processus existant sur le port 8888
fuser -k 8888/tcp 2>/dev/null || true

# Démarrer le serveur en arrière-plan
cd /mnt/c/martial_hub_django/martialcomp
nohup python3 manage.py runserver 0.0.0.0:8888 > django_server.log 2>&1 &

# Obtenir le PID
PID=$!
echo "Serveur démarré avec PID: $PID"

# Attendre que le serveur démarre
echo "Attente du démarrage du serveur..."
sleep 5

# Vérifier si le serveur est démarré
if ps -p $PID > /dev/null; then
    echo "✅ Serveur Django en cours d'exécution sur le port 8888"
    echo ""
    echo "📍 URLs disponibles :"
    echo "   - http://localhost:8888/"
    echo "   - http://localhost:8888/competitions/onboarding/"
    echo "   - http://localhost:8888/admin/"
    echo ""
    echo "Pour voir les logs : tail -f django_server.log"
    echo "Pour arrêter : kill $PID"
else
    echo "❌ Erreur lors du démarrage du serveur"
    echo "Vérification des logs..."
    tail -20 django_server.log
fi