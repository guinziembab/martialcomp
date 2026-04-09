#\!/bin/bash
# Créer une configuration de combat complète

echo "=== CRÉATION CONFIGURATION COMBAT COMPLÈTE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Examiner la structure du modèle CombatConfiguration..."
grep -A50 "class CombatConfiguration" apps/competitions/models/combat.py  < /dev/null |  grep -E "models\.|verbose_name|null|blank" | head -30

echo -e "\n2. Créer une configuration avec tous les champs requis..."
sudo -u www-data python3 manage.py shell << 'PYTHON_CREATE'
from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Discipline

try:
    discipline = Discipline.objects.get(id=63)  # Long Phai
    print(f"Création de configuration pour: {discipline.name}")
    
    # Créer une configuration avec TOUS les champs nécessaires
    config = CombatConfiguration.objects.create(
        discipline=discipline,
        nom="Configuration Long Phai Standard",
        system='qwan_ki_do',
        description='Configuration standard pour les combats Long Phai',
        durees_combat={
            "cadet": 120,    # 2 minutes
            "junior": 150,   # 2.5 minutes
            "senior": 180,   # 3 minutes
            "veteran": 120   # 2 minutes
        },
        durees_prolongation={
            "default": 60    # 1 minute
        },
        nb_sorties_avertissement=3,
        nb_sorties_disqualification=5,
        valeurs_points={
            "technique_simple": 1,
            "technique_complexe": 2,
            "technique_exceptionnelle": 3
        },
        valeurs_penalites={
            "avertissement": -0.5,
            "penalite_mineure": -1,
            "penalite_majeure": -2
        },
        nb_avertissements_sanction=3,
        valeur_sanction=-1,
        # Champs supplémentaires qui pourraient être requis
        labels_points={
            "technique_simple": "Technique Simple (1 pt)",
            "technique_complexe": "Technique Complexe (2 pts)",
            "technique_exceptionnelle": "Technique Exceptionnelle (3 pts)"
        },
        labels_penalites={
            "avertissement": "Avertissement",
            "penalite_mineure": "Pénalité Mineure",
            "penalite_majeure": "Pénalité Majeure"
        },
        config_arbitrage={
            "nb_arbitres_lateraux": 2,
            "arbitre_central_requis": True,
            "video_arbitrage": False
        },
        regles_specifiques={
            "autoriser_projections": True,
            "autoriser_sol": False,
            "temps_sol_max": 0
        },
        categories_autorisees=["cadet", "junior", "senior", "veteran"],
        affichage_options={
            "afficher_score_temps_reel": True,
            "afficher_chrono": True,
            "son_fin_combat": True
        }
    )
    
    print(f"✓ Configuration créée avec succès: {config.nom}")
    print(f"  ID: {config.id}")
    
except Exception as e:
    print(f"✗ Erreur lors de la création: {e}")
    print(f"Type d'erreur: {type(e).__name__}")
    
    # Si erreur, essayer avec le minimum requis
    print("\nTentative avec configuration minimale...")
    try:
        # D'abord voir quels champs sont vraiment requis
        from django.db import models
        for field in CombatConfiguration._meta.get_fields():
            if hasattr(field, 'null') and not field.null and field.name not in ['id', 'created_at', 'updated_at']:
                print(f"  - Champ requis: {field.name}")
    except:
        pass
PYTHON_CREATE

echo -e "\n3. Si échec, utiliser l'interface d'administration..."
echo "URL d'administration: https://martialcomp.com/fr/admin/competitions/combatconfiguration/add/"
echo "Vous pouvez créer manuellement une configuration via l'admin Django"

echo -e "\n4. Pour le moment, mettre à jour le formulaire pour gérer l'absence de configuration..."
# On peut modifier le formulaire pour ne pas exiger de configuration

SSHEOF

echo ""
echo "=== ANALYSE TERMINÉE ==="
