#!/bin/bash
# Script de diagnostic ciblé sur le problème des cases à cocher disciplines

echo "================================================"
echo "🔍 DIAGNOSTIC PROBLÈME DISCIPLINES FÉDÉRATION"
echo "================================================"
echo ""
echo "Date: $(date)"
echo ""

PROJECT_DIR="/home/martialc/martialcomp"
cd "$PROJECT_DIR"

# 1. Vérifier les disciplines en base
echo "1️⃣ VÉRIFICATION DES DISCIPLINES EN BASE"
echo "========================================="
python manage.py shell << 'EOF'
from apps.competitions.models import Discipline

# Compter les disciplines
total = Discipline.objects.count()
active = Discipline.objects.filter(is_active=True).count()

print(f"Total disciplines: {total}")
print(f"Disciplines actives: {active}")
print("\nPremières disciplines actives:")
for d in Discipline.objects.filter(is_active=True)[:10]:
    print(f"  ID {d.id}: {d.name}")
EOF

echo ""

# 2. Vérifier le formulaire FederationCreationForm
echo "2️⃣ ANALYSE DU FORMULAIRE FederationCreationForm"
echo "================================================"
python manage.py shell << 'EOF'
from apps.competitions.forms.onboarding import FederationCreationForm
import inspect

# Analyser le formulaire
form = FederationCreationForm()

print("Champs du formulaire:")
for field_name, field in form.fields.items():
    widget_class = field.widget.__class__.__name__
    print(f"  - {field_name}: {field.__class__.__name__} (Widget: {widget_class})")

# Vérifier spécifiquement le champ disciplines
if 'disciplines' in form.fields:
    field = form.fields['disciplines']
    print(f"\nDétails du champ 'disciplines':")
    print(f"  - Type: {field.__class__.__name__}")
    print(f"  - Widget: {field.widget.__class__.__name__}")
    print(f"  - Required: {field.required}")
    print(f"  - Queryset count: {field.queryset.count() if hasattr(field, 'queryset') else 'N/A'}")
    
    # Vérifier les attributs du widget
    if hasattr(field.widget, 'attrs'):
        print(f"  - Widget attrs: {field.widget.attrs}")
else:
    print("\n❌ ERREUR: Le champ 'disciplines' n'existe pas dans le formulaire!")
EOF

echo ""

# 3. Vérifier le template de création fédération
echo "3️⃣ ANALYSE DU TEMPLATE federation_creation.html"
echo "==============================================="
TEMPLATE="apps/competitions/templates/competitions/onboarding/federation_creation.html"

if [ -f "$TEMPLATE" ]; then
    echo "✅ Template trouvé"
    
    # Chercher comment les disciplines sont rendues
    echo -e "\n📋 Recherche du rendu des disciplines:"
    grep -n -A 5 -B 5 "discipline" "$TEMPLATE" | head -30 || echo "Aucune mention de 'discipline' trouvée"
    
    echo -e "\n📋 Recherche de {{ form.disciplines }}:"
    grep -n "{{ form.disciplines }}" "$TEMPLATE" && echo "✅ {{ form.disciplines }} trouvé" || echo "❌ {{ form.disciplines }} NON trouvé"
    
    echo -e "\n📋 Recherche de boucles for sur disciplines:"
    grep -n -A 3 "for.*discipline" "$TEMPLATE" || echo "Aucune boucle for sur disciplines"
else
    echo "❌ Template introuvable: $TEMPLATE"
fi

echo ""

# 4. Vérifier la vue handle_federation_creation
echo "4️⃣ ANALYSE DE LA VUE handle_federation_creation"
echo "==============================================="
VIEW_FILE="apps/competitions/views/onboarding/federations.py"

if [ -f "$VIEW_FILE" ]; then
    echo "✅ Vue trouvée"
    
    # Chercher la gestion des disciplines
    echo -e "\n📋 Recherche de la gestion des disciplines dans POST:"
    grep -n -A 10 "disciplines.*=" "$VIEW_FILE" | head -20 || echo "Aucune assignation de disciplines trouvée"
    
    # Chercher form.save
    echo -e "\n📋 Recherche de form.save():"
    grep -n -B 5 -A 5 "form\.save" "$VIEW_FILE" | head -20
else
    echo "❌ Vue introuvable: $VIEW_FILE"
fi

echo ""

# 5. Test de création d'un formulaire avec données
echo "5️⃣ TEST DE VALIDATION DU FORMULAIRE"
echo "==================================="
python manage.py shell << 'EOF'
from apps.competitions.forms.onboarding import FederationCreationForm
from apps.competitions.models import Discipline

# Créer des données de test
disciplines = Discipline.objects.filter(is_active=True)[:3]
data = {
    'name': 'Test Federation',
    'country': 'FR',
    'contact_email': 'test@test.com',
    'contact_phone': '0123456789',
    'description': 'Test',
}

# Ajouter les disciplines si possible
if disciplines.exists():
    data['disciplines'] = [d.id for d in disciplines]
    print(f"Disciplines ajoutées aux données: {data['disciplines']}")
else:
    print("⚠️ Aucune discipline active trouvée")

# Créer et valider le formulaire
form = FederationCreationForm(data=data)
print(f"\nFormulaire valide: {form.is_valid()}")

if not form.is_valid():
    print("Erreurs de validation:")
    for field, errors in form.errors.items():
        print(f"  - {field}: {errors}")
else:
    print("✅ Formulaire valide avec les données de test")
    print("Données nettoyées:")
    for k, v in form.cleaned_data.items():
        if k == 'disciplines':
            print(f"  - {k}: {[d.name for d in v] if v else 'Aucune'}")
        else:
            print(f"  - {k}: {v}")
EOF

echo ""

# 6. Vérifier les logs récents
echo "6️⃣ LOGS RÉCENTS (erreurs federation)"
echo "====================================="
LOG_LOCATIONS=(
    "/var/log/django/martialcomp.log"
    "/var/log/apache2/error.log"
    "/home/martialc/logs/django.log"
    "/var/log/martialcomp/django.log"
)

for log in "${LOG_LOCATIONS[@]}"; do
    if [ -f "$log" ]; then
        echo "📄 Analyse de $log:"
        tail -100 "$log" | grep -i "federation\|discipline" | tail -10 || echo "  Aucune erreur récente trouvée"
        break
    fi
done

echo ""

# 7. Vérifier les permissions du répertoire media
echo "7️⃣ PERMISSIONS DU RÉPERTOIRE MEDIA"
echo "=================================="
MEDIA_DIR="media/federation_logos"
if [ -d "$MEDIA_DIR" ]; then
    ls -la "$MEDIA_DIR" | head -5
    echo "✅ Répertoire media existe"
else
    echo "❌ Répertoire $MEDIA_DIR n'existe pas"
fi

echo ""

# 8. Résumé et recommandations
echo "8️⃣ RÉSUMÉ DU DIAGNOSTIC"
echo "======================"
echo ""
echo "Points à vérifier manuellement:"
echo "1. Le widget du champ disciplines (doit être CheckboxSelectMultiple)"
echo "2. Le template utilise bien {{ form.disciplines }}"
echo "3. La vue gère correctement les disciplines dans le POST"
echo "4. Les disciplines sont bien sauvegardées avec form.save(commit=False)"
echo ""
echo "================================================"
echo "✅ DIAGNOSTIC TERMINÉ"
echo "================================================"