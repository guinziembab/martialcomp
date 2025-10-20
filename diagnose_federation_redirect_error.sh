#!/bin/bash
# Diagnostiquer l'erreur de redirection après création de fédération

echo "================================================"
echo "🔍 DIAGNOSTIC ERREUR REDIRECTION FÉDÉRATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Recherche de l'erreur dans les logs..."
echo "========================================"
echo "📋 Dernière erreur de création de fédération:"
tail -100 logs/django.log | grep -A10 -B5 "federation_detail\|FEDERATION CREATION\|NoReverseMatch" | tail -30

echo ""
echo "2️⃣ Vérification du code de redirection..."
echo "========================================="
echo "📋 Dans federations.py de onboarding:"
grep -A5 -B5 "redirect.*federation" apps/competitions/views/onboarding/federations.py | grep -A5 -B5 "162"

echo ""
echo "3️⃣ Vérification des URLs disponibles..."
echo "========================================"
echo "📋 URLs dans dashboard:"
grep -n "federation_detail\|federation-detail" apps/competitions/urls/dashboard.py

echo ""
echo "📋 URLs dans __init__.py:"
grep -n "dashboard" apps/competitions/urls/__init__.py

echo ""
echo "4️⃣ Test des URLs de redirection possibles..."
echo "==========================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

print("🧪 Test des URLs de dashboard fédération:")

# Liste des patterns possibles
url_patterns = [
    ('competitions:dashboard:federation_detail', {'federation_id': 1}),
    ('competitions:dashboard:federation', {'federation_id': 1}),
    ('competitions:federations:dashboard', {'federation_id': 1}),
    ('competitions:federation_dashboard', {'federation_id': 1}),
    ('dashboard:federation', {'federation_id': 1}),
    ('federation_dashboard', {'federation_id': 1}),
]

for pattern, kwargs in url_patterns:
    try:
        url = reverse(pattern, kwargs=kwargs)
        print(f"✅ {pattern} -> {url}")
    except NoReverseMatch:
        print(f"❌ {pattern} - Non trouvé")

print("\n🧪 Test des vues dashboard disponibles:")
try:
    from apps.competitions.views.dashboard.federations import federation_dashboard
    print("✅ Vue federation_dashboard importée")
except ImportError as e:
    print(f"❌ Erreur import: {e}")
PYEOF

echo ""
echo "5️⃣ Vérification de la structure des URLs..."
echo "=========================================="
echo "📋 Fichiers URLs dans competitions:"
find apps/competitions/urls -name "*.py" -type f | sort

echo ""
echo "6️⃣ Contenu du fichier dashboard.py..."
echo "====================================="
if [ -f "apps/competitions/urls/dashboard.py" ]; then
    echo "📋 Patterns dans dashboard.py:"
    grep -E "path.*federation|url.*federation" apps/competitions/urls/dashboard.py | head -10
else
    echo "❌ Fichier dashboard.py non trouvé"
fi

REMOTE_COMMANDS