#!/bin/bash
# Script rapide pour corriger les disciplines fédération

echo "================================================"
echo "🚀 CORRECTION RAPIDE DISCIPLINES FÉDÉRATION"
echo "================================================"
echo ""

# Se connecter et exécuter directement les commandes
ssh martialcomp-production << 'REMOTE_COMMANDS'
echo "📍 Connexion au serveur de production..."
cd /var/www/vhosts/martialcomp.com/httpdocs

echo ""
echo "1️⃣ Vérification de l'état actuel..."
echo "=================================="
grep -A 5 "class Meta:" apps/competitions/forms/onboarding.py | grep -A 3 "model = Federation" | grep "fields ="

echo ""
echo "2️⃣ Application de la correction..."
echo "=================================="

# Faire un backup
cp apps/competitions/forms/onboarding.py apps/competitions/forms/onboarding.py.backup_$(date +%Y%m%d_%H%M%S)

# Appliquer la correction avec sed
sed -i "/class FederationCreationForm/,/class Meta:/{/fields = \[/s/\]/&/; s/\]/\, 'disciplines'\]/}" apps/competitions/forms/onboarding.py

echo ""
echo "3️⃣ Vérification après correction..."
echo "===================================="
grep -A 5 "class Meta:" apps/competitions/forms/onboarding.py | grep -A 3 "model = Federation" | grep "fields ="

echo ""
echo "4️⃣ Redémarrage des services..."
echo "==============================="
sudo systemctl restart martialcomp
sudo systemctl reload apache2

echo ""
echo "✅ Correction appliquée!"
echo ""
echo "📋 Tester sur: https://app.martialcomp.com/competitions/onboarding/federation/"
REMOTE_COMMANDS