#!/bin/bash
# Script de déploiement simplifié pour corriger l'erreur 500

echo "🚀 Déploiement de la correction de l'erreur 500..."

# Configuration
REMOTE="martialcomp@martialcomp.com:/home/martialcomp/public_html"

# 1. Transférer uniquement le fichier template corrigé
echo "📤 Transfert du template corrigé..."
rsync -avz --progress \
    apps/competitions/templates/competitions/club/competition_registration_simple.html \
    ${REMOTE}/apps/competitions/templates/competitions/club/

echo ""
echo "✅ Template transféré avec succès!"
echo ""
echo "⚠️  IMPORTANT: Connectez-vous au serveur pour redémarrer Django:"
echo "    ssh martialcomp@martialcomp.com"
echo "    cd /home/martialcomp/public_html"
echo "    source venv/bin/activate"
echo "    pkill -f gunicorn"
echo "    gunicorn config.wsgi:application --bind unix:gunicorn.sock --workers 4 --daemon"
echo ""
echo "📌 URL à vérifier: https://martialcomp.com/fr/competitions/club/competition-registration/4/"