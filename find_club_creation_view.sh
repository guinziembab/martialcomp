#!/bin/bash
# Trouver et analyser la vue club creation

echo "================================================"
echo "🔍 RECHERCHE DE LA VUE CLUB CREATION"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Recherche dans les URLs..."
echo "============================"
grep -r "club/creation" apps/competitions/urls/ 2>/dev/null | grep -v ".pyc"

echo ""
echo "2️⃣ Recherche de la vue associée..."
echo "================================="
# Chercher la fonction ou classe qui gère cette URL
find apps/competitions/views -name "*.py" -exec grep -l "club.*creation\|ClubCreation\|create_club" {} \; 2>/dev/null

echo ""
echo "3️⃣ Analyse du fichier views/onboarding..."
echo "========================================"
if [ -f "apps/competitions/views/onboarding/clubs.py" ]; then
    echo "Fichier trouvé : apps/competitions/views/onboarding/clubs.py"
    grep -n "def\|class" apps/competitions/views/onboarding/clubs.py | head -20
else
    # Chercher dans __init__.py ou autres fichiers
    find apps/competitions/views/onboarding -name "*.py" -exec grep -l "club_creation\|ClubCreation" {} \; 2>/dev/null
fi

echo ""
echo "4️⃣ Vérification du rendu du formulaire..."
echo "========================================"
# Chercher comment le formulaire est rendu
find apps/competitions -name "*.py" -exec grep -l "ClubCreationForm" {} \; 2>/dev/null | while read file; do
    echo "Dans $file:"
    grep -B5 -A5 "ClubCreationForm" "$file" | grep -E "(render|template|form)" | head -10
done

echo ""
echo "5️⃣ Test alternatif : modifier la vue..."
echo "====================================="
# Chercher et modifier la vue pour déboguer
VIEW_FILE=$(grep -r "def club_creation\|class ClubCreation" apps/competitions/views/ 2>/dev/null | cut -d: -f1 | head -1)
if [ -n "$VIEW_FILE" ]; then
    echo "Vue trouvée dans : $VIEW_FILE"
    
    # Ajouter un print pour déboguer
    cp "$VIEW_FILE" "$VIEW_FILE.backup_debug"
    
    # Chercher le contexte du formulaire
    grep -n "context\|form" "$VIEW_FILE" | head -20
fi

echo ""
echo "6️⃣ Forcer le rechargement des templates..."
echo "========================================"
# Vider le cache des templates compilés
find . -path "*/templates/*" -name "*.pyc" -delete 2>/dev/null
find . -path "*/__pycache__/*" -name "*.pyc" -delete 2>/dev/null

# Toucher le fichier template pour forcer le rechargement
touch apps/competitions/templates/competitions/onboarding/club_creation.html

echo "✅ Cache vidé et template touché"

echo ""
echo "7️⃣ Redémarrage complet..."
echo "========================"
sudo systemctl restart martialcomp
# Attendre plus longtemps
sleep 5

echo ""
echo "8️⃣ Test avec wget pour voir le HTML complet..."
echo "==========================================="
wget -q -O - https://martialcomp.com/fr/competitions/onboarding/club/creation/ | grep -B10 -A10 "country\|Country\|Pays" | head -30

EOF

echo ""
echo "================================================"
echo "📊 ANALYSE COMPLÈTE"
echo "================================================"