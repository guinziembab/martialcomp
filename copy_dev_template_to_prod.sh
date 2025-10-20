#!/bin/bash
# Copier directement le template de développement vers la production

echo "================================================"
echo "📋 COPIE DU TEMPLATE DE DÉVELOPPEMENT"
echo "================================================"
echo ""

# Copier le template local vers la production
echo "1️⃣ Copie du template federation.html de dev vers prod..."
echo "======================================================"
scp /mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/federation.html \
    martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/federation.html

echo ""
echo "2️⃣ Vérification sur le serveur..."
echo "================================"
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "Taille du fichier copié:"
ls -lh apps/competitions/templates/competitions/dashboard/federation.html

echo ""
echo "Premières lignes du template:"
head -20 apps/competitions/templates/competitions/dashboard/federation.html

echo ""
echo "3️⃣ Redémarrage du service..."
echo "==========================="
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "4️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

EOF

echo ""
echo "================================================"
echo "✅ TEMPLATE DE DÉVELOPPEMENT COPIÉ"
echo "================================================"
echo ""
echo "Le template exact de développement est maintenant"
echo "en production. Tous les liens devraient fonctionner"
echo "exactement comme en développement."