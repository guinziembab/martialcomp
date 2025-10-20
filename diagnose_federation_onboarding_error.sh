#!/bin/bash
# Diagnostiquer l'erreur d'onboarding fédération

echo "================================================"
echo "🔍 DIAGNOSTIC ERREUR ONBOARDING FÉDÉRATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Recherche des erreurs récentes dans les logs..."
echo "=================================================="
echo "📋 Dernières erreurs Django (liées à onboarding/federation):"
tail -100 logs/django.log | grep -A10 -B5 "onboarding.*federation\|federation.*500\|DT_bguinziemba" | tail -30

echo ""
echo "📋 Erreurs Gunicorn récentes:"
tail -50 logs/gunicorn_error.log | grep -A10 -B5 "onboarding.*federation\|Traceback" | tail -20

echo ""
echo "2️⃣ Vérification de la vue onboarding federation..."
echo "================================================="
echo "📋 Fichier onboarding/federations.py existe?"
ls -la apps/competitions/views/onboarding/federations.py

echo ""
echo "📋 Import dans __init__.py:"
grep "federation" apps/competitions/views/onboarding/__init__.py

echo ""
echo "3️⃣ Vérification du formulaire FederationCreationForm..."
echo "======================================================"
echo "📋 Champs dans Meta.fields:"
grep -A5 "class Meta:" apps/competitions/forms/onboarding.py | grep -A3 "model = Federation"

echo ""
echo "4️⃣ Test des imports spécifiques..."
echo "==================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

print("🧪 Test des imports onboarding federation:")

try:
    from apps.competitions.views.onboarding.federations import handle_federation_creation
    print("✅ Import handle_federation_creation OK")
except Exception as e:
    print(f"❌ Erreur import handle_federation_creation: {e}")

try:
    from apps.competitions.forms.onboarding import FederationCreationForm
    form = FederationCreationForm()
    print(f"✅ FederationCreationForm OK - {len(form.fields)} champs")
    if 'disciplines' in form.fields:
        print("  ✅ Champ disciplines présent")
    else:
        print("  ❌ Champ disciplines manquant!")
except Exception as e:
    print(f"❌ Erreur FederationCreationForm: {e}")

# Vérifier les disciplines
try:
    from apps.competitions.models import Discipline
    count = Discipline.objects.filter(is_active=True).count()
    print(f"✅ {count} disciplines actives en base")
except Exception as e:
    print(f"❌ Erreur disciplines: {e}")

# Vérifier l'utilisateur
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.filter(username='DT_bguinziemba').first()
    if user:
        print(f"✅ Utilisateur DT_bguinziemba trouvé (ID: {user.id})")
    else:
        print("❌ Utilisateur DT_bguinziemba non trouvé")
except Exception as e:
    print(f"❌ Erreur recherche utilisateur: {e}")
PYEOF

echo ""
echo "5️⃣ Vérification des URLs..."
echo "=========================="
grep -n "onboarding.*federation" apps/competitions/urls/onboarding.py

echo ""
echo "6️⃣ Recherche de l'erreur spécifique..."
echo "====================================="
# Chercher les tracebacks complets
echo "📋 Dernière erreur complète:"
tail -200 logs/django.log | grep -A20 "Internal Server Error.*onboarding.*federation" | tail -25

REMOTE_COMMANDS