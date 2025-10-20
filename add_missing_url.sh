#!/bin/bash
# Ajouter l'URL manquante federation_manage_settings

echo "================================================"
echo "🔧 AJOUT DE L'URL MANQUANTE"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Vérification des URLs existantes..."
echo "====================================="
echo "URLs federation actuelles:"
grep -E "path.*federation.*manage" apps/competitions/urls/dashboard.py | grep -v "^#"

echo ""
echo "2️⃣ Ajout de l'URL manquante..."
echo "============================="

# Trouver la dernière URL federation et ajouter après
LINE_NUM=$(grep -n "federation_manage_reports" apps/competitions/urls/dashboard.py | cut -d: -f1 | tail -1)

if [ -n "$LINE_NUM" ]; then
    # Ajouter après la ligne federation_manage_reports
    sed -i "${LINE_NUM}a\\    path('federations/<int:federation_id>/settings/', federations.federation_manage_settings, name='federation_manage_settings')," apps/competitions/urls/dashboard.py
    echo "✅ URL ajoutée après la ligne $LINE_NUM"
else
    echo "❌ Impossible de trouver où insérer l'URL"
    # Ajouter avant la fin des patterns
    sed -i "/^]$/i\\    path('federations/<int:federation_id>/settings/', federations.federation_manage_settings, name='federation_manage_settings')," apps/competitions/urls/dashboard.py
fi

echo ""
echo "3️⃣ Vérification de l'ajout..."
echo "==========================="
grep -n "federation_manage_settings" apps/competitions/urls/dashboard.py || echo "❌ URL toujours manquante"

echo ""
echo "4️⃣ Redémarrage du service..."
echo "==========================="
sudo systemctl restart martialcomp
sleep 3

echo ""
echo "5️⃣ Test final..."
echo "==============="
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

EOF

echo ""
echo "================================================"
echo "✅ URL AJOUTÉE"
echo "================================================"