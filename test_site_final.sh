#!/bin/bash
# Test final du site

echo "================================================"
echo "🧪 TEST FINAL DU SITE"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification des dernières erreurs..."
echo "========================================"
echo "📋 Logs Django (5 dernières lignes d'erreur):"
tail -50 logs/django.log | grep -A2 -B2 "ERROR\|500" | tail -10

echo ""
echo "2️⃣ Test de toutes les importations critiques..."
echo "==============================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

print("🧪 Test des imports critiques:")

# Test 1: Views federations
try:
    from apps.competitions.views.federations import federation_list, federation_detail
    print("✅ Import views.federations OK")
except Exception as e:
    print(f"❌ Erreur views.federations: {e}")

# Test 2: Utils
try:
    from apps.utils.decorators import federation_admin_required
    print("✅ Import utils.decorators OK")
except Exception as e:
    print(f"❌ Erreur utils.decorators: {e}")

# Test 3: Forms
try:
    from apps.competitions.forms.onboarding import FederationCreationForm
    print("✅ Import forms.onboarding OK")
except Exception as e:
    print(f"❌ Erreur forms.onboarding: {e}")

# Test 4: URLs
print("\n🧪 Test des URLs principales:")
from django.urls import reverse
urls_to_test = ['welcome', 'account_login', 'account_logout']

for url_name in urls_to_test:
    try:
        url = reverse(url_name)
        print(f"✅ {url_name}: {url}")
    except Exception as e:
        print(f"❌ {url_name}: {str(e)[:50]}...")

# Test 5: Page d'accueil
print("\n🧪 Test de la vue welcome:")
try:
    from apps.competitions.views import welcome
    print("✅ Import view welcome OK")
except Exception as e:
    print(f"❌ Erreur view welcome: {e}")

PYEOF

echo ""
echo "3️⃣ Test avec curl..."
echo "===================="
echo "Test de https://martialcomp.com/fr/ :"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://martialcomp.com/fr/ || echo "Erreur curl"

echo ""
echo "4️⃣ État des services..."
echo "======================="
systemctl is-active martialcomp && echo "✅ Service martialcomp: actif" || echo "❌ Service martialcomp: inactif"
systemctl is-active apache2 && echo "✅ Apache2: actif" || echo "❌ Apache2: inactif"

echo ""
echo "================================================"
echo "📊 RÉSUMÉ DU TEST"
echo "================================================"
echo ""
echo "✅ Actions réalisées:"
echo "  - federations.py transféré avec federation_list et federation_detail"
echo "  - Erreur de syntaxe dans onboarding.py corrigée"
echo "  - Modules utils créés"
echo "  - Services redémarrés"
echo ""
echo "🎯 Le site devrait maintenant être accessible sur:"
echo "   https://martialcomp.com/fr/"

REMOTE_COMMANDS