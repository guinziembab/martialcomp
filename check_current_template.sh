#\!/bin/bash
# Vérifier quel template est utilisé actuellement

echo "================================================"
echo "🔍 VÉRIFICATION DU TEMPLATE ACTUEL"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification dans la vue federation_dashboard..."
echo "================================================="
echo "📋 Template utilisé dans la fonction:"
grep -A2 -B2 "return render.*federation.*\.html" apps/competitions/views/dashboard/federations.py  < /dev/null |  grep -n "federation_dashboard" -A20 | grep "return render"

echo ""
echo "2️⃣ Contenu actuel autour de la ligne du return..."
echo "================================================"
echo "📋 Lignes 125-135 de federations.py:"
sed -n '125,135p' apps/competitions/views/dashboard/federations.py

echo ""
echo "3️⃣ Templates federation disponibles..."
echo "===================================="
ls -la apps/competitions/templates/competitions/dashboard/federation*.html | tail -10

echo ""
echo "4️⃣ Vérification de la taille du template actuel..."
echo "================================================="
if [ -f "apps/competitions/templates/competitions/dashboard/federation_simple.html" ]; then
    echo "📋 Taille du template simple:"
    wc -l apps/competitions/templates/competitions/dashboard/federation_simple.html
fi

if [ -f "apps/competitions/templates/competitions/dashboard/federation.html" ]; then
    echo "📋 Taille du template complet:"
    wc -l apps/competitions/templates/competitions/dashboard/federation.html
fi

REMOTE_COMMANDS
