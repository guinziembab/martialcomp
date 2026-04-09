#!/bin/bash
# Commandes à exécuter sur le serveur de production

echo "📁 Navigation vers le répertoire Django..."
echo "cd /var/www/vhosts/martialcomp.com/httpdocs/"
echo ""

echo "📋 Sauvegarde du fichier actuel..."
echo "cp apps/competitions/templates/competitions/club/competition_registration_simple.html apps/competitions/templates/competitions/club/competition_registration_simple.html.bak_$(date +%Y%m%d_%H%M%S)"
echo ""

echo "🔧 Application de la correction..."
echo "sed -i 's/competition_management_simple/competition_management_detail/g' apps/competitions/templates/competitions/club/competition_registration_simple.html"
echo ""

echo "✅ Vérification de la correction..."
echo "grep -n 'competition_management' apps/competitions/templates/competitions/club/competition_registration_simple.html | grep 394"
echo ""

echo "🔄 Redémarrage de l'application..."
echo "# Option 1 - Si Gunicorn avec systemd:"
echo "systemctl restart gunicorn"
echo ""
echo "# Option 2 - Si processus Gunicorn manuel:"
echo "ps aux | grep gunicorn"
echo "kill -HUP [PID_DU_PROCESSUS_GUNICORN]"
echo ""
echo "# Option 3 - Via Plesk:"
echo "plesk bin extension --exec pm2 nodejs restart all"