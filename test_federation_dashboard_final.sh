#\!/bin/bash
# Tester le dashboard fédération après corrections

echo "================================================"
echo "🧪 TEST FINAL DASHBOARD FÉDÉRATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Test avec curl..."
echo "==================="
echo "Test de l'URL: https://martialcomp.com/fr/competitions/dashboard/federation/41/"
curl -s -o /dev/null -w "Status HTTP: %{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/

echo ""
echo "2️⃣ Vérification des logs récents..."
echo "==================================="
echo "📋 Derniers logs d'erreur (si présents):"
tail -20 logs/django.log  < /dev/null |  grep -E "ERROR|Exception|federation/41" | tail -10 || echo "Pas d'erreurs récentes"

echo ""
echo "3️⃣ Test direct de la vue..."
echo "=========================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.test import Client

client = Client()

# Se connecter
logged_in = client.login(username='DT_bguinziemba', password='AQWZSX123ok,')
print(f"🧪 Login: {logged_in}")

if logged_in:
    # Tester l'accès au dashboard fédération
    response = client.get('/competitions/dashboard/federation/41/', HTTP_HOST='martialcomp.com')
    print(f"📋 Réponse dashboard fédération:")
    print(f"   - Status: {response.status_code}")
    
    if response.status_code == 200:
        print("   ✅ Dashboard fédération accessible\!")
        # Vérifier le contenu
        content = response.content.decode('utf-8')
        if 'UBLP' in content:
            print("   ✅ Contenu de la fédération présent")
    elif response.status_code == 302:
        print(f"   ⚠️  Redirection vers: {response.url}")
    else:
        print(f"   ❌ Erreur {response.status_code}")
PYEOF

echo ""
echo "4️⃣ Vérification du contenu généré..."
echo "===================================="
echo "📋 Extrait de la section statistiques (lignes 105-145):"
sed -n '105,145p' apps/competitions/views/dashboard/federations.py | head -40

echo ""
echo "================================================"
echo "📊 RÉSUMÉ"
echo "================================================"
echo ""
echo "Si le status est 200, le dashboard fonctionne\!"
echo "Si c'est encore 500, vérifiez les logs ci-dessus."

REMOTE_COMMANDS
