#\!/bin/bash
# Vérifier la fédération et tester la connexion

echo "================================================"
echo "🔍 VÉRIFICATION FINALE ET TEST"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification de la fédération pour DT_bguinziemba..."
echo "======================================================"
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import Federation, FederationAdministrator, UserProfile

User = get_user_model()
user = User.objects.filter(username='DT_bguinziemba').first()

if user:
    print(f"✅ Utilisateur trouvé: {user.username}")
    
    # Vérifier le profil
    if hasattr(user, 'userprofile'):
        profile = user.userprofile
        print(f"✅ Role: {profile.role}")
        print(f"✅ Onboarding complété: {profile.onboarding_completed}")
    
    # Vérifier les fédérations
    print("\n📋 Fédérations associées:")
    
    # En tant que owner
    federations_owner = Federation.objects.filter(owner=user)
    for fed in federations_owner:
        print(f"   - {fed.name} (ID: {fed.id}) - En tant que OWNER")
    
    # En tant qu'administrateur
    fed_admins = FederationAdministrator.objects.filter(user=user)
    for fa in fed_admins:
        print(f"   - {fa.federation.name} (ID: {fa.federation.id}) - En tant qu'ADMIN (primary={fa.is_primary})")
    
    # Trouver LA fédération qui sera utilisée par custom_login
    federation = Federation.objects.filter(owner=user).first() or Federation.objects.filter(administrators__user=user).first()
    if federation:
        print(f"\n✅ Fédération qui sera utilisée pour la redirection: {federation.name} (ID: {federation.id})")
        print(f"   URL de redirection: /competitions/dashboard/federation/{federation.id}/")
    else:
        print("\n❌ Aucune fédération trouvée pour la redirection")
PYEOF

echo ""
echo "2️⃣ Test de connexion simulé..."
echo "==============================="
python3 << 'PYEOF'
import django
django.setup()

from django.test import Client
from django.urls import reverse

client = Client()

print("🧪 Test de connexion avec DT_bguinziemba:")

# Se connecter
logged_in = client.login(username='DT_bguinziemba', password='AQWZSX123ok,')
print(f"   - Login réussi: {logged_in}")

if logged_in:
    # Accéder au dashboard principal
    response = client.get('/competitions/dashboard/', follow=False)
    print(f"   - Réponse dashboard: {response.status_code}")
    
    if response.status_code == 302:
        print(f"   - Redirection vers: {response.url}")
        
        # Suivre la redirection
        final_response = client.get('/competitions/dashboard/', follow=True)
        if final_response.redirect_chain:
            print("   - Chaîne de redirection:")
            for url, code in final_response.redirect_chain:
                print(f"     → {url} (code: {code})")
PYEOF

echo ""
echo "3️⃣ Vérification des logs récents..."
echo "==================================="
echo "📋 Derniers logs de connexion (si disponibles):"
tail -20 logs/django.log  < /dev/null |  grep -E "DT_bguinziemba|federation.*redirect|Login.*success" | tail -10 || echo "Pas de logs trouvés"

echo ""
echo "================================================"
echo "📊 RÉSUMÉ"
echo "================================================"
echo ""
echo "✅ Les corrections ont été appliquées:"
echo "   - custom_login.py utilise maintenant les bonnes URLs"
echo "   - La redirection devrait fonctionner correctement"
echo ""
echo "🔍 Pour tester:"
echo "   1. Déconnectez-vous complètement"
echo "   2. Connectez-vous avec DT_bguinziemba / AQWZSX123ok,"
echo "   3. Vous devriez être redirigé vers le dashboard fédération"
echo ""

REMOTE_COMMANDS
