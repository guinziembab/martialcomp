from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
"""
Vues fonctionnelles pour le dashboard coach
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

# Base template function
def render_coach_page(request, template_name, context_data=None):
    """Fonction utilitaire pour rendre les pages coach"""
    base_context = {
        'user': request.user,
        'page_title': context_data.get('page_title', _('Dashboard Coach')),
        'dashboard_type': 'coach',
    }
    
    if context_data:
        base_context.update(context_data)
    
    return render(request, template_name, base_context)

@login_required
def coach_students(request):
    """Gestion des élèves"""
    context = {
        'page_title': _('Mes élèves'),
        'section': 'students',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Mes élèves'), 'active': True}
        ],
        'students_count': 0,
        'active_students': [],
        'pending_requests': [],
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/students.html', context)

@login_required
def coach_disciplines(request):
    """Gestion des disciplines"""
    from apps.competitions.models import Discipline, CoachProfile
    
    disciplines = []
    coach_profile = None
    
    try:
        # Récupérer le profil coach de l'utilisateur
        coach_profile = CoachProfile.objects.filter(practitioner__user=request.user).first()
        if coach_profile:
            # Récupérer les disciplines associées au coach
            from apps.competitions.models.discipline import Discipline
            disciplines = get_organization_queryset(Discipline, request.user)
    except Exception as e:
        logger.warning(f"Erreur lors de la récupération des disciplines pour {request.user}: {e}")
        disciplines = []
    
    context = {
        'page_title': _('Mes disciplines'),
        'section': 'disciplines',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Mes disciplines'), 'active': True}
        ],
        'disciplines': disciplines,
        'coach_profile': coach_profile,
        'disciplines_count': len(disciplines) if disciplines else 0,
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/disciplines.html', context)

@login_required  
def coach_planning(request):
    """Gestion du planning"""
    context = {
        'page_title': _('Planning'),
        'section': 'planning',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Planning'), 'active': True}
        ],
        'upcoming_classes': [],
        'weekly_schedule': {},
        'today_classes': [],
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/planning.html', context)

@login_required
def coach_programs(request):
    """Programmes d'entraînement"""
    context = {
        'page_title': _('Programmes d\'entraînement'),
        'section': 'programs',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Programmes'), 'active': True}
        ],
        'programs': [
            {
                'id': 1,
                'name': 'Programme Débutant Karaté',
                'duration': '3 mois',
                'students': 5,
                'level': 'Débutant',
                'discipline': 'Karaté'
            },
            {
                'id': 2,
                'name': 'Préparation Compétition',
                'duration': '6 mois',
                'students': 8,
                'level': 'Avancé',
                'discipline': 'Taekwondo'
            }
        ],
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/programs.html', context)

@login_required
def coach_competitions(request):
    """Gestion des compétitions"""
    context = {
        'page_title': _('Compétitions'),
        'section': 'competitions',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Compétitions'), 'active': True}
        ],
        'upcoming_competitions': [
            {
                'name': 'Championnat Régional',
                'date': '15 septembre 2025',
                'location': 'Paris',
                'students_registered': 3
            }
        ],
        'past_competitions': [],
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/competitions.html', context)

@login_required
def coach_stats(request):
    """Statistiques"""
    context = {
        'page_title': _('Statistiques'),
        'section': 'stats',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Statistiques'), 'active': True}
        ],
        'stats': {
            'total_students': 25,
            'active_students': 20,
            'classes_this_month': 45,
            'average_rating': 4.8,
            'revenue_this_month': 2500,
            'competitions_won': 12
        },
        'monthly_data': [
            {'month': 'Janvier', 'students': 18, 'revenue': 2200},
            {'month': 'Février', 'students': 22, 'revenue': 2400},
            {'month': 'Mars', 'students': 25, 'revenue': 2500},
        ]
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/stats.html', context)

@login_required
def coach_finances(request):
    """Gestion financière - Redirection vers le module finance principal"""
    from django.shortcuts import redirect
    
    # Rediriger vers le module finance principal avec un paramètre pour identifier le rôle coach
    return redirect('finances:dashboard')

@login_required
def coach_testimonials(request):
    """Gestion des témoignages"""
    context = {
        'page_title': _('Témoignages'),
        'section': 'testimonials',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Témoignages'), 'active': True}
        ],
        'testimonials': [
            {
                'id': 1,
                'student_name': 'Marie Dupont',
                'rating': 5,
                'comment': 'Excellent coach ! Très pédagogue et patient.',
                'date': '2025-07-15',
                'discipline': 'Karaté'
            },
            {
                'id': 2,
                'student_name': 'Pierre Martin',
                'rating': 5,
                'comment': 'Grâce à lui, j\'ai progressé très rapidement.',
                'date': '2025-07-10',
                'discipline': 'Taekwondo'
            }
        ],
        'average_rating': 4.8,
        'total_reviews': 24
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/testimonials.html', context)

