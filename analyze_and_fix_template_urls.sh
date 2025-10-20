#!/bin/bash
# Analyser et corriger les URLs dans le template

echo "================================================"
echo "🔍 ANALYSE DES URLs DANS LE TEMPLATE"
echo "================================================"
echo ""

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Recherche des URLs dans le template..."
echo "========================================"
echo "URLs trouvées:"
grep -o "{% url '[^']*'" apps/competitions/templates/competitions/dashboard/federation.html | sort | uniq | head -20

echo ""
echo "2️⃣ Vérification des vues correspondantes..."
echo "=========================================="
echo "Vues définies dans federations.py:"
grep "^def " apps/competitions/views/dashboard/federations.py | awk '{print $2}' | cut -d'(' -f1 | sort

echo ""
echo "3️⃣ Création d'un mapping des URLs..."
echo "==================================="
# Créer un script de correction
cat > /tmp/fix_urls.sh << 'SCRIPT'
#!/bin/bash

# Corriger les URLs qui ne correspondent pas
cd /var/www/vhosts/martialcomp.com/httpdocs

# Sauvegarder
cp apps/competitions/templates/competitions/dashboard/federation.html \
   apps/competitions/templates/competitions/dashboard/federation_backup_urls.html

# Remplacer les URLs problématiques
# Si les URLs utilisent un namespace différent, les corriger
sed -i "s|{% url 'competitions:federations:|{% url 'competitions:dashboard:|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|{% url 'federations:|{% url 'competitions:dashboard:|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

# Corriger les noms de vues spécifiques
sed -i "s|federation_clubs_list|federation_manage_clubs|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_competitions_list|federation_manage_competitions|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_practitioners_list|federation_manage_practitioners|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_judges_list|federation_manage_judges|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_licenses_list|federation_manage_licenses|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_grades|federation_manage_certifications|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_statistics|federation_manage_reports|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

sed -i "s|federation_settings_view|federation_manage_settings|g" \
    apps/competitions/templates/competitions/dashboard/federation.html

echo "✅ URLs corrigées"
SCRIPT

chmod +x /tmp/fix_urls.sh
/tmp/fix_urls.sh

echo ""
echo "4️⃣ Vérification après correction..."
echo "=================================="
echo "Nouvelles URLs (10 premières):"
grep -o "{% url '[^']*'" apps/competitions/templates/competitions/dashboard/federation.html | sort | uniq | head -10

echo ""
echo "5️⃣ Redémarrage du service..."
echo "==========================="
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "6️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

EOF

echo ""
echo "================================================"
echo "✅ ANALYSE ET CORRECTIONS TERMINÉES"
echo "================================================"