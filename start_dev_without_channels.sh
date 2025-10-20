#!/bin/bash

# Script pour démarrer le serveur de développement sans channels
echo "🚀 Démarrage du serveur Django (sans channels)..."
echo ""

# Variables
PORT=8888
HOST=0.0.0.0

# Exporter la variable pour ignorer channels
export DJANGO_SKIP_CHANNELS=1

# Informations de connexion
echo "=================================="
echo "📍 SERVEUR DE DÉVELOPPEMENT"
echo "=================================="
echo ""
echo "Le serveur va démarrer sur :"
echo "  - http://localhost:${PORT}"
echo "  - http://127.0.0.1:${PORT}"
echo ""
echo "🔗 LIENS DE TEST ONBOARDING:"
echo ""
echo "1. Page d'accueil onboarding :"
echo "   http://localhost:${PORT}/competitions/onboarding/"
echo ""
echo "2. Création de club (vue sécurisée) :"
echo "   http://localhost:${PORT}/competitions/onboarding/club/creation/"
echo ""
echo "3. Création de fédération (vue sécurisée) :"
echo "   http://localhost:${PORT}/competitions/onboarding/federation/"
echo ""
echo "4. Page d'erreur de test :"
echo "   http://localhost:${PORT}/competitions/onboarding/error/"
echo ""
echo "5. Page de finalisation :"
echo "   http://localhost:${PORT}/competitions/onboarding/complete/"
echo ""
echo "=================================="
echo ""
echo "Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

# Démarrer Django
python3 manage.py runserver ${HOST}:${PORT} --skip-checks 2>&1 | grep -v "ModuleNotFoundError: No module named 'channels'" || true