#\!/bin/bash
# Solution simple pour corriger le formulaire

echo "=== SOLUTION SIMPLE FORMULAIRE COMBAT ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Créer une configuration de combat minimale via l'admin..."
echo "Essayons d'abord de créer une configuration simple"

sudo -u www-data python3 manage.py shell << 'PYTHON_CONFIG'
from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Discipline

try:
    # Configuration minimale avec seulement les champs requis
    discipline = Discipline.objects.get(id=63)
    
    # Valeurs par défaut simples
    config = CombatConfiguration(
        discipline=discipline,
        nom="Long Phai Standard",
        system='qwan_ki_do',
        description='Configuration standard Long Phai'
    )
    
    # Définir les JSONFields avec des valeurs par défaut
    config.durees_combat = {"default": 120}  # 2 minutes
    config.durees_prolongation = {"default": 60}  # 1 minute
    config.nb_sorties_avertissement = 3
    config.nb_sorties_disqualification = 5
    config.valeurs_points = {"point": 1}
    config.valeurs_penalites = {"penalite": -1}
    config.nb_avertissements_sanction = 3
    config.valeur_sanction = -1
    
    config.save()
    print("✓ Configuration créée avec succès\!")
    print(f"  ID: {config.id}")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    
    # Afficher exactement quels champs sont manquants
    import traceback
    traceback.print_exc()
PYTHON_CONFIG

echo -e "\n2. Vérifier les configurations existantes..."
sudo -u www-data python3 manage.py shell << 'PYTHON_CHECK'
from apps.competitions.models.combat import CombatConfiguration

configs = CombatConfiguration.objects.all()
print(f"Nombre total de configurations: {configs.count()}")

if configs.exists():
    for config in configs:
        print(f"  - ID: {config.id}, Nom: {config.nom}, Discipline: {config.discipline}")
else:
    print("Aucune configuration trouvée.")
    print("\nPour créer une configuration:")
    print("1. Allez sur https://martialcomp.com/fr/admin/")
    print("2. Connectez-vous avec un compte admin")
    print("3. Cherchez 'Combat configurations' dans la section Competitions")
    print("4. Cliquez sur 'Ajouter'")
PYTHON_CHECK

echo -e "\n3. Alternative: Rendre le champ configuration vraiment optionnel dans le modèle..."
# On pourrait modifier le modèle Combat pour rendre configuration nullable
grep -A5 -B5 "configuration.*ForeignKey" apps/competitions/models/combat.py  < /dev/null |  grep -C3 "Combat"

echo -e "\n✓ Instructions pour résoudre le problème:"
echo "1. Créez une configuration via l'admin Django"
echo "2. Ou modifiez temporairement le modèle Combat pour rendre 'configuration' optionnel"
echo "3. Les arbitres peuvent être sélectionnés parmi les utilisateurs staff"

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
