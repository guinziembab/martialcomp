#!/bin/bash
# Vérifier le rôle de l'utilisateur DT_bguinziemba

echo "================================================"
echo "🔍 VÉRIFICATION RÔLE UTILISATEUR"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Analyse simplifiée du profil..."
echo "==================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import UserProfile, Practitioner

User = get_user_model()

print("🔍 Utilisateur DT_bguinziemba:")
user = User.objects.filter(username='DT_bguinziemba').first()
if user:
    print(f"✅ Trouvé - ID: {user.id}")
    
    # UserProfile
    try:
        profile = user.userprofile
        print(f"\n📋 UserProfile:")
        print(f"   - Role actuel: '{profile.role}'")
        print(f"   - Onboarding complété: {profile.onboarding_completed}")
        
        # Si le rôle n'est pas federation_admin, le mettre à jour
        if profile.role != 'federation_admin':
            print(f"\n⚠️  L'utilisateur a le rôle '{profile.role}' au lieu de 'federation_admin'")
            print("   C'est pourquoi il est redirigé vers le dashboard Spectateur")
    except Exception as e:
        print(f"❌ Erreur UserProfile: {e}")
    
    # Vérifier les fédérations
    print(f"\n📋 Fédérations créées:")
    from apps.competitions.models import Federation
    federations = Federation.objects.filter(owner=user)
    if federations.exists():
        for f in federations:
            print(f"   - {f.name} (ID: {f.id})")
        print(f"\n✅ L'utilisateur a créé {federations.count()} fédération(s)")
    else:
        print("   ❌ Aucune fédération créée")
else:
    print("❌ Utilisateur non trouvé")
PYEOF

echo ""
echo "2️⃣ Vérification de la logique de redirection..."
echo "=============================================="
echo "📋 Vue dashboard dans base.py:"
grep -A20 "def dashboard" apps/competitions/views/dashboard/base.py | grep -A15 "role\|redirect" | head -20

echo ""
echo "3️⃣ Correction du rôle utilisateur..."
echo "===================================="
python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import UserProfile, Federation

User = get_user_model()

user = User.objects.filter(username='DT_bguinziemba').first()
if user:
    try:
        profile = user.userprofile
        
        # Vérifier si l'utilisateur a une fédération
        has_federation = Federation.objects.filter(owner=user).exists()
        
        if has_federation and profile.role != 'federation_admin':
            print(f"🔧 Mise à jour du rôle de '{profile.role}' vers 'federation_admin'")
            profile.role = 'federation_admin'
            profile.save()
            print("✅ Rôle mis à jour avec succès!")
            print("   L'utilisateur sera maintenant redirigé vers le dashboard Fédération")
        elif profile.role == 'federation_admin':
            print("✅ L'utilisateur a déjà le bon rôle 'federation_admin'")
        else:
            print(f"ℹ️  Rôle actuel: '{profile.role}', pas de fédération trouvée")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
PYEOF

echo ""
echo "4️⃣ Test de la redirection..."
echo "============================"
python3 << 'PYEOF'
import django
django.setup()

from django.urls import reverse

print("🧪 URLs de dashboard disponibles:")
dashboards = [
    'competitions:dashboard:dashboard',
    'competitions:dashboard:federations',
    'competitions:dashboard:spectator'
]

for db in dashboards:
    try:
        url = reverse(db)
        print(f"✅ {db} -> {url}")
    except:
        print(f"❌ {db} non trouvé")
PYEOF

echo ""
echo "================================================"
echo "✅ DIAGNOSTIC TERMINÉ"
echo "================================================"

REMOTE_COMMANDS