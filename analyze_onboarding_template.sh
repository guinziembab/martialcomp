#!/bin/bash
# Analyser le template d'onboarding

echo "================================================"
echo "🔍 ANALYSE DU TEMPLATE ONBOARDING CLUB"
echo "================================================"
echo ""

ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash' << 'EOF'

echo "1️⃣ Recherche du template..."
echo "=========================="
find . -name "*club*creation*.html" -type f 2>/dev/null | grep -v "__pycache__" | grep -v "static" | head -10

echo ""
echo "2️⃣ Vérification du template principal..."
echo "========================================"
TEMPLATE="apps/competitions/templates/competitions/onboarding/club_creation.html"
if [ -f "$TEMPLATE" ]; then
    echo "Template trouvé : $TEMPLATE"
    echo ""
    echo "Recherche du champ country:"
    grep -n -B2 -A2 "country" "$TEMPLATE" | head -20
    
    echo ""
    echo "Méthode de rendu du formulaire:"
    grep -n -E "(form\.|{{ form|crispy)" "$TEMPLATE" | head -10
else
    echo "Template non trouvé à cet emplacement"
fi

echo ""
echo "3️⃣ Vérification du formulaire dans la vue..."
echo "=========================================="
echo "Recherche de la vue club_creation:"
VIEW_FILE=$(grep -r "def club_creation" apps/competitions/views/ 2>/dev/null | cut -d: -f1 | head -1)
if [ -n "$VIEW_FILE" ]; then
    echo "Vue trouvée dans: $VIEW_FILE"
    grep -A20 "def club_creation" "$VIEW_FILE" | head -30
else
    echo "Vue club_creation non trouvée"
fi

echo ""
echo "4️⃣ Test direct du formulaire..."
echo "==============================="
python3 << 'PYTHON_TEST'
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.competitions.forms.onboarding import ClubCreationForm
from apps.competitions.choices import COUNTRY_CHOICES

print("Test du formulaire ClubCreationForm:")
print("====================================")

# Créer une instance du formulaire
form = ClubCreationForm()

# Vérifier les champs
print(f"Nombre de champs: {len(form.fields)}")
print(f"Liste des champs: {list(form.fields.keys())}")

# Vérifier spécifiquement le champ country
if 'country' in form.fields:
    field = form.fields['country']
    print(f"\nChamp 'country' trouvé:")
    print(f"  - Type: {type(field).__name__}")
    print(f"  - Widget: {type(field.widget).__name__}")
    print(f"  - Requis: {field.required}")
    print(f"  - Label: {field.label}")
    if hasattr(field, 'choices'):
        print(f"  - Nombre de choix: {len(field.choices)}")
else:
    print("\n❌ Champ 'country' NON TROUVÉ dans le formulaire!")

# Vérifier le rendu HTML
print("\nRendu HTML du champ country:")
if 'country' in form:
    print(form['country'])
else:
    print("❌ Impossible de rendre le champ country")

PYTHON_TEST

EOF

echo ""
echo "================================================"
echo "📊 RÉSUMÉ DE L'ANALYSE"
echo "================================================"