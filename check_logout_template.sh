#!/bin/bash
# Vérifier le template logout et le formulaire

echo "================================================"
echo "🔍 VÉRIFICATION TEMPLATE LOGOUT"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Contenu du template logout..."
echo "================================="
if [ -f apps/competitions/templates/account/logout.html ]; then
    echo "📋 Template logout actuel:"
    cat apps/competitions/templates/account/logout.html | grep -A20 -B5 "form\|csrf\|POST\|submit"
else
    echo "❌ Template logout non trouvé"
fi

echo ""
echo "2️⃣ Vérification du formulaire de logout..."
echo "=========================================="
grep -n "method.*post\|method.*POST" apps/competitions/templates/account/logout.html

echo ""
echo "3️⃣ Recherche d'autres erreurs récentes..."
echo "========================================="
echo "📋 Dernières erreurs complètes:"
tail -50 logs/django.log | grep -A10 "logout.*500\|logout.*ERROR\|Internal Server Error"

echo ""
echo "📋 Erreurs Gunicorn complètes:"
tail -50 logs/gunicorn_error.log | grep -A10 -B5 "logout\|NoneType"

REMOTE_COMMANDS