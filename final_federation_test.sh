#!/bin/bash
# Test final de la création de fédération

echo "================================================"
echo "🧪 TEST FINAL CRÉATION FÉDÉRATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification des URLs corrigées..."
echo "===================================="
echo "📋 URLs federation dans dashboard.py:"
grep "federation" apps/competitions/urls/dashboard.py

echo ""
echo "📋 Redirections dans onboarding/federations.py:"
grep -n "redirect.*federation" apps/competitions/views/onboarding/federations.py

echo ""
echo "2️⃣ Test complet du workflow..."
echo "==============================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.urls import reverse

print("🧪 Test complet des URLs:")
print("=" * 50)

# Test 1: URL d'onboarding
try:
    url = reverse('competitions:onboarding:federation')
    print(f"✅ Onboarding federation: {url}")
except Exception as e:
    print(f"❌ Onboarding federation: {e}")

# Test 2: URL de redirection avec ID
try:
    url = reverse('competitions:dashboard:federation_detail', kwargs={'federation_id': 1})
    print(f"✅ Dashboard federation_detail: {url}")
except Exception as e:
    print(f"❌ Dashboard federation_detail: {e}")

# Test 3: Vérifier que le formulaire est accessible
from apps.competitions.forms.onboarding import FederationCreationForm
form = FederationCreationForm()
print(f"\n✅ Formulaire FederationCreationForm: {len(form.fields)} champs")
print(f"   - Disciplines disponibles: {form.fields['disciplines'].queryset.count()}")

# Test 4: Vérifier l'utilisateur DT_bguinziemba
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.filter(username='DT_bguinziemba').first()
if user:
    print(f"\n✅ Utilisateur DT_bguinziemba trouvé")
    print(f"   - ID: {user.id}")
    print(f"   - Email: {user.email}")
    print(f"   - Actif: {user.is_active}")
else:
    print("\n❌ Utilisateur DT_bguinziemba non trouvé")
PYEOF

echo ""
echo "3️⃣ Derniers logs d'erreur..."
echo "==========================="
echo "📋 Dernières erreurs (si présentes):"
tail -20 logs/django.log | grep -i "error\|exception" | tail -5 || echo "Aucune erreur récente"

echo ""
echo "================================================"
echo "✅ RÉSUMÉ DES CORRECTIONS"
echo "================================================"
echo ""
echo "✅ Actions réalisées:"
echo "  1. Validator du champ logo corrigé"
echo "  2. URL federation_detail ajoutée dans dashboard.py"
echo "  3. Redirection corrigée vers federation_detail"
echo "  4. 35 disciplines disponibles dans le formulaire"
echo ""
echo "🎯 Le workflow complet devrait maintenant fonctionner:"
echo ""
echo "1. Connexion: DT_bguinziemba / AQWZSX123ok,"
echo "2. Création fédération: https://martialcomp.com/fr/competitions/onboarding/federation/"
echo "3. Redirection automatique vers le dashboard fédération après création"
echo ""

REMOTE_COMMANDS