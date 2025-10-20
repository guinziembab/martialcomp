#\!/bin/bash
# Vérifier que le dashboard fonctionne maintenant

echo "================================================"
echo "🧪 VÉRIFICATION FINALE DU DASHBOARD"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "Test avec authentification complète..."
echo "===================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from django.test import Client

client = Client()

# Se connecter
print("1️⃣ Connexion...")
logged = client.login(username='DT_bguinziemba', password='AQWZSX123ok,')
print(f"   {'✅ OK' if logged else '❌ Échec'}")

if logged:
    # Accéder au dashboard fédération
    print("\n2️⃣ Accès au dashboard fédération...")
    try:
        resp = client.get('/competitions/dashboard/federation/41/', HTTP_HOST='martialcomp.com', follow=True)
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 200:
            print("   ✅ Dashboard accessible\!")
            
            # Vérifier le contenu
            content = resp.content.decode('utf-8')
            
            # Rechercher des indicateurs de succès
            if 'UBLP' in content:
                print("   ✅ Nom de la fédération présent")
            if 'Tableau de bord' in content or 'Dashboard' in content:
                print("   ✅ Page de dashboard confirmée")
            
            # Rechercher des erreurs
            if 'NoReverseMatch' in content:
                print("   ❌ Encore des erreurs d'URL dans le template")
            elif 'error' in content.lower() and 'no error' not in content.lower():
                print("   ⚠️  Possible erreur dans la page")
            else:
                print("   ✅ Pas d'erreurs évidentes détectées")
                
        else:
            print(f"   ❌ Erreur {resp.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
PYEOF

echo ""
echo "Vérification des logs..."
echo "======================="
echo "📋 Dernières erreurs (si présentes):"
tail -10 logs/django.log  < /dev/null |  grep -E "ERROR|NoReverseMatch" | tail -5 || echo "Pas d'erreurs récentes"

echo ""
echo "================================================"
echo "✅ TEST TERMINÉ"
echo "================================================"

REMOTE_COMMANDS
