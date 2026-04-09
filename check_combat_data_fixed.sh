#\!/bin/bash
# Vérifier les données disponibles pour les combats (corrigé)

echo "=== VÉRIFICATION DONNÉES COMBAT (CORRIGÉ) ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier les imports et la structure..."
ls -la apps/users/ 2>/dev/null || echo "Pas de dossier apps/users"
ls -la apps/accounts/ 2>/dev/null || echo "Pas de dossier apps/accounts"

echo -e "\n2. Vérifier directement dans la base de données..."
sudo -u www-data python3 manage.py shell << 'PYTHON_CHECK'
from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Competition
from django.contrib.auth.models import User

# Vérifier les configurations
configs = CombatConfiguration.objects.all()
print(f"Nombre de configurations de combat: {configs.count()}")
if configs.count() == 0:
    print("ATTENTION: Aucune configuration de combat n'existe\!")
    print("C'est probablement pourquoi le champ est désactivé.")

# Vérifier la compétition 4
try:
    comp = Competition.objects.get(id=4)
    print(f"\nCompétition ID 4: {comp.title}")
    print(f"Discipline: {comp.discipline}")
    print(f"Discipline ID: {comp.discipline.id}")
    
    # Vérifier s'il y a des configurations pour cette discipline
    configs_discipline = CombatConfiguration.objects.filter(discipline=comp.discipline)
    print(f"Configurations pour cette discipline: {configs_discipline.count()}")
    
    # Si aucune config, on peut en créer une par défaut
    if configs_discipline.count() == 0:
        print("\nAUCUNE CONFIGURATION pour cette discipline\!")
        print("Il faut créer une configuration de combat pour pouvoir sélectionner ce champ.")
except Competition.DoesNotExist:
    print("Compétition ID 4 non trouvée")

# Vérifier les utilisateurs qui peuvent être arbitres
print("\n3. Vérifier les utilisateurs pouvant être arbitres...")
users = User.objects.filter(is_active=True)
print(f"Nombre total d'utilisateurs actifs: {users.count()}")

# Vérifier s'il y a des profils de juges
try:
    from apps.competitions.models.judges import JudgeProfile
    judges = JudgeProfile.objects.filter(is_active=True, is_combat_referee=True)
    print(f"Juges combat actifs: {judges.count()}")
    for judge in judges[:5]:
        print(f"  - {judge.user.username}")
except Exception as e:
    print(f"Erreur avec JudgeProfile: {e}")
PYTHON_CHECK

echo -e "\n3. Examiner le template form_combat.html..."
head -50 apps/competitions/templates/competitions/combat/form_combat.html

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
