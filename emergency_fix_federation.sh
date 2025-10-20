#!/bin/bash
# Fix d'urgence pour l'erreur 500

echo "================================================"
echo "🚨 FIX D'URGENCE ERREUR 500"
echo "================================================"
echo ""

# Se connecter au serveur et exécuter les commandes
ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Diagnostic de l'erreur..."
echo "============================"

# Vérifier si l'URL existe
echo "Recherche de l'URL federation_manage_settings:"
grep -n "federation_manage_settings" apps/competitions/urls/dashboard.py || echo "❌ URL non trouvée dans dashboard.py"

echo ""
echo "Recherche de la fonction:"
grep -n "def federation_manage_settings" apps/competitions/views/dashboard/federations.py || echo "❌ Fonction non trouvée"

echo ""
echo "2️⃣ Forcer le rechargement..."
echo "==========================="

# Tuer tous les processus gunicorn
sudo pkill -f gunicorn

# Attendre un peu
sleep 2

# Redémarrer le service
sudo systemctl restart martialcomp

echo ""
echo "3️⃣ Attente du redémarrage..."
echo "============================"
sleep 5

# Vérifier le statut
sudo systemctl status martialcomp | grep -E "(Active|Main PID)"

echo ""
echo "4️⃣ Test rapide..."
echo "================="
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

echo ""
echo "✅ Redémarrage forcé effectué"

EOF

echo ""
echo "================================================"
echo "✅ FIX D'URGENCE APPLIQUÉ"
echo "================================================"