#!/bin/bash
# Diagnostiquer le profil et les rôles de DT_bguinziemba

echo "================================================"
echo "🔍 DIAGNOSTIC PROFIL UTILISATEUR DT_bguinziemba"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Analyse du profil utilisateur..."
echo "===================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import UserProfile, Practitioner
from apps.organizations.models import OrganizationMember, Federation, FederationAdministrator

User = get_user_model()

print("🔍 Recherche de l'utilisateur DT_bguinziemba:")
print("=" * 50)

user = User.objects.filter(username='DT_bguinziemba').first()
if user:
    print(f"✅ Utilisateur trouvé:")
    print(f"   - ID: {user.id}")
    print(f"   - Username: {user.username}")
    print(f"   - Email: {user.email}")
    print(f"   - Actif: {user.is_active}")
    print(f"   - Staff: {user.is_staff}")
    print(f"   - Superuser: {user.is_superuser}")
    
    # Vérifier UserProfile
    print("\n📋 UserProfile:")
    try:
        profile = user.userprofile
        print(f"   - Role: {profile.role}")
        print(f"   - Onboarding complété: {profile.onboarding_completed}")
        print(f"   - Organization ID: {profile.organization_id}")
        print(f"   - Practitioner ID: {profile.practitioner_id}")
    except:
        print("   ❌ Pas de UserProfile")
    
    # Vérifier Practitioner
    print("\n📋 Practitioner:")
    practitioner = Practitioner.objects.filter(user=user).first()
    if practitioner:
        print(f"   - ID: {practitioner.id}")
        print(f"   - Nom: {practitioner.first_name} {practitioner.last_name}")
    else:
        print("   ❌ Pas de Practitioner")
    
    # Vérifier OrganizationMember
    print("\n📋 OrganizationMember:")
    memberships = OrganizationMember.objects.filter(user=user)
    if memberships.exists():
        for m in memberships:
            print(f"   - Organization: {m.organization.name} (Type: {m.organization.organization_type})")
            print(f"     Role: {m.role.name if m.role else 'Aucun'}")
    else:
        print("   ❌ Aucune appartenance à une organisation")
    
    # Vérifier FederationAdministrator
    print("\n📋 FederationAdministrator:")
    fed_admins = FederationAdministrator.objects.filter(user=user)
    if fed_admins.exists():
        for fa in fed_admins:
            print(f"   - Federation: {fa.federation.name}")
            print(f"     Role: {fa.role}")
            print(f"     Primary: {fa.is_primary}")
    else:
        print("   ❌ Pas administrateur de fédération")
    
    # Vérifier les fédérations créées
    print("\n📋 Fédérations créées (owner):")
    federations = Federation.objects.filter(owner=user)
    if federations.exists():
        for f in federations:
            print(f"   - {f.name} (ID: {f.id})")
    else:
        print("   ❌ Aucune fédération créée")
        
else:
    print("❌ Utilisateur DT_bguinziemba non trouvé")
PYEOF

echo ""
echo "2️⃣ Vérification de la logique de redirection..."
echo "=============================================="
echo "📋 Dans base.py (middleware ou redirection):"
grep -n "dashboard.*redirect\|role.*spectator" apps/competitions/views/dashboard/base.py | head -10

echo ""
echo "📋 Dans le middleware OnboardingRedirect:"
grep -A10 -B5 "spectator\|dashboard" apps/competitions/middleware/__init__.py 2>/dev/null | head -20

echo ""
echo "3️⃣ Vérification des rôles disponibles..."
echo "========================================"
python3 << 'PYEOF'
import django
django.setup()

from apps.competitions.models import UserProfile

print("📋 Choix de rôles disponibles dans UserProfile:")
if hasattr(UserProfile, 'ROLE_CHOICES'):
    for choice in UserProfile.ROLE_CHOICES:
        print(f"   - {choice[0]}: {choice[1]}")
else:
    print("   ❌ ROLE_CHOICES non défini")

# Vérifier les champs du modèle
print("\n📋 Champs du modèle UserProfile:")
for field in UserProfile._meta.get_fields():
    if field.name == 'role':
        print(f"   - Type: {field.get_internal_type()}")
        if hasattr(field, 'choices') and field.choices:
            print("   - Choix disponibles:")
            for c in field.choices:
                print(f"     * {c[0]}: {c[1]}")
PYEOF

echo ""
echo "4️⃣ Logs récents de connexion..."
echo "==============================="
echo "📋 Dernières connexions de DT_bguinziemba:"
tail -100 logs/django.log | grep -i "DT_bguinziemba\|login.*success" | tail -10

REMOTE_COMMANDS