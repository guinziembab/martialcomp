# Vue de démonstration pour la gestion des compétitions
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def competition_management_demo(request):
    """
    Version de démonstration de l'interface de gestion des compétitions
    Fonctionne sans avoir besoin d'un club configuré
    """
    
    # Données de démonstration
    demo_data = {
        'club': {
            'name': 'Club de Démonstration',
            'id': 1
        },
        'available_competitions': [
            {
                'id': 1,
                'name': 'Championnat Régional Karaté',
                'start_date': timezone.now().date(),
                'location': 'Dojo Central',
                'categories': [
                    {
                        'id': 1,
                        'name': 'Kata Senior -75kg',
                        'age_min': 18,
                        'age_max': None,
                        'weight_min': 65,
                        'weight_max': 75
                    },
                    {
                        'id': 2,
                        'name': 'Kumite Junior',
                        'age_min': 12,
                        'age_max': 17,
                        'weight_min': None,
                        'weight_max': None
                    }
                ]
            },
            {
                'id': 2,
                'name': 'Tournoi Open Taekwondo',
                'start_date': timezone.now().date(),
                'location': 'Gymnase Municipal',
                'categories': [
                    {
                        'id': 3,
                        'name': 'Poomsae Débutant',
                        'age_min': 8,
                        'age_max': 12,
                        'weight_min': None,
                        'weight_max': None
                    }
                ]
            }
        ],
        'practitioners': [
            {
                'id': 1,
                'full_name': 'Marie Dupont',
                'current_grade': 'Ceinture brune',
                'photo': None
            },
            {
                'id': 2,
                'full_name': 'Jean Martin',
                'current_grade': 'Ceinture noire 1er dan',
                'photo': None
            },
            {
                'id': 3,
                'full_name': 'Sophie Moreau',
                'current_grade': 'Ceinture rouge',
                'photo': None
            }
        ],
        'judges': [
            {
                'id': 1,
                'practitioner': {
                    'full_name': 'Pierre Dubois',
                    'current_grade': 'Ceinture noire 3e dan'
                }
            }
        ]
    }
    
    # Organiser les données comme dans la vraie vue
    competition_data = {}
    for comp in demo_data['available_competitions']:
        competition_data[comp['id']] = {
            'competition': comp,
            'categories': comp['categories'],
            'registrations_by_category': {
                1: [  # Quelques inscriptions d'exemple
                    {
                        'id': 1,
                        'practitioner': demo_data['practitioners'][0],
                        'is_judge': False
                    }
                ],
                2: [
                    {
                        'id': 2,
                        'practitioner': demo_data['practitioners'][1],
                        'is_judge': True
                    }
                ]
            },
            'unregistered_practitioners': demo_data['practitioners'][2:],  # Sophie non inscrite
            'total_registered': 2
        }
    
    context = {
        'club': demo_data['club'],
        'available_competitions': demo_data['available_competitions'],
        'practitioners': demo_data['practitioners'],
        'judges': demo_data['judges'],
        'competition_data': competition_data,
        'current_section': 'competitions',
        'is_demo': True  # Flag pour identifier que c'est une démo
    }
    
    return render(request, 'competitions/club/competition_management.html', context)