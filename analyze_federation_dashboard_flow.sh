#\!/bin/bash
# Analyser le flux complet de federation_dashboard

echo "================================================"
echo "🔍 ANALYSE COMPLÈTE DU FLUX FEDERATION_DASHBOARD"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Affichage complet de la fonction..."
echo "======================================"
echo "📋 Fonction federation_dashboard complète:"
awk '/^def federation_dashboard\(request, federation_id\):/{p=1} p{print NR ": " $0} /^def [a-z_]+\(/{if(p && \!/^def federation_dashboard/)exit} /^@[a-z_]+/{if(p)exit}' apps/competitions/views/dashboard/federations.py  < /dev/null |  head -100

echo ""
echo "2️⃣ Analyse du problème avec federation_id=41..."
echo "=============================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from apps.competitions.models import Federation
from django.contrib.auth import get_user_model

User = get_user_model()

print("🔍 Analyse avec federation_id=41:")
print("=" * 50)

# Vérifier les conditions
fed = Federation.objects.filter(id=41).first()
user = User.objects.get(username='DT_bguinziemba')

print(f"1. Fédération ID 41 existe: {'✅ Oui' if fed else '❌ Non'}")
if fed:
    print(f"   - Nom: {fed.name}")
    print(f"   - ID: {fed.id}")

print(f"\n2. Utilisateur DT_bguinziemba:")
print(f"   - Username: {user.username}")
print(f"   - Est superuser: {user.is_superuser}")
print(f"   - Est staff: {user.is_staff}")

# Simuler le flux de la fonction
print("\n3. Simulation du flux avec federation_id=41:")
print("   - federation_id n'est pas None ✅")
print("   - Donc on ne rentre PAS dans le bloc if federation_id is None")
print("   - On devrait continuer après la ligne 80")
print("   → Il doit y avoir un problème après la ligne 80")

# Vérifier ce qui se passe après
print("\n4. Qu'est-ce qui devrait se passer après ligne 80?")
print("   - Récupérer la fédération")
print("   - Vérifier les permissions")
print("   - Préparer le contexte")
print("   - Retourner le template")
PYEOF

echo ""
echo "3️⃣ Recherche du code après ligne 80..."
echo "====================================="
echo "📋 Lignes 80-130:"
sed -n '80,130p' apps/competitions/views/dashboard/federations.py

echo ""
echo "================================================"
echo "📊 DIAGNOSTIC"
echo "================================================"
echo ""
echo "Il semble que le code après la ligne 80 soit"
echo "manquant ou incomplet, causant un return None."

REMOTE_COMMANDS
