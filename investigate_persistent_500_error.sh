#\!/bin/bash
# Investiguer l'erreur 500 persistante

echo "================================================"
echo "🔍 INVESTIGATION ERREUR 500 PERSISTANTE"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Vérification des logs d'erreur récents..."
echo "==========================================="
echo "📋 Dernières erreurs Django (30 dernières lignes):"
tail -30 logs/django.log  < /dev/null |  grep -A10 -B5 "ERROR\|Exception\|500\|federation/41" || echo "Pas de logs django.log"

echo ""
echo "📋 Logs Gunicorn:"
sudo journalctl -u martialcomp -n 50 | grep -A5 -B5 "ERROR\|Exception\|500" | tail -30 || echo "Pas de logs gunicorn"

echo ""
echo "2️⃣ Test direct de la vue avec traceback complet..."
echo "================================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

import traceback
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware

User = get_user_model()

try:
    from apps.competitions.views.dashboard.federations import federation_dashboard
    from apps.competitions.models import Federation
    
    # Créer une requête complète
    user = User.objects.get(username='DT_bguinziemba')
    factory = RequestFactory()
    request = factory.get('/competitions/dashboard/federation/41/')
    request.user = user
    
    # Ajouter la session
    session_middleware = SessionMiddleware(lambda r: None)
    session_middleware.process_request(request)
    request.session.save()
    
    # Ajouter les messages
    messages_middleware = MessageMiddleware(lambda r: None)
    messages_middleware.process_request(request)
    
    # Vérifier que la fédération existe
    fed = Federation.objects.filter(id=41).first()
    if fed:
        print(f"✅ Fédération trouvée: {fed.name}")
    else:
        print("❌ Fédération ID 41 non trouvée\!")
    
    # Appeler la vue
    print("\n🧪 Appel de la vue federation_dashboard...")
    response = federation_dashboard(request, federation_id=41)
    
    if response:
        print(f"✅ Réponse reçue: {type(response)}")
        if hasattr(response, 'status_code'):
            print(f"   Status: {response.status_code}")
    else:
        print("❌ La vue retourne None\!")
        
except Exception as e:
    print(f"\n❌ ERREUR DÉTECTÉE: {type(e).__name__}: {e}")
    print("\n📋 Traceback complet:")
    traceback.print_exc()
PYEOF

echo ""
echo "3️⃣ Vérification du code actuel de federation_dashboard..."
echo "========================================================"
echo "📋 Début de la fonction (30 premières lignes):"
grep -n -A30 "def federation_dashboard" apps/competitions/views/dashboard/federations.py | head -40

echo ""
echo "4️⃣ Vérification des imports..."
echo "=============================="
echo "📋 Imports dans federations.py:"
head -30 apps/competitions/views/dashboard/federations.py | grep "^from\|^import"

echo ""
echo "================================================"
echo "📊 ANALYSE"
echo "================================================"

REMOTE_COMMANDS
