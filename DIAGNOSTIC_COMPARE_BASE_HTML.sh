#!/bin/bash
# Script de diagnostic pour comparer base.html local vs production
# Date: 24 novembre 2024

echo "=================================================="
echo "DIAGNOSTIC: Comparaison base.html local vs production"
echo "=================================================="
echo ""

echo "=== 1. Vérification du fichier LOCAL ==="
echo "Fichier: apps/competitions/templates/base.html"
echo ""
echo "Lignes avec 'const currentLang' :"
grep -n "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html
echo ""

echo "Lignes 231, 340, 358 (devrait contenir les corrections) :"
sed -n '231p;340p;358p' apps/competitions/templates/base.html
echo ""

echo "=== 2. Vérification du fichier PRODUCTION ==="
ssh pierrep99@martialcomp.com << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "Fichier: apps/competitions/templates/base.html"
echo ""
echo "Lignes avec 'const currentLang' :"
grep -n "const currentLang = document.documentElement.lang" apps/competitions/templates/base.html 2>/dev/null || echo "ERREUR: Corrections introuvables!"
echo ""

echo "Lignes 231, 340, 358 (devrait contenir les corrections) :"
sed -n '231p;340p;358p' apps/competitions/templates/base.html 2>/dev/null || echo "ERREUR: Impossible de lire les lignes!"
echo ""

echo "Date de dernière modification du fichier :"
ls -lh apps/competitions/templates/base.html
echo ""

echo "=== 3. Recherche d'ANCIENS tags {% url %} problématiques ==="
echo "Ces tags NE DOIVENT PAS être présents dans le JavaScript :"
grep -n "{% url.*notifications" apps/competitions/templates/base.html | head -10
if [ $? -ne 0 ]; then
    echo "✅ Aucun ancien tag {% url %} trouvé - CORRECT"
fi
echo ""

echo "=== 4. Vérification du cache Python ==="
find apps/competitions -name "__pycache__" -type d | wc -l
echo "^ Nombre de répertoires __pycache__ (devrait être 0 après nettoyage)"
echo ""

echo "=== 5. Vérification du statut Passenger ==="
ls -lh tmp/restart.txt 2>/dev/null || echo "ATTENTION: tmp/restart.txt n'existe pas!"
echo ""

ENDSSH

echo ""
echo "=================================================="
echo "FIN DU DIAGNOSTIC"
echo "=================================================="
