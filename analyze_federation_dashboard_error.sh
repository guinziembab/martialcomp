#\!/bin/bash
# Analyser l'erreur 500 sur le dashboard fédération

echo "================================================"
echo "🔍 ANALYSE ERREUR 500 - DASHBOARD FÉDÉRATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification des logs d'erreur..."
echo "===================================="
echo "📋 Dernières erreurs Django:"
tail -50 logs/django.log  < /dev/null |  grep -A5 -B5 "ERROR\|Exception\|federation/41" | tail -30

echo ""
echo "📋 Logs Apache récents:"
sudo tail -20 /var/log/apache2/martialcomp.com-error_log | grep -v "SIGTERM\|favicon"

echo ""
echo "2️⃣ Vérification de la vue federation_dashboard..."
echo "==============================================="
echo "📋 Recherche de la fonction:"
grep -n "def federation_dashboard" apps/competitions/views/dashboard/federations.py | head -5

echo ""
echo "3️⃣ Test direct de la vue..."
echo "==========================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from apps.competitions.models import Federation

User = get_user_model()

try:
    # Importer la vue
    from apps.competitions.views.dashboard.federations import federation_dashboard
    print("✅ Vue federation_dashboard importée avec succès")
    
    # Vérifier si la fédération 41 existe
    fed = Federation.objects.filter(id=41).first()
    if fed:
        print(f"✅ Fédération trouvée: {fed.name} (ID: {fed.id})")
    else:
        print("❌ Fédération ID 41 non trouvée\!")
        
    # Simuler une requête
    user = User.objects.get(username='DT_bguinziemba')
    factory = RequestFactory()
    request = factory.get('/competitions/dashboard/federation/41/')
    request.user = user
    
    # Essayer d'appeler la vue
    try:
        response = federation_dashboard(request, federation_id=41)
        print(f"✅ Vue appelée avec succès, status: {response.status_code if hasattr(response, 'status_code') else 'OK'}")
    except Exception as e:
        print(f"❌ Erreur lors de l'appel de la vue: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
PYEOF

echo ""
echo "4️⃣ Vérification du template utilisé..."
echo "======================================"
echo "📋 Templates federation dans dashboard:"
find apps/competitions/templates/competitions/dashboard/ -name "*federation*" -type f 2>/dev/null | head -10

echo ""
echo "5️⃣ Vérification des permissions..."
echo "================================="
python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import FederationAdministrator, Federation

User = get_user_model()
user = User.objects.get(username='DT_bguinziemba')
fed = Federation.objects.filter(id=41).first()

if fed:
    print(f"🔍 Permissions pour {user.username} sur {fed.name}:")
    
    # Vérifier si owner
    if fed.owner == user:
        print("   ✅ Est propriétaire (owner)")
    
    # Vérifier si admin
    fa = FederationAdministrator.objects.filter(user=user, federation=fed).first()
    if fa:
        print(f"   ✅ Est administrateur (role: {fa.role}, primary: {fa.is_primary})")
    
    # Vérifier les permissions
    from apps.competitions.views.dashboard import federations
    if hasattr(federations, 'has_federation_access'):
        has_access = federations.has_federation_access(user, fed)
        print(f"   ✅ has_federation_access: {has_access}")
PYEOF

echo ""
echo "================================================"
echo "📊 RÉSUMÉ DES PROBLÈMES POTENTIELS"
echo "================================================"

REMOTE_COMMANDS
