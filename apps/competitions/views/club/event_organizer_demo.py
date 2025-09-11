"""
Version de démonstration de l'interface d'organisation d'événements
Fonctionne avec des données d'exemple pour la démonstration
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import random

@login_required
def event_organizer_demo(request):
    """
    Version démo de l'interface d'organisation d'événements
    Utilise des données d'exemple pour montrer toutes les fonctionnalités
    """
    
    today = timezone.now().date()
    
    # Données d'exemple pour la démonstration
    demo_organization = {
        'name': 'École Martiale de Démonstration',
        'id': 1
    }
    
    # Compétitions en cours d'organisation (données d'exemple)
    demo_competitions = [
        {
            'id': 1,
            'name': 'Championnat Régional Karaté 2024',
            'start_date': today + timedelta(days=15),
            'end_date': today + timedelta(days=16),
            'location': 'Complexe Sportif Municipal',
            'status': 'published',
            'get_status_display': 'Publié'
        },
        {
            'id': 2,
            'name': 'Open International Taekwondo',
            'start_date': today + timedelta(days=45),
            'end_date': today + timedelta(days=47),
            'location': 'Palais des Sports',
            'status': 'draft',
            'get_status_display': 'Brouillon'
        },
        {
            'id': 3,
            'name': 'Tournoi Jeunes Espoirs',
            'start_date': today + timedelta(days=7),
            'end_date': today + timedelta(days=7),
            'location': 'Dojo Central',
            'status': 'ongoing',
            'get_status_display': 'En cours'
        }
    ]
    
    # Événements génériques
    demo_events = [
        {
            'id': 1,
            'title': 'Stage de Formation Arbitres',
            'start_date': today + timedelta(days=20),
            'location': 'Centre de Formation',
            'event_type': 'training',
            'get_event_type_display': 'Formation'
        },
        {
            'id': 2,
            'title': 'Assemblée Générale Annuelle',
            'start_date': today + timedelta(days=30),
            'location': 'Siège de la Fédération',
            'event_type': 'meeting',
            'get_event_type_display': 'Réunion'
        }
    ]
    
    # Événements terminés récemment
    demo_completed = [
        {
            'id': 4,
            'name': 'Coupe de Printemps',
            'end_date': today - timedelta(days=5),
            'status': 'completed'
        },
        {
            'id': 5,
            'name': 'Tournoi des Ceintures Noires',
            'end_date': today - timedelta(days=12),
            'status': 'completed'
        }
    ]
    
    # Données détaillées par événement
    event_details = {}
    
    for comp in demo_competitions:
        # Générer des données réalistes
        total_participants = random.randint(25, 150)
        confirmed = int(total_participants * 0.8)
        pending = total_participants - confirmed
        categories_count = random.randint(8, 24)
        expected_revenue = total_participants * random.randint(20, 45)
        
        # Score de préparation basé sur le statut
        if comp['status'] == 'draft':
            prep_score = random.randint(30, 60)
            issues = ['Configuration incomplète', 'Catégories à définir']
        elif comp['status'] == 'published':
            prep_score = random.randint(75, 95)
            issues = ['Quelques détails à finaliser'] if prep_score < 90 else []
        else:  # ongoing
            prep_score = 100
            issues = []
            
        event_details[comp['id']] = {
            'competition': comp,
            'stats': {
                'total_participants': total_participants,
                'confirmed_participants': confirmed,
                'pending_participants': pending,
                'categories_count': categories_count,
                'expected_revenue': expected_revenue,
                'preparation_score': prep_score,
                'preparation_issues': issues
            }
        }
    
    for event in demo_events:
        participants = random.randint(10, 40)
        confirmed = int(participants * 0.9)
        
        event_details[f"event_{event['id']}"] = {
            'event': event,
            'stats': {
                'total_participants': participants,
                'confirmed_participants': confirmed,
                'revenue': participants * random.randint(15, 30)
            }
        }
    
    # Statistiques globales
    total_registrations = sum(d['stats']['total_participants'] for d in event_details.values())
    confirmed_registrations = sum(d['stats'].get('confirmed_participants', 0) for d in event_details.values())
    pending_registrations = total_registrations - confirmed_registrations
    
    # Statistiques financières
    financial_stats = {
        'event_revenue': 12450,
        'total_invoiced': 18750,
        'invoices_issued': 15,
        'pending_payments': 8,
        'currency': 'EUR'
    }
    
    # Alertes générées automatiquement
    alerts = [
        {
            'type': 'warning',
            'title': 'Peu d\'inscriptions - Tournoi Jeunes Espoirs',
            'message': 'Seulement 28 participants inscrits, événement dans 7 jours',
            'action_url': '#'
        },
        {
            'type': 'info',
            'title': 'Inscriptions à traiter - Championnat Régional',
            'message': '12 inscriptions en attente de confirmation',
            'action_url': '#'
        },
        {
            'type': 'danger',
            'title': 'Configuration urgente - Open International',
            'message': 'Catégories et planning non définis, événement dans 45 jours',
            'action_url': '#'
        }
    ]
    
    # Activité récente
    recent_activity = [
        {
            'type': 'registration',
            'timestamp': today - timedelta(hours=2),
            'title': 'Nouvelle inscription - Championnat Régional',
            'description': 'Marie Dubois (Club Olympique)',
            'icon': 'fas fa-user-plus'
        },
        {
            'type': 'registration',
            'timestamp': today - timedelta(hours=5),
            'title': 'Nouvelle inscription - Tournoi Jeunes',
            'description': 'Pierre Martin (Dojo des Pins)',
            'icon': 'fas fa-user-plus'
        },
        {
            'type': 'payment',
            'timestamp': today - timedelta(hours=8),
            'title': 'Paiement reçu',
            'description': 'Inscription Pierre Martin - 25€',
            'icon': 'fas fa-euro-sign'
        }
    ]
    
    # KPI
    kpi_data = {
        'total_events': len(demo_competitions) + len(demo_events),
        'total_participants': total_registrations,
        'confirmation_rate': (confirmed_registrations / total_registrations * 100) if total_registrations > 0 else 0,
        'expected_revenue': sum(d['stats'].get('expected_revenue', 0) for d in event_details.values()),
        'events_this_month': 3
    }
    
    context = {
        'club': {'name': 'Club Organisateur Démo'},
        'organization': demo_organization,
        'ongoing_competitions': demo_competitions,
        'ongoing_events': demo_events,
        'recent_completed': demo_completed,
        'event_details': event_details,
        'stats': {
            'total_registrations': total_registrations,
            'confirmed_registrations': confirmed_registrations,
            'pending_registrations': pending_registrations,
        },
        'financial_stats': financial_stats,
        'alerts': alerts,
        'recent_activity': recent_activity,
        'kpi_data': kpi_data,
        'current_section': 'event_organizer',
        'page_title': 'Organisation d\'Événements (DÉMO)',
        'is_demo': True,
    }
    
    return render(request, 'competitions/club/event_organizer_dashboard.html', context)


@login_required
def competition_management_detail_demo(request, competition_id):
    """
    Version démo de la gestion détaillée d'une compétition
    """
    
    # Données d'exemple pour la compétition
    demo_competition = {
        'id': competition_id,
        'name': 'Championnat Régional Karaté 2024',
        'description': 'Compétition officielle regroupant les meilleurs athlètes de la région dans toutes les catégories d\'âge.',
        'start_date': timezone.now().date() + timedelta(days=15),
        'end_date': timezone.now().date() + timedelta(days=16),
        'location': 'Complexe Sportif Municipal',
        'max_participants': 200,
        'registration_deadline': timezone.now().date() + timedelta(days=7),
        'status': 'published',
        'get_status_display': 'Publié'
    }
    
    # Catégories d'exemple
    demo_categories = [
        {
            'id': 1,
            'name': 'Kata Senior Masculine -75kg',
            'min_age': 18, 'max_age': None,
            'min_weight': 65, 'max_weight': 75,
            'gender': 'male',
            'get_gender_display': 'Masculin',
            'participant_count': 12
        },
        {
            'id': 2,
            'name': 'Kumite Junior Féminin',
            'min_age': 14, 'max_age': 17,
            'min_weight': None, 'max_weight': None,
            'gender': 'female',
            'get_gender_display': 'Féminin',
            'participant_count': 8
        },
        {
            'id': 3,
            'name': 'Kata Vétéran Mixte',
            'min_age': 35, 'max_age': None,
            'min_weight': None, 'max_weight': None,
            'gender': 'mixed',
            'get_gender_display': 'Mixte',
            'participant_count': 6
        }
    ]
    
    # Inscriptions d'exemple
    demo_registrations = [
        {
            'id': 1,
            'practitioner': {
                'full_name': 'Jean Dubois',
                'current_grade': 'Ceinture noire 2ème dan',
                'organization': {'name': 'Club Olympique'}
            },
            'category': {'name': 'Kata Senior Masculine -75kg'},
            'status': 'confirmed',
            'get_status_display': 'Confirmé',
            'registration_date': timezone.now().date() - timedelta(days=3)
        },
        {
            'id': 2,
            'practitioner': {
                'full_name': 'Marie Martin',
                'current_grade': 'Ceinture marron',
                'organization': {'name': 'Dojo des Champions'}
            },
            'category': {'name': 'Kumite Junior Féminin'},
            'status': 'pending',
            'get_status_display': 'En attente',
            'registration_date': timezone.now().date() - timedelta(days=1)
        },
        {
            'id': 3,
            'practitioner': {
                'full_name': 'Pierre Moreau',
                'current_grade': 'Ceinture noire 3ème dan',
                'organization': {'name': 'Académie des Arts Martiaux'}
            },
            'category': {'name': 'Kata Vétéran Mixte'},
            'status': 'confirmed',
            'get_status_display': 'Confirmé',
            'registration_date': timezone.now().date() - timedelta(days=5)
        }
    ]
    
    # Données financières d'exemple
    financial_overview = {
        'total_revenue': 1250,
        'pending_payments': 450,
        'expenses': 800,
        'net_profit': 450
    }
    
    # Données de planning d'exemple
    schedule_data = {
        'tatamis': 3,
        'time_slots': [],
        'judge_assignments': []
    }
    
    context = {
        'competition': demo_competition,
        'categories': demo_categories,
        'registrations': demo_registrations,
        'financial_overview': financial_overview,
        'schedule_data': schedule_data,
        'page_title': f"Gestion - {demo_competition['name']} (DÉMO)",
        'is_demo': True,
    }
    
    return render(request, 'competitions/club/competition_management_detail.html', context)