#!/bin/bash
# Tracer ce qui se passe réellement lors de la redirection

echo "================================================"
echo "🔍 TRACE COMPLÈTE DE LA REDIRECTION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Ajout de logs de debug dans base.py..."
echo "========================================"

# Backup
cp apps/competitions/views/dashboard/base.py apps/competitions/views/dashboard/base.py.backup_debug

# Ajouter des logs de debug
python3 << 'PYEOF'
import re

# Lire le fichier
with open("apps/competitions/views/dashboard/base.py", 'r') as f:
    content = f.read()

# Ajouter des logs avant chaque redirection
# Chercher la fonction dashboard
lines = content.split('\n')
new_lines = []
in_dashboard = False

for i, line in enumerate(lines):
    # Détecter le début de la fonction dashboard
    if 'def dashboard(request):' in line:
        in_dashboard = True
    
    # Ajouter des logs avant les redirections
    if in_dashboard and 'return redirect' in line:
        # Ajouter un log juste avant
        indent = len(line) - len(line.lstrip())
        log_line = ' ' * indent + f'logger.info(f"REDIRECT DEBUG: User {{request.user.username}} role={{profile.role}} -> {line.strip()}")\n'
        new_lines.append(log_line)
    
    new_lines.append(line)
    
    # Sortir de la fonction
    if in_dashboard and line.strip() and not line.startswith(' ') and not line.startswith('\t') and i > 10:
        in_dashboard = False

# Écrire le fichier modifié
with open("apps/competitions/views/dashboard/base.py", 'w') as f:
    f.write('\n'.join(new_lines))

print("✅ Logs de debug ajoutés")
PYEOF

echo ""
echo "2️⃣ Test direct de la vue dashboard..."
echo "====================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory, Client
from django.contrib.auth import login
from django.contrib.sessions.backends.db import SessionStore

User = get_user_model()

print("🧪 Test avec client Django:")
client = Client()

# Se connecter
logged_in = client.login(username='DT_bguinziemba', password='AQWZSX123ok,')
print(f"Login réussi: {logged_in}")

if logged_in:
    # Tester l'accès au dashboard
    response = client.get('/competitions/dashboard/', follow=False)
    print(f"\n📋 Réponse dashboard:")
    print(f"   - Status: {response.status_code}")
    if response.status_code == 302:
        print(f"   - Redirection vers: {response.url}")
    
    # Suivre toutes les redirections
    response = client.get('/competitions/dashboard/', follow=True)
    print(f"\n📋 Après redirections:")
    print(f"   - URL finale: {response.wsgi_request.path}")
    print(f"   - Status: {response.status_code}")
PYEOF

echo ""
echo "3️⃣ Vérification des sessions..."
echo "=============================="
python3 << 'PYEOF'
import django
django.setup()

from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

# Chercher les sessions récentes
recent = timezone.now() - timedelta(hours=1)
sessions = Session.objects.filter(expire_date__gt=timezone.now())

print(f"📋 Sessions actives: {sessions.count()}")

# Chercher celle de DT_bguinziemba
user = User.objects.get(username='DT_bguinziemba')
for session in sessions[:5]:
    data = session.get_decoded()
    if data.get('_auth_user_id') == str(user.id):
        print(f"\n✅ Session trouvée pour DT_bguinziemba:")
        print(f"   - Session key: {session.session_key[:10]}...")
        print(f"   - Expire: {session.expire_date}")
PYEOF

echo ""
echo "4️⃣ Vérification dans les logs Django..."
echo "======================================"
echo "📋 Derniers logs de redirection:"
tail -30 logs/django.log | grep -E "REDIRECT DEBUG|dashboard.*DT_bguinziemba|spectator.*redirect" || echo "Pas de logs de debug trouvés"

echo ""
echo "5️⃣ Redémarrage pour appliquer les logs..."
echo "========================================"
sudo systemctl restart martialcomp
echo "✅ Service redémarré"

echo ""
echo "================================================"
echo "🔍 INSTRUCTIONS DE TEST"
echo "================================================"
echo ""
echo "1. Déconnectez-vous complètement"
echo "2. Reconnectez-vous avec DT_bguinziemba / AQWZSX123ok,"
echo "3. Notez l'URL où vous êtes redirigé"
echo ""
echo "Puis exécutez:"
echo "tail -50 /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log | grep 'REDIRECT DEBUG'"
echo ""

REMOTE_COMMANDS