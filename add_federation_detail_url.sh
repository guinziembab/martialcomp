#!/bin/bash
# Ajouter l'URL federation_detail manquante

echo "================================================"
echo "🔧 AJOUT URL FEDERATION_DETAIL"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification du fichier dashboard.py..."
echo "========================================"
echo "📋 Contenu actuel:"
cat apps/competitions/urls/dashboard.py | head -30

echo ""
echo "2️⃣ Ajout de l'URL federation_detail..."
echo "======================================"

# Backup
cp apps/competitions/urls/dashboard.py apps/competitions/urls/dashboard.py.backup_federation_detail

# Ajouter l'URL manquante
python3 << 'PYEOF'
# Lire le fichier
with open("apps/competitions/urls/dashboard.py", 'r') as f:
    lines = f.readlines()

# Chercher où insérer la nouvelle URL (après la ligne federations)
new_lines = []
added = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Si on trouve la ligne avec federations et qu'on n'a pas encore ajouté
    if "path('federations/'," in line and "name='federations'" in line and not added:
        # Ajouter la nouvelle URL juste après
        indent = "    "  # 4 espaces d'indentation
        new_lines.append(f"{indent}path('federation/<int:federation_id>/', federations.federation_dashboard, name='federation_detail'),\n")
        added = True
        print(f"✅ URL ajoutée après la ligne {i+1}")

# Écrire le fichier modifié
with open("apps/competitions/urls/dashboard.py", 'w') as f:
    f.writelines(new_lines)

if added:
    print("✅ URL federation_detail ajoutée avec succès")
else:
    print("❌ Impossible de trouver où ajouter l'URL")
PYEOF

echo ""
echo "3️⃣ Vérification de l'ajout..."
echo "============================="
echo "📋 Nouvelles URLs federation:"
grep -E "path.*federation" apps/competitions/urls/dashboard.py

echo ""
echo "4️⃣ Test de l'URL..."
echo "==================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.urls import reverse

print("🧪 Test des URLs federation:")
try:
    # Test de l'URL federations (sans ID)
    url1 = reverse('competitions:dashboard:federations')
    print(f"✅ URL federations: {url1}")
except Exception as e:
    print(f"❌ URL federations: {e}")

try:
    # Test de l'URL federation_detail (avec ID)
    url2 = reverse('competitions:dashboard:federation_detail', kwargs={'federation_id': 1})
    print(f"✅ URL federation_detail: {url2}")
except Exception as e:
    print(f"❌ URL federation_detail: {e}")
PYEOF

echo ""
echo "5️⃣ Redémarrage des services..."
echo "=============================="
sudo systemctl restart martialcomp
sudo systemctl reload apache2

echo ""
echo "================================================"
echo "✅ URL AJOUTÉE"
echo "================================================"
echo ""
echo "L'URL 'federation_detail' a été ajoutée dans dashboard.py"
echo "La redirection après création de fédération devrait maintenant fonctionner."
echo ""
echo "🎯 Testez la création de fédération:"
echo "   https://martialcomp.com/fr/competitions/onboarding/federation/"
echo "   Compte: DT_bguinziemba / AQWZSX123ok,"

REMOTE_COMMANDS