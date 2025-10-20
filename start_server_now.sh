#!/bin/bash

# Script simple pour démarrer le serveur
echo "🚀 Démarrage du serveur Django sur le port 8888..."
echo ""

# Utiliser l'environnement virtuel regen
if [ -d "./venv_regen" ]; then
    echo "Utilisation de venv_regen..."
    source ./venv_regen/bin/activate
else
    echo "Utilisation de python3 système..."
fi

# Installer les dépendances minimales si nécessaire
pip install django 2>/dev/null || true

echo ""
echo "📍 Le serveur sera accessible sur :"
echo "   http://localhost:8888/"
echo "   http://localhost:8888/competitions/onboarding/"
echo ""

# Démarrer le serveur
python3 manage.py runserver 0.0.0.0:8888 --insecure