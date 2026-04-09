#!/bin/bash
# Script pour vider complètement le cache et forcer le rechargement
# Date: 24 novembre 2024

echo "=========================================="
echo "VIDAGE COMPLET DU CACHE"
echo "=========================================="

ssh martialcomp-production << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "→ Activation de l'environnement virtuel..."
source /var/www/vhosts/martialcomp.com/venv/bin/activate

echo ""
echo "→ Vérification que base.html contient les corrections..."
grep -c "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html

echo ""
echo "→ Affichage des lignes corrigées dans base.html..."
grep -n "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html

echo ""
echo "→ Suppression COMPLÈTE du cache Python..."
find . -type d -name "__pycache__" -print -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -print -delete 2>/dev/null
find . -type f -name "*.pyo" -print -delete 2>/dev/null

echo ""
echo "→ Suppression du cache Django..."
python3 manage.py clear_cache 2>/dev/null || echo "  (commande clear_cache non disponible)"

echo ""
echo "→ Rechargement forcé de l'application Passenger..."
mkdir -p tmp
touch tmp/restart.txt
sleep 2
touch tmp/restart.txt

echo ""
echo "→ Vérification de la date de modification du fichier restart.txt..."
ls -lh tmp/restart.txt

echo ""
echo "✓ Cache vidé et application rechargée!"
echo ""
echo "IMPORTANT: Vous devez maintenant:"
echo "1. Vider le cache de votre navigateur (Ctrl+Shift+Delete)"
echo "2. Ou ouvrir une fenêtre de navigation privée"
echo "3. Recharger la page avec Ctrl+F5 (rechargement forcé)"

ENDSSH

echo ""
echo "=========================================="
echo "TERMINÉ"
echo "=========================================="
