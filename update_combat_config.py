"""
Script pour mettre à jour les configurations de combat existantes
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Discipline

# Configurations par discipline
DISCIPLINE_CONFIGS = {
    'taekwondo': {
        'valeurs_points': [1, 2, 3, 4, 5],
        'valeurs_penalites': [-0.5, -1],
        'labels_points': {
            '1': 'Poing au tronc',
            '2': 'Pied au tronc',
            '3': 'Pied à la tête',
            '4': 'Retourné au tronc',
            '5': 'Retourné à la tête'
        },
        'labels_penalites': {
            '-0.5': 'Kyong-go',
            '-1': 'Gam-jeom'
        },
        'nb_combattants_equipe': 1
    },
    'karate': {
        'valeurs_points': [1, 2, 3],
        'valeurs_penalites': [-1, -2],
        'labels_points': {
            '1': 'Yuko',
            '2': 'Waza-ari',
            '3': 'Ippon'
        },
        'labels_penalites': {
            '-1': 'Keikoku',
            '-2': 'Hansoku-chui'
        },
        'nb_combattants_equipe': 1
    },
    'qwan_ki_do': {
        'valeurs_points': [0.25, 0.5, 1, 1.5, 2],
        'valeurs_penalites': [-0.25, -0.5, -1, -2],
        'labels_points': {
            '0.25': 'Quart de point',
            '0.5': 'Demi-point',
            '1': 'Un point',
            '1.5': 'Un point et demi',
            '2': 'Deux points'
        },
        'labels_penalites': {
            '-0.25': 'Avertissement',
            '-0.5': 'Retrait simple',
            '-1': 'Retrait',
            '-2': 'Retrait double'
        },
        'nb_combattants_equipe': 1
    },
    'default': {
        'valeurs_points': [0.25, 0.5, 1, 1.5, 2],
        'valeurs_penalites': [-0.25, -0.5, -1, -2],
        'labels_points': {},
        'labels_penalites': {},
        'nb_combattants_equipe': 1
    }
}

def update_configurations():
    print("=== MISE À JOUR DES CONFIGURATIONS DE COMBAT ===")
    
    # Mettre à jour les configurations existantes
    configs = CombatConfiguration.objects.all()
    
    for config in configs:
        print(f"\nConfiguration: {config.nom}")
        
        # Déterminer le type de configuration
        system_config = DISCIPLINE_CONFIGS.get(config.system, DISCIPLINE_CONFIGS['default'])
        
        # Mettre à jour avec les valeurs par défaut si vides
        if not config.valeurs_points:
            config.valeurs_points = system_config['valeurs_points']
            print(f"  ✓ Valeurs de points: {config.valeurs_points}")
        
        if not config.valeurs_penalites:
            config.valeurs_penalites = system_config['valeurs_penalites']
            print(f"  ✓ Valeurs de pénalités: {config.valeurs_penalites}")
        
        # Ajouter les labels s'ils n'existent pas
        if not hasattr(config, 'labels_points') or not config.labels_points:
            config.labels_points = system_config.get('labels_points', {})
            print(f"  ✓ Labels de points ajoutés")
        
        if not hasattr(config, 'labels_penalites') or not config.labels_penalites:
            config.labels_penalites = system_config.get('labels_penalites', {})
            print(f"  ✓ Labels de pénalités ajoutés")
        
        # Autres paramètres
        if not hasattr(config, 'nb_combattants_equipe'):
            config.nb_combattants_equipe = system_config['nb_combattants_equipe']
        
        if not hasattr(config, 'afficher_nom_equipe'):
            config.afficher_nom_equipe = True
        
        if not hasattr(config, 'cumul_points_equipe'):
            config.cumul_points_equipe = True
        
        config.save()
    
    print("\n✅ Configurations mises à jour avec succès!")

def create_sample_configs():
    """Créer des configurations d'exemple pour chaque discipline"""
    print("\n=== CRÉATION DE CONFIGURATIONS D'EXEMPLE ===")
    
    for discipline_name, config_data in DISCIPLINE_CONFIGS.items():
        if discipline_name == 'default':
            continue
            
        # Chercher ou créer la discipline
        discipline, _ = Discipline.objects.get_or_create(
            name=discipline_name.title(),
            defaults={'description': f"Configuration {discipline_name}"}
        )
        
        # Vérifier si une config existe déjà
        exists = CombatConfiguration.objects.filter(
            discipline=discipline,
            system=discipline_name
        ).exists()
        
        if not exists:
            config = CombatConfiguration.objects.create(
                discipline=discipline,
                nom=f"Règles officielles {discipline_name.title()}",
                system=discipline_name,
                valeurs_points=config_data['valeurs_points'],
                valeurs_penalites=config_data['valeurs_penalites'],
                labels_points=config_data.get('labels_points', {}),
                labels_penalites=config_data.get('labels_penalites', {}),
                nb_combattants_equipe=config_data['nb_combattants_equipe'],
                afficher_nom_equipe=True,
                cumul_points_equipe=True
            )
            print(f"  ✓ Configuration créée pour {discipline_name}")

if __name__ == "__main__":
    update_configurations()
    # create_sample_configs()  # Décommenter pour créer des configs d'exemple