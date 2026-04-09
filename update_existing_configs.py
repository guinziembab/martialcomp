"""
Script pour mettre à jour les configurations existantes avec les labels
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.competitions.models.combat import CombatConfiguration
from apps.competitions.models import Discipline

# Configurations par discipline
DISCIPLINE_CONFIGS = {
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
        'nb_combattants_equipe': 5,
        'afficher_nom_equipe': True,
        'cumul_points_equipe': True
    },
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
        'nb_combattants_equipe': 1,
        'afficher_nom_equipe': False,
        'cumul_points_equipe': False
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
        'nb_combattants_equipe': 1,
        'afficher_nom_equipe': False,
        'cumul_points_equipe': False
    }
}

print("=== MISE À JOUR DES CONFIGURATIONS EXISTANTES ===")

# Récupérer toutes les configurations
configs = CombatConfiguration.objects.all()
print(f"\nNombre de configurations trouvées: {configs.count()}")

for config in configs:
    print(f"\n📝 Configuration: {config.nom} (Système: {config.system})")
    
    # Déterminer la config à appliquer
    if config.system in DISCIPLINE_CONFIGS:
        disc_config = DISCIPLINE_CONFIGS[config.system]
    else:
        # Config par défaut
        disc_config = DISCIPLINE_CONFIGS['qwan_ki_do']
        print("   → Utilisation de la configuration Qwan Ki Do par défaut")
    
    # Appliquer les valeurs
    config.valeurs_points = disc_config['valeurs_points']
    config.valeurs_penalites = disc_config['valeurs_penalites']
    config.labels_points = disc_config['labels_points']
    config.labels_penalites = disc_config['labels_penalites']
    config.nb_combattants_equipe = disc_config['nb_combattants_equipe']
    config.afficher_nom_equipe = disc_config['afficher_nom_equipe']
    config.cumul_points_equipe = disc_config['cumul_points_equipe']
    
    try:
        config.save()
        print("   ✓ Mise à jour réussie")
        print(f"     - Points: {config.valeurs_points}")
        print(f"     - Pénalités: {config.valeurs_penalites}")
        print(f"     - Équipe: {config.nb_combattants_equipe} combattant(s)")
        print(f"     - Cumul équipe: {'Oui' if config.cumul_points_equipe else 'Non'}")
    except Exception as e:
        print(f"   ✗ Erreur: {e}")

# Si aucune configuration n'existe, en créer une par défaut
if configs.count() == 0:
    print("\n⚠️  Aucune configuration trouvée. Création d'une configuration par défaut...")
    
    # Récupérer ou créer une discipline
    discipline = Discipline.objects.first()
    if not discipline:
        discipline = Discipline.objects.create(
            name="Qwan Ki Do",
            description="Art martial vietnamien"
        )
        print("   ✓ Discipline créée")
    
    # Créer la configuration
    config = CombatConfiguration.objects.create(
        discipline=discipline,
        nom="Configuration par défaut",
        system='qwan_ki_do',
        valeurs_points=DISCIPLINE_CONFIGS['qwan_ki_do']['valeurs_points'],
        valeurs_penalites=DISCIPLINE_CONFIGS['qwan_ki_do']['valeurs_penalites'],
        labels_points=DISCIPLINE_CONFIGS['qwan_ki_do']['labels_points'],
        labels_penalites=DISCIPLINE_CONFIGS['qwan_ki_do']['labels_penalites'],
        nb_combattants_equipe=DISCIPLINE_CONFIGS['qwan_ki_do']['nb_combattants_equipe'],
        afficher_nom_equipe=DISCIPLINE_CONFIGS['qwan_ki_do']['afficher_nom_equipe'],
        cumul_points_equipe=DISCIPLINE_CONFIGS['qwan_ki_do']['cumul_points_equipe']
    )
    print(f"   ✓ Configuration '{config.nom}' créée avec succès")

print("\n✅ Mise à jour terminée!")
print("\n📝 Pour tester l'interface, accédez à:")
print("   http://127.0.0.1:8888/en/competitions/combat/combats/3/interface-v2/")