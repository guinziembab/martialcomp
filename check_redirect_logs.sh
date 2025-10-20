#!/bin/bash
# Vérifier les logs de redirection après redémarrage

echo "================================================"
echo "🔍 VÉRIFICATION LOGS DE REDIRECTION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Derniers logs Django avec REDIRECT DEBUG..."
echo "============================================="
tail -100 logs/django.log | grep -E "REDIRECT DEBUG|DT_bguinziemba.*dashboard|federation.*redirect" | tail -20

echo ""
echo "2️⃣ Vérification de l'URL exacte du dashboard..."
echo "=============================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.competitions.models import UserProfile

User = get_user_model()

print("🧪 URLs de dashboard disponibles:")
urls = [
    ('competitions:dashboard:dashboard', {}),
    ('competitions:dashboard:spectator', {}), 
    ('competitions:dashboard:federation_detail', {'federation_id': 41}),
]

for name, kwargs in urls:
    try:
        url = reverse(name, kwargs=kwargs)
        print(f"✅ {name} -> {url}")
    except:
        print(f"❌ {name} non trouvé")

# Vérifier s'il y a un autre chemin de redirection
print("\n📋 Vérification du profil DT_bguinziemba:")
user = User.objects.filter(username='DT_bguinziemba').first()
if user and hasattr(user, 'userprofile'):
    profile = user.userprofile
    print(f"   - Role dans DB: '{profile.role}' (type: {type(profile.role)})")
    print(f"   - Est exactement 'federation_admin': {profile.role == 'federation_admin'}")
    
    # Vérifier caractère par caractère
    if profile.role != 'federation_admin':
        print(f"   - Comparaison caractère par caractère:")
        for i, (c1, c2) in enumerate(zip(profile.role, 'federation_admin')):
            if c1 != c2:
                print(f"     Position {i}: '{c1}' != '{c2}'")
PYEOF

echo ""
echo "3️⃣ Retirer les logs de debug et corriger le else final..."
echo "========================================================"

# Retirer les logs de debug et s'assurer que federation_admin est bien géré
python3 << 'PYEOF'
# Restaurer le fichier original
import shutil
try:
    shutil.copy('apps/competitions/views/dashboard/base.py.backup_debug', 
                'apps/competitions/views/dashboard/base.py')
    print("✅ Fichier base.py restauré")
except:
    print("⚠️  Pas de backup trouvé")

# Vérifier que federation_admin est bien dans les conditions
with open('apps/competitions/views/dashboard/base.py', 'r') as f:
    content = f.read()
    
if "elif profile.role == 'federation_admin':" in content:
    print("✅ Condition federation_admin présente")
else:
    print("❌ Condition federation_admin manquante!")
PYEOF

echo ""
echo "4️⃣ Test alternatif - Forcer temporairement un role différent..."
echo "=============================================================="
python3 << 'PYEOF'
import django
django.setup()

from django.contrib.auth import get_user_model
from apps.competitions.models import UserProfile

User = get_user_model()
user = User.objects.filter(username='DT_bguinziemba').first()

if user and hasattr(user, 'userprofile'):
    profile = user.userprofile
    
    # Essayer de voir si c'est un problème d'encoding
    print(f"🧪 Test de différents roles:")
    
    # Sauvegarder le role actuel
    original_role = profile.role
    
    # Tester avec 'admin'
    profile.role = 'admin'
    profile.save()
    print(f"   - Changé temporairement à: '{profile.role}'")
    
    # Remettre federation_admin
    profile.role = 'federation_admin'
    profile.save()
    print(f"   - Remis à: '{profile.role}'")
    
    # Forcer un refresh depuis la DB
    profile.refresh_from_db()
    print(f"   - Après refresh: '{profile.role}'")
PYEOF

echo ""
echo "5️⃣ Redémarrage final..."
echo "======================="
sudo systemctl restart martialcomp
echo "✅ Service redémarré"

echo ""
echo "================================================"
echo "📊 RÉSUMÉ"
echo "================================================"
echo ""
echo "Si l'utilisateur est toujours redirigé vers spectateur,"
echo "c'est peut-être parce que:"
echo ""
echo "1. Le middleware interfère avec la redirection"
echo "2. Une autre vue intercepte la requête avant"
echo "3. Le role n'est pas exactement 'federation_admin'"
echo ""
echo "Testez maintenant la connexion et vérifiez les logs."

REMOTE_COMMANDS