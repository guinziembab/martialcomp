#\!/bin/bash
# Test du dashboard avec authentification

echo "================================================"
echo "🧪 TEST DASHBOARD AVEC AUTHENTIFICATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Test avec session authentifiée..."
echo "===================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()

print("🔐 Test avec authentification:")
print("=" * 50)

# Se connecter
logged = client.login(username='DT_bguinziemba', password='AQWZSX123ok,')
print(f"1. Connexion: {'✅ Réussie' if logged else '❌ Échouée'}")

if logged:
    # Test du dashboard principal
    print("\n2. Test redirection dashboard principal:")
    resp = client.get('/competitions/dashboard/', HTTP_HOST='martialcomp.com')
    print(f"   - Status: {resp.status_code}")
    if resp.status_code == 302:
        print(f"   - Redirige vers: {resp.url}")
    
    # Test direct du dashboard fédération
    print("\n3. Test direct dashboard fédération:")
    resp = client.get('/competitions/dashboard/federation/41/', HTTP_HOST='martialcomp.com', follow=True)
    print(f"   - Status final: {resp.status_code}")
    
    if resp.status_code == 200:
        content = resp.content.decode('utf-8')
        
        # Vérifier le contenu
        checks = [
            ('UBLP' in content, "Nom de la fédération (UBLP)"),
            ('Tableau de bord' in content or 'Dashboard' in content, "Titre du dashboard"),
            ('Clubs' in content or 'clubs' in content, "Section clubs"),
            ('Compétitions' in content or 'competitions' in content, "Section compétitions"),
        ]
        
        print("\n4. Vérification du contenu:")
        for check, desc in checks:
            print(f"   {'✅' if check else '❌'} {desc}")
        
        # Si des erreurs sont présentes
        if 'error' in content.lower() or 'erreur' in content.lower():
            print("\n⚠️  Erreurs détectées dans la page:")
            import re
            errors = re.findall(r'(error < /dev/null | erreur).*?</[^>]+>', content.lower(), re.IGNORECASE | re.DOTALL)
            for err in errors[:3]:
                print(f"   - {err[:100]}...")
    
    else:
        print(f"   ❌ Erreur: Status {resp.status_code}")
        if resp.redirect_chain:
            print("   Chaîne de redirection:")
            for url, code in resp.redirect_chain:
                print(f"     → {url} ({code})")
PYEOF

echo ""
echo "2️⃣ Vérification des logs après test..."
echo "====================================="
echo "📋 Derniers logs (erreurs uniquement):"
tail -20 logs/django.log | grep -E "ERROR|Exception" | tail -10 || echo "Pas d'erreurs récentes"

echo ""
echo "================================================"
echo "📊 RÉSUMÉ"
echo "================================================"
echo ""
echo "Si le status est 200 et le contenu est vérifié,"
echo "le dashboard fédération fonctionne correctement\!"

REMOTE_COMMANDS
