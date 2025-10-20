#!/bin/bash
# Vérifier l'erreur de validation du formulaire

echo "================================================"
echo "🔍 ANALYSE ERREUR VALIDATION FORMULAIRE"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Recherche de l'erreur complète dans _clean_fields..."
echo "======================================================"
tail -200 logs/django.log | grep -A30 "_clean_fields" | tail -40

echo ""
echo "2️⃣ Vérification du formulaire onboarding.py..."
echo "=============================================="
echo "📋 Ligne avec le pattern corrigé:"
grep -n "pattern" apps/competitions/forms/onboarding.py | grep -A2 -B2 "85"

echo ""
echo "3️⃣ Examen de la classe FederationCreationForm complète..."
echo "========================================================"
sed -n '/class FederationCreationForm/,/^class\|^def\|^$/p' apps/competitions/forms/onboarding.py | head -60

echo ""
echo "4️⃣ Test direct du formulaire..."
echo "==============================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from apps.competitions.forms.onboarding import FederationCreationForm
from apps.competitions.models import Discipline

print("🧪 Test de création du formulaire vide:")
try:
    form = FederationCreationForm()
    print(f"✅ Formulaire créé - {len(form.fields)} champs")
    
    # Lister les champs
    print("\n📋 Champs du formulaire:")
    for field_name, field in form.fields.items():
        print(f"  - {field_name}: {field.__class__.__name__}")
        if hasattr(field, 'queryset') and field_name == 'disciplines':
            print(f"    Disciplines disponibles: {field.queryset.count()}")
    
except Exception as e:
    print(f"❌ Erreur création formulaire: {e}")
    import traceback
    traceback.print_exc()

print("\n🧪 Test avec données POST simulées:")
data = {
    'name': 'Test Federation',
    'country': 'FR',
    'description': 'Test description',
    'contact_email': 'test@test.com',
    'contact_phone': '+33123456789',
    'address': '123 rue test',
    'city': 'Paris',
    'postal_code': '75001',
    'founding_date': '2025-01-01',
    'disciplines': []
}

try:
    form = FederationCreationForm(data=data)
    if form.is_valid():
        print("✅ Formulaire valide!")
    else:
        print("❌ Erreurs de validation:")
        for field, errors in form.errors.items():
            print(f"  - {field}: {errors}")
except Exception as e:
    print(f"❌ Erreur validation: {e}")
    import traceback
    traceback.print_exc()
PYEOF

echo ""
echo "5️⃣ Vérification de la vue handle_federation_creation..."
echo "====================================================="
echo "📋 Ligne 96 où l'erreur se produit:"
sed -n '90,100p' apps/competitions/views/onboarding/federations.py

REMOTE_COMMANDS