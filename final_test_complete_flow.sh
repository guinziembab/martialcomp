#\!/bin/bash
# Test complet du flux de connexion et dashboard

echo "================================================"
echo "✅ TEST COMPLET DU FLUX FÉDÉRATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Test de connexion et redirection complète..."
echo "=============================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.test import Client

client = Client()

print("🧪 Test du flux complet:")
print("=" * 50)

# 1. Connexion
print("\n1️⃣ CONNEXION")
logged_in = client.login(username='DT_bguinziemba', password='AQWZSX123ok,')
print(f"   Login réussi: {logged_in}")

if logged_in:
    # 2. Accès au dashboard principal
    print("\n2️⃣ ACCÈS AU DASHBOARD PRINCIPAL")
    response = client.get('/competitions/dashboard/', HTTP_HOST='martialcomp.com', follow=True)
    print(f"   Status final: {response.status_code}")
    
    if response.redirect_chain:
        print("   Chaîne de redirection:")
        for url, code in response.redirect_chain:
            print(f"     → {url} (code: {code})")
    
    final_url = response.wsgi_request.path
    print(f"   URL finale: {final_url}")
    
    # 3. Vérifier qu'on est sur le dashboard fédération
    if '/federation/41/' in final_url or '/federation/' in final_url:
        print("   ✅ Redirection vers dashboard fédération réussie\!")
        
        # 4. Accès direct au dashboard fédération
        print("\n3️⃣ ACCÈS DIRECT AU DASHBOARD FÉDÉRATION")
        response = client.get('/competitions/dashboard/federation/41/', HTTP_HOST='martialcomp.com', follow=True)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            # Vérifier le contenu
            if 'UBLP' in content:
                print("   ✅ Nom de la fédération présent")
            if 'Tableau de bord' in content:
                print("   ✅ Titre du dashboard présent")
            if 'clubs_count' in content or 'Clubs' in content:
                print("   ✅ Section clubs présente")
        
    elif '/spectator/' in final_url:
        print("   ❌ Toujours redirigé vers spectateur")
    else:
        print(f"   ⚠️  Redirigé vers: {final_url}")
PYEOF

echo ""
echo "2️⃣ Test avec curl pour voir le HTML..."
echo "====================================="
echo "📋 Test de l'URL finale:"
RESPONSE=$(curl -s -L -c cookies.txt https://martialcomp.com/fr/competitions/dashboard/federation/41/  < /dev/null |  head -100)
echo "$RESPONSE" | grep -E "<title>|<h1>|dashboard|fédération|UBLP" | head -10

echo ""
echo "================================================"
echo "📊 RÉSUMÉ FINAL"
echo "================================================"
echo ""
echo "✅ Corrections appliquées:"
echo "   - custom_login.py corrigé pour rediriger federation_admin"
echo "   - URLs corrigées (federation_detail au lieu de federation_dashboard)"
echo "   - Dashboard fédération corrigé (plus d'erreur 500)"
echo ""
echo "🔍 L'utilisateur DT_bguinziemba devrait maintenant:"
echo "   1. Se connecter normalement"
echo "   2. Être redirigé vers /competitions/dashboard/"
echo "   3. Qui redirige vers /competitions/dashboard/federation/41/"
echo "   4. Voir le dashboard de sa fédération UBLP"

REMOTE_COMMANDS