@login_required
def coach_seminars(request):
    """Planification de stages et séminaires"""
    context = {
        'page_title': _('Stages et séminaires'),
        'section': 'seminars',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Stages'), 'active': True}
        ],
        'upcoming_seminars': [
            {
                'id': 1,
                'title': 'Stage d\'été Karaté',
                'date': '15-20 Août 2025',
                'location': 'Dojo principal',
                'participants': 15,
                'max_participants': 20,
                'level': 'Tous niveaux'
            }
        ],
        'past_seminars': [],
        'seminar_requests': []
    }
    
    return render_coach_page(request, 'competitions/dashboard/coach/seminars.html', context)

@login_required
def coach_clients(request):
    """Gestion des clients"""
    context = {
        'page_title': _('Gestion clients'),
        'section': 'clients',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Clients'), 'active': True}
        ],
        'clients': [
            {
                'id': 1,
                'name': 'Marie Dupont',
                'email': 'marie@example.com',
                'phone': '06 12 34 56 78',
                'discipline': 'Karaté',
                'level': 'Intermédiaire',
                'status': 'active',
                'next_payment': '2025-08-15'
            }
        ],
        'client_stats': {
            'total': 25,
            'active': 20,
            'inactive': 3,
            'pending': 2
        }
    }

    return render_coach_page(request, 'competitions/dashboard/coach/clients.html', context)


@login_required
def coach_site_config(request):
    """Configuration du site public coach"""
    from django.contrib import messages
    from apps.competitions.models import CoachProfile, Practitioner

    # Récupérer le profil coach
    coach_profile = None
    practitioner = None
    site_config = {}

    try:
        practitioner = Practitioner.objects.filter(user=request.user).first()
        if practitioner:
            coach_profile = CoachProfile.objects.filter(practitioner=practitioner).first()
    except Exception as e:
        logger.warning(f"Erreur récupération profil coach pour site config: {e}")

    # Traitement du formulaire POST
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            site_config = {
                'site_title': request.POST.get('site_title', ''),
                'site_subtitle': request.POST.get('site_subtitle', ''),
                'about_text': request.POST.get('about_text', ''),
                'specialties': request.POST.get('specialties', ''),
                'experience_years': request.POST.get('experience_years', ''),
                'phone': request.POST.get('phone', ''),
                'email': request.POST.get('email', ''),
                'location': request.POST.get('location', ''),
                'social_facebook': request.POST.get('social_facebook', ''),
                'social_instagram': request.POST.get('social_instagram', ''),
                'social_youtube': request.POST.get('social_youtube', ''),
                # Tarifs
                'tarif_prive': request.POST.get('tarif_prive', '50'),
                'tarif_collectif': request.POST.get('tarif_collectif', '30'),
                'tarif_forfait': request.POST.get('tarif_forfait', '180'),
            }

            # Sauvegarder dans la session pour l'instant (TODO: sauvegarder en BDD)
            request.session['coach_site_config'] = site_config

            messages.success(request, _('Configuration du site enregistrée avec succès !'))

        except Exception as e:
            logger.error(f"Erreur sauvegarde config site coach: {e}")
            messages.error(request, _('Erreur lors de la sauvegarde de la configuration.'))

    # Récupérer la config existante de la session
    site_config = request.session.get('coach_site_config', {})

    # Valeurs par défaut
    default_config = {
        'site_title': f"{request.user.first_name} {request.user.last_name}",
        'site_subtitle': _('Coach Professionnel en Arts Martiaux'),
        'about_text': _('Passionné par les arts martiaux depuis plus de 15 ans, je propose des cours adaptés à tous les niveaux.'),
        'specialties': 'Karaté, Taekwondo, Self-défense',
        'experience_years': '10',
        'phone': '+33 6 XX XX XX XX',
        'email': request.user.email or 'contact@coach.com',
        'location': 'Paris, France',
        'social_facebook': '',
        'social_instagram': '',
        'social_youtube': '',
        'tarif_prive': '50',
        'tarif_collectif': '30',
        'tarif_forfait': '180',
    }

    # Fusionner avec les valeurs par défaut
    for key, value in default_config.items():
        if key not in site_config or not site_config[key]:
            site_config[key] = value

    context = {
        'page_title': _('Configuration du site'),
        'section': 'site_config',
        'breadcrumbs': [
            {'name': _('Dashboard'), 'url': 'competitions:dashboard:coach'},
            {'name': _('Configuration du site'), 'active': True}
        ],
        'coach_profile': coach_profile,
        'practitioner': practitioner,
        'site_config': site_config,
        'coach_slug': practitioner.club.slug if practitioner and hasattr(practitioner, 'club') and practitioner.club else 'coach',
    }

    return render_coach_page(request, 'competitions/dashboard/coach/site_config.html', context)