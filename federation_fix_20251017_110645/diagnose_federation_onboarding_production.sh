#!/bin/bash
# Script de diagnostic pour l'onboarding fédération en production

echo "=========================================="
echo "🔍 DIAGNOSTIC ONBOARDING FÉDÉRATION"
echo "=========================================="
echo ""

PROJECT_DIR="/home/martialc/martialcomp"
cd "$PROJECT_DIR"

# 1. Vérifier la structure de la base de données
echo "1️⃣ Vérification base de données..."
python manage.py shell << 'EOF'
from django.db import connection
from apps.competitions.models import Discipline, Federation

# Vérifier les disciplines
disciplines_count = Discipline.objects.filter(is_active=True).count()
print(f"  ✓ Disciplines actives: {disciplines_count}")

# Vérifier la structure de la table
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_name = 'competitions_federation_disciplines'
    """)
    table_exists = cursor.fetchone()[0]
    print(f"  ✓ Table competitions_federation_disciplines existe: {'✅' if table_exists else '❌'}")

# Lister quelques disciplines
print("\n  Disciplines disponibles:")
for d in Discipline.objects.filter(is_active=True)[:5]:
    print(f"    - {d.id}: {d.name}")
EOF

echo ""

# 2. Vérifier le formulaire
echo "2️⃣ Vérification formulaire..."
python manage.py shell << 'EOF'
from apps.competitions.forms.competitions import FederationCreationForm
import inspect

# Créer une instance du formulaire
form = FederationCreationForm()

# Vérifier les champs
print(f"  ✓ Champs du formulaire: {list(form.fields.keys())}")

# Vérifier spécifiquement le champ disciplines
if 'disciplines' in form.fields:
    field = form.fields['disciplines']
    print(f"  ✓ Champ 'disciplines' présent")
    print(f"  ✓ Widget: {field.widget.__class__.__name__}")
    print(f"  ✓ Required: {field.required}")
else:
    print("  ❌ Champ 'disciplines' MANQUANT!")
EOF

echo ""

# 3. Vérifier le template
echo "3️⃣ Vérification template..."
TEMPLATE="apps/competitions/templates/competitions/onboarding/federation_creation.html"

if [ -f "$TEMPLATE" ]; then
    echo "  ✓ Template existe"
    
    # Vérifier comment les disciplines sont rendues
    if grep -q "{{ form.disciplines }}" "$TEMPLATE"; then
        echo "  ✅ Template utilise {{ form.disciplines }}"
    else
        echo "  ⚠️  Template ne utilise pas {{ form.disciplines }}"
        
        # Vérifier si une boucle manuelle est utilisée
        if grep -q "for discipline in disciplines" "$TEMPLATE"; then
            echo "  ⚠️  Template génère manuellement les checkboxes"
        fi
    fi
else
    echo "  ❌ Template introuvable!"
fi

echo ""

# 4. Vérifier la vue
echo "4️⃣ Vérification vue..."
VIEW_FILE="apps/competitions/views/onboarding/emergency_views.py"

if [ -f "$VIEW_FILE" ]; then
    echo "  ✓ Vue d'urgence existe"
    
    # Vérifier la logique de soumission
    if grep -q "safe_federation_creation" "$VIEW_FILE"; then
        echo "  ✅ safe_federation_creation trouvée"
    fi
else
    echo "  ❌ Vue d'urgence introuvable!"
fi

echo ""

# 5. Test de création manuelle
echo "5️⃣ Test création fédération..."
python manage.py shell << 'EOF'
from apps.competitions.models import Federation, Discipline, Organization
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.filter(is_staff=True).first()

if user:
    try:
        # Créer une organisation
        org = Organization.objects.create(
            name='Test Diag Federation',
            type='federation',
            created_by=user
        )
        
        # Créer une fédération
        federation = Federation.objects.create(
            name='Test Diagnostic Federation',
            country='FR',
            description='Test',
            organization=org,
            created_by=user
        )
        
        # Ajouter des disciplines
        disciplines = Discipline.objects.filter(is_active=True)[:3]
        for disc in disciplines:
            federation.disciplines.add(disc)
        
        print(f"  ✅ Fédération créée: ID={federation.id}")
        print(f"  ✅ Disciplines associées: {federation.disciplines.count()}")
        
        # Nettoyer
        federation.delete()
        org.delete()
        print("  ✅ Test réussi - Nettoyage effectué")
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
else:
    print("  ❌ Aucun utilisateur admin trouvé")
EOF

echo ""

# 6. Vérifier les URLs
echo "6️⃣ Vérification URLs..."
URL_FILE="apps/competitions/urls/onboarding.py"

if grep -q "safe_federation_creation" "$URL_FILE" 2>/dev/null; then
    echo "  ✅ URL safe_federation_creation active"
elif grep -q "handle_federation_creation" "$URL_FILE" 2>/dev/null; then
    echo "  ⚠️  URL utilise l'ancienne vue handle_federation_creation"
else
    echo "  ❌ Aucune URL federation trouvée"
fi

echo ""

# 7. Vérifier les logs récents
echo "7️⃣ Erreurs récentes dans les logs..."
LOG_FILE="/var/log/django/martialcomp.log"

if [ -f "$LOG_FILE" ]; then
    tail -50 "$LOG_FILE" | grep -i "federation\|discipline" | tail -10 || echo "  ✓ Aucune erreur récente"
else
    # Essayer un autre emplacement
    if [ -f "/home/martialc/logs/django.log" ]; then
        tail -50 "/home/martialc/logs/django.log" | grep -i "federation\|discipline" | tail -10 || echo "  ✓ Aucune erreur récente"
    else
        echo "  ⚠️  Fichier de log introuvable"
    fi
fi

echo ""

# 8. Vérifier le middleware
echo "8️⃣ Vérification middleware..."
MIDDLEWARE_FILE="apps/competitions/middleware/__init__.py"

if [ -f "$MIDDLEWARE_FILE" ]; then
    if grep -q "OnboardingRedirectMiddleware" "$MIDDLEWARE_FILE"; then
        echo "  ✓ OnboardingRedirectMiddleware trouvé"
        echo "  ⚠️  ATTENTION: Ce middleware peut causer des boucles de redirection!"
    fi
else
    echo "  ✓ Pas de middleware d'onboarding (OK)"
fi

echo ""
echo "=========================================="
echo "✅ DIAGNOSTIC TERMINÉ"
echo "=========================================="
echo ""
echo "📝 Recommandations basées sur le diagnostic:"
echo "- Vérifier si le formulaire inclut correctement le champ disciplines"
echo "- S'assurer que le template rend {{ form.disciplines }}"
echo "- Désactiver temporairement OnboardingRedirectMiddleware si présent"
echo "- Vérifier les logs pour des erreurs spécifiques"
echo ""