#\!/bin/bash
# Vérifier les données disponibles pour les combats

echo "=== VÉRIFICATION DONNÉES COMBAT ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier s'il y a des configurations de combat..."
sudo -u www-data python3 << 'PYTHON_CHECK'
import os
import sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
django.setup()

from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Competition
from apps.users.models import User

# Vérifier les configurations
configs = CombatConfiguration.objects.all()
print(f"Nombre de configurations de combat: {configs.count()}")
for config in configs:
    print(f"  - {config.nom} ({config.discipline})")

# Vérifier la compétition 4
try:
    comp = Competition.objects.get(id=4)
    print(f"\nCompétition ID 4: {comp.title}")
    print(f"Discipline: {comp.discipline}")
    
    # Vérifier s'il y a des configurations pour cette discipline
    configs_discipline = CombatConfiguration.objects.filter(discipline=comp.discipline)
    print(f"Configurations pour cette discipline: {configs_discipline.count()}")
except Competition.DoesNotExist:
    print("Compétition ID 4 non trouvée")

# Vérifier les arbitres disponibles
print("\n2. Vérifier les arbitres disponibles...")
# Chercher les utilisateurs avec des rôles d'arbitre
from apps.users.models import UserProfile
arbitres = UserProfile.objects.filter(role='referee').select_related('user')
print(f"Nombre d'arbitres (role=referee): {arbitres.count()}")
for arbitre in arbitres[:5]:
    print(f"  - {arbitre.user.username}")

# Vérifier aussi les juges
from apps.competitions.models.judges import JudgeProfile
judge_profiles = JudgeProfile.objects.filter(is_active=True)
print(f"\nNombre de profils juges actifs: {judge_profiles.count()}")
for judge in judge_profiles[:5]:
    print(f"  - {judge.user.username} (Combat: {judge.is_combat_referee})")
PYTHON_CHECK

echo -e "\n3. Vérifier le template du formulaire..."
find apps -name "*form_combat*" -path "*/templates/*" -type f

echo -e "\n4. Si pas de template, chercher d'autres templates de combat..."
find apps -name "*combat*" -path "*/templates/*" -name "*.html"  < /dev/null |  grep -E "(form|create|creer)" | head -10

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
