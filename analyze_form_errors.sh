#!/bin/bash
# Analyser les erreurs de formulaire et le problème de redirection

echo "================================================"
echo "🔍 ANALYSE PROBLÈME CONNEXION ET FORMULAIRES"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification du template de login..."
echo "======================================"
echo "📋 Template login:"
if [ -f "apps/competitions/templates/account/login.html" ]; then
    echo "Fichier trouvé, recherche des champs de formulaire:"
    grep -n "input\|form\|id=\|name=" apps/competitions/templates/account/login.html | head -20
else
    echo "Template personnalisé non trouvé, utilisation du template par défaut"
fi

echo ""
echo "2️⃣ Test de connexion avec DT_bguinziemba..."
echo "=========================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.test import RequestFactory
from apps.competitions.views.dashboard.base import dashboard

User = get_user_model()

print("🔍 Test de connexion et redirection:")
user = User.objects.filter(username='DT_bguinziemba').first()

if user:
    print(f"✅ Utilisateur trouvé: {user.username}")
    
    # Simuler l'authentification
    auth_user = authenticate(username='DT_bguinziemba', password='AQWZSX123ok,')
    if auth_user:
        print("✅ Authentification réussie")
    else:
        print("❌ Échec de l'authentification - vérifier le mot de passe")
    
    # Tester la logique de redirection
    print("\n📋 Test de la logique dashboard:")
    
    # Créer une requête simulée
    factory = RequestFactory()
    request = factory.get('/competitions/dashboard/')
    request.user = user
    
    try:
        # Appeler directement la vue dashboard pour voir la redirection
        response = dashboard(request)
        if hasattr(response, 'url'):
            print(f"✅ Redirection vers: {response.url}")
        else:
            print(f"❌ Pas de redirection, response: {type(response)}")
    except Exception as e:
        print(f"❌ Erreur dans dashboard: {e}")
        import traceback
        traceback.print_exc()
PYEOF

echo ""
echo "3️⃣ Vérification du middleware OnboardingRedirect..."
echo "=================================================="
echo "📋 Middleware qui pourrait interférer:"
grep -A10 -B5 "class OnboardingRedirectMiddleware" apps/competitions/middleware/__init__.py 2>/dev/null | head -20

echo ""
echo "4️⃣ Logs de connexion récents..."
echo "==============================="
echo "📋 Dernières tentatives de connexion:"
tail -50 logs/django.log | grep -i "login\|dashboard\|redirect.*DT_bguinziemba\|spectator" | tail -15

echo ""
echo "5️⃣ Vérification directe de la page dashboard..."
echo "=============================================="
python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import UserProfile, FederationAdministrator

User = get_user_model()
user = User.objects.filter(username='DT_bguinziemba').first()

if user and hasattr(user, 'userprofile'):
    profile = user.userprofile
    print(f"📋 Profil utilisateur:")
    print(f"   - Role: {profile.role}")
    print(f"   - Onboarding: {profile.onboarding_completed}")
    
    # Vérifier le chemin de redirection attendu
    if profile.role == 'federation_admin':
        fed_admins = FederationAdministrator.objects.filter(user=user, is_primary=True)
        if fed_admins.exists():
            fed = fed_admins.first().federation
            print(f"\n✅ Devrait aller vers: /competitions/dashboard/federation/{fed.id}/")
        else:
            print("\n❌ Pas de FederationAdministrator principal trouvé")
    else:
        print(f"\n⚠️ Role incorrect: {profile.role}")
PYEOF

REMOTE_COMMANDS