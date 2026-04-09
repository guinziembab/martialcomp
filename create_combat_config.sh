#\!/bin/bash
# Créer une configuration de combat

echo "=== CRÉATION CONFIGURATION DE COMBAT ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Créer une configuration de combat pour Long Phai..."
sudo -u www-data python3 manage.py shell << 'PYTHON_CREATE'
from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Competition, Discipline

# Récupérer la discipline Long Phai
try:
    discipline = Discipline.objects.get(id=63)  # Long Phai
    print(f"Discipline trouvée: {discipline.name}")
    
    # Créer une configuration de combat par défaut pour Long Phai
    config, created = CombatConfiguration.objects.get_or_create(
        discipline=discipline,
        nom="Configuration Long Phai Standard",
        defaults={
            'system': 'qwan_ki_do',  # Ou 'custom' si vous préférez
            'description': 'Configuration standard pour les combats Long Phai',
            'durees_combat': {
                "cadet": 120,    # 2 minutes
                "junior": 150,   # 2.5 minutes
                "senior": 180,   # 3 minutes
                "veteran": 120   # 2 minutes
            },
            'durees_prolongation': {
                "default": 60    # 1 minute de prolongation
            },
            'nb_sorties_avertissement': 3,
            'nb_sorties_disqualification': 5,
            'valeurs_points': {
                "technique_simple": 1,
                "technique_complexe": 2,
                "technique_exceptionnelle": 3
            },
            'valeurs_penalites': {
                "avertissement": -0.5,
                "penalite_mineure": -1,
                "penalite_majeure": -2
            },
            'nb_avertissements_sanction': 3,
            'valeur_sanction': -1
        }
    )
    
    if created:
        print("✓ Configuration de combat créée avec succès\!")
    else:
        print("✓ Configuration de combat existante trouvée")
    
    print(f"Configuration: {config.nom}")
    print(f"Système: {config.system}")
    
    # Vérifier qu'elle est bien créée
    configs = CombatConfiguration.objects.filter(discipline=discipline)
    print(f"\nNombre de configurations pour Long Phai: {configs.count()}")
    
except Discipline.DoesNotExist:
    print("✗ Discipline Long Phai non trouvée")
except Exception as e:
    print(f"✗ Erreur: {e}")

print("\n2. Créer des profils d'arbitres de combat...")
from django.contrib.auth.models import User

# Récupérer quelques utilisateurs pour les rendre arbitres
users = User.objects.filter(is_active=True, is_staff=True)[:3]
print(f"Utilisateurs staff trouvés: {users.count()}")

for user in users:
    print(f"  - {user.username} (staff)")
    # On pourrait créer des JudgeProfile ici si le modèle existe

# Vérifier aussi les super-utilisateurs
superusers = User.objects.filter(is_superuser=True, is_active=True)
print(f"\nSuper-utilisateurs actifs: {superusers.count()}")
for su in superusers:
    print(f"  - {su.username} (superuser)")
PYTHON_CREATE

echo -e "\n2. Vérifier que la configuration a été créée..."
sudo -u www-data python3 manage.py shell << 'PYTHON_VERIFY'
from apps.competitions.models.combat import CombatConfiguration

configs = CombatConfiguration.objects.all()
print(f"Total configurations de combat: {configs.count()}")
for config in configs:
    print(f"  - {config.nom} (Discipline: {config.discipline})")
PYTHON_VERIFY

echo -e "\n✓ Configuration créée. Les champs devraient maintenant être activés."

SSHEOF

echo ""
echo "=== CRÉATION TERMINÉE ==="
