#\!/bin/bash
# Investiguer la nouvelle erreur 500

echo "================================================"
echo "🔍 INVESTIGATION NOUVELLE ERREUR 500"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification des logs d'erreur récents..."
echo "==========================================="
echo "📋 Dernières erreurs Django:"
tail -30 logs/django.log  < /dev/null |  grep -A10 "ERROR\|Exception" | tail -20

echo ""
echo "📋 Logs système récents:"
sudo journalctl -u martialcomp -n 30 | grep -A5 "ERROR\|500" | tail -15 || echo "Pas de logs système"

echo ""
echo "2️⃣ Vérification du template actuellement utilisé..."
echo "================================================="
echo "📋 Template dans la vue:"
grep "render.*federation.*\.html" apps/competitions/views/dashboard/federations.py | grep -B2 -A2 "def federation_dashboard" -A20 | grep "return render"

echo ""
echo "3️⃣ Test direct de la vue avec traceback..."
echo "========================================"
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

import traceback
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware

User = get_user_model()

try:
    # Importer la vue
    from apps.competitions.views.dashboard.federations import federation_dashboard
    
    # Créer une requête
    user = User.objects.get(username='DT_bguinziemba')
    factory = RequestFactory()
    request = factory.get('/competitions/dashboard/federation/41/')
    request.user = user
    
    # Ajouter session et messages
    session_middleware = SessionMiddleware(lambda r: None)
    session_middleware.process_request(request)
    request.session.save()
    
    messages_middleware = MessageMiddleware(lambda r: None)
    messages_middleware.process_request(request)
    
    # Appeler la vue
    print("🧪 Appel de federation_dashboard...")
    response = federation_dashboard(request, federation_id=41)
    
    if response:
        print(f"✅ Réponse reçue: {type(response)}")
        if hasattr(response, 'status_code'):
            print(f"   Status: {response.status_code}")
    else:
        print("❌ La vue retourne None\!")
        
except Exception as e:
    print(f"\n❌ ERREUR: {type(e).__name__}: {e}")
    print("\n📋 Traceback complet:")
    traceback.print_exc()
PYEOF

echo ""
echo "4️⃣ Vérification du contenu du template simple..."
echo "=============================================="
echo "📋 Premières lignes du template:"
head -30 apps/competitions/templates/competitions/dashboard/federation_simple.html | tail -20

echo ""
echo "================================================"
echo "📊 ANALYSE"
echo "================================================"

REMOTE_COMMANDS
