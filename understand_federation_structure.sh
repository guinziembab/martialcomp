#\!/bin/bash
# Comprendre la structure Federation/Organization

echo "================================================"
echo "🔍 ANALYSE STRUCTURE FEDERATION/ORGANIZATION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Analyse de la relation Federation-Organization..."
echo "==================================================="
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 << 'PYEOF'
import django
django.setup()

from apps.competitions.models import Federation, Organization, Club, Competition

print("📋 Structure du modèle Federation:")
fed = Federation.objects.get(id=41)
print(f"   - Nom: {fed.name}")

# Vérifier si Federation a un champ organization
if hasattr(fed, 'organization'):
    print(f"   - Organization associée: {fed.organization}")
    print(f"   - Type: {type(fed.organization)}")
    org = fed.organization
    
    # Tester les requêtes
    print("\n🧪 Test des requêtes avec l'organization:")
    try:
        clubs = Club.objects.filter(organization=org).count()
        print(f"   ✅ Clubs dans l'organization: {clubs}")
    except Exception as e:
        print(f"   ❌ Erreur clubs: {e}")
    
    try:
        # Pour Competition, chercher par organizing_organization
        comps = Competition.objects.filter(organizing_organization=org).count()
        print(f"   ✅ Compétitions de l'organization: {comps}")
    except Exception as e:
        print(f"   ❌ Erreur compétitions: {e}")
        
    # Essayer une autre approche pour les compétitions liées à la fédération
    print("\n🧪 Approche alternative pour les compétitions:")
    try:
        # Via les clubs de la fédération
        clubs_fed = Club.objects.filter(organization=org)
        comps_via_clubs = Competition.objects.filter(organizing_organization=org).count()
        print(f"   ✅ Compétitions via organization: {comps_via_clubs}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
else:
    print("   ❌ Federation n'a pas de champ 'organization'")
    
    # Chercher comment Federation est liée à Organization
    print("\n📋 Champs de Federation:")
    for field in Federation._meta.get_fields():
        if 'org' in field.name.lower():
            print(f"   - {field.name}: {field.__class__.__name__}")
PYEOF

echo ""
echo "2️⃣ Vérification de la vue actuelle..."
echo "===================================="
echo "📋 Extrait du code problématique (lignes 108-115):"
sed -n '108,115p' apps/competitions/views/dashboard/federations.py

echo ""
echo "3️⃣ Proposition de correction..."
echo "=============================="
echo "Si Federation.organization existe, la correction serait:"
echo "- clubs_count = Club.objects.filter(organization=federation.organization).count()"
echo "- competitions_count = Competition.objects.filter(organizing_organization=federation.organization).count()"

REMOTE_COMMANDS
