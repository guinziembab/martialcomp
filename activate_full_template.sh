#\!/bin/bash
# Activer le template complet federation.html

echo "================================================"
echo "🔧 ACTIVATION DU TEMPLATE COMPLET"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Modification de la vue pour utiliser le template complet..."
echo "==========================================================="

# Sauvegarder
cp apps/competitions/views/dashboard/federations.py apps/competitions/views/dashboard/federations.py.backup_template

# Remplacer federation_simple.html par federation.html
sed -i "s/'competitions\/dashboard\/federation_simple\.html'/'competitions\/dashboard\/federation.html'/g" \
    apps/competitions/views/dashboard/federations.py

echo "✅ Vue modifiée"

echo ""
echo "2️⃣ Vérification de la modification..."
echo "===================================="
echo "📋 Templates utilisés après modification:"
grep "return render.*federation.*\.html" apps/competitions/views/dashboard/federations.py  < /dev/null |  head -5

echo ""
echo "3️⃣ Vérification du template complet..."
echo "====================================="
echo "📋 Premières lignes du template complet:"
head -20 apps/competitions/templates/competitions/dashboard/federation.html | grep -E "extends|block|UBLP|federation"

echo ""
echo "4️⃣ Redémarrage du service..."
echo "============================"
sudo systemctl restart martialcomp
echo "✅ Service redémarré"

echo ""
echo "5️⃣ Test avec curl..."
echo "==================="
echo "Test de l'URL: https://martialcomp.com/fr/competitions/dashboard/federation/41/"
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

REMOTE_COMMANDS

echo ""
echo "6️⃣ Test détaillé avec authentification..."
echo "========================================"
ssh martialcomp-production << 'REMOTE_TEST'
cd /var/www/vhosts/martialcomp.com/httpdocs
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.test import Client

client = Client()

print("🔐 Test du template complet:")
print("=" * 50)

if client.login(username='DT_bguinziemba', password='AQWZSX123ok,'):
    resp = client.get('/competitions/dashboard/federation/41/', HTTP_HOST='martialcomp.com', follow=True)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        content = resp.content.decode('utf-8')
        
        # Vérifier que c'est bien le template complet
        indicators = {
            'UBLP': 'Nom fédération',
            'card': 'Cards Bootstrap',
            'dashboard-card': 'Classes du template complet',
            'federation_manage': 'Liens de gestion',
            'fa-': 'Icônes FontAwesome',
            'col-md': 'Grille Bootstrap',
            'btn-primary': 'Boutons',
            'Compétitions récentes': 'Section compétitions',
            'Clubs récents': 'Section clubs',
        }
        
        print("\n✅ Indicateurs du template complet:")
        found_count = 0
        for key, desc in indicators.items():
            found = key in content
            if found:
                found_count += 1
            status = '✅' if found else '❌'
            print(f"   {status} {desc}")
        
        if found_count >= 5:
            print(f"\n✅ SUCCÈS: Template complet actif ({found_count}/{len(indicators)} indicateurs)")
        else:
            print(f"\n⚠️  Template simplifié encore actif ? ({found_count}/{len(indicators)} indicateurs)")
            
        # Rechercher des erreurs
        if 'NoReverseMatch' in content:
            print("\n❌ ERREUR: URLs manquantes")
            # Extraire l'erreur
            import re
            errors = re.findall(r"NoReverseMatch.*?'([^']+)'", content)
            for err in errors[:3]:
                print(f"   - URL manquante: {err}")
    else:
        print(f"❌ Erreur HTTP {resp.status_code}")
else:
    print("❌ Échec connexion")
PYEOF
REMOTE_TEST

echo ""
echo "================================================"
echo "✅ ACTIVATION TERMINÉE"
echo "================================================"

