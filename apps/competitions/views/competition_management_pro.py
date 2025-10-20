"""
Vue professionnelle pour la gestion complète des compétitions
Utilisée par competition_management_detail.html (nouveau template pro)
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from django.db.models import Count, Q
import json

from ..models import Competition, CompetitionCategory, CompetitionRegistration, CompetitionType


@login_required
def competition_management_pro(request, competition_id):
    """
    Vue principale pour la gestion professionnelle d'une compétition.
    Inclut toutes les fonctionnalités avancées.
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # TODO: Vérifier les permissions
    
    # Récupérer les clubs pour les filtres
    clubs = set()
    for reg in competition.registrations.all():
        if reg.practitioner.club:
            clubs.add(reg.practitioner.club)
    
    context = {
        'competition': competition,
        'clubs': list(clubs),
    }
    
    return render(request, 'competitions/club/competition_management_pro.html', context)


@login_required
@require_POST
def add_competition_type(request, competition_id):
    """Ajouter un type de compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        
        # Créer le type de compétition
        comp_type = CompetitionType.objects.create(
            name=data.get('name'),
            description=data.get('description', ''),
            rules=data.get('rules', 'custom')
        )
        
        # L'associer à la compétition
        competition.competition_types.add(comp_type)
        
        return JsonResponse({
            'success': True,
            'message': _("Type de compétition créé avec succès"),
            'type_id': comp_type.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def assign_to_category(request, competition_id):
    """Assigner un pratiquant à une catégorie par drag & drop"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')
        category_id = data.get('category_id')
        
        registration = get_object_or_404(
            CompetitionRegistration,
            id=registration_id,
            competition=competition
        )
        category = get_object_or_404(
            CompetitionCategory,
            id=category_id,
            competition=competition
        )
        
        # Vérifier qu'il n'est pas déjà dans une catégorie du même type
        if category.competition_type:
            existing = registration.categories.filter(
                competition_type=category.competition_type
            ).exists()
            
            if existing:
                return JsonResponse({
                    'success': False,
                    'message': _("Le pratiquant est déjà inscrit dans une catégorie de ce type")
                })
        
        # Assigner à la catégorie
        registration.categories.add(category)
        
        return JsonResponse({
            'success': True,
            'message': _("Pratiquant affecté avec succès"),
            'practitioner_name': registration.practitioner.get_full_name(),
            'category_name': category.name
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def remove_from_category(request, competition_id):
    """Retirer un pratiquant d'une catégorie"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        registration_id = data.get('registration_id')
        category_id = data.get('category_id')
        
        registration = get_object_or_404(
            CompetitionRegistration,
            id=registration_id,
            competition=competition
        )
        category = get_object_or_404(
            CompetitionCategory,
            id=category_id,
            competition=competition
        )
        
        registration.categories.remove(category)
        
        return JsonResponse({
            'success': True,
            'message': _("Pratiquant retiré de la catégorie")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def publish_competition(request, competition_id):
    """Publier une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Vérifications avant publication
        if not competition.venue_name:
            return JsonResponse({
                'success': False,
                'message': _("Veuillez définir le lieu de la compétition avant de publier")
            })
        
        if not competition.categories.exists():
            return JsonResponse({
                'success': False,
                'message': _("Veuillez créer au moins une catégorie avant de publier")
            })
        
        # Publier
        competition.is_published = True
        competition.save()
        
        # TODO: Envoyer des notifications aux clubs
        
        return JsonResponse({
            'success': True,
            'message': _("Compétition publiée avec succès !")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
@require_POST
def assign_judge(request, competition_id):
    """Assigner un juge à une zone/rôle"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        data = json.loads(request.body)
        judge_id = data.get('judge_id')
        zone = data.get('zone')
        role = data.get('role')
        
        # TODO: Implémenter l'assignation des juges
        
        return JsonResponse({
            'success': True,
            'message': _("Juge affecté avec succès")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@login_required
def get_competition_stats(request, competition_id):
    """Obtenir les statistiques de la compétition en temps réel"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    stats = {
        'practitioners': competition.registrations.count(),
        'categories': competition.categories.count(),
        'judges': 0,  # TODO: Implémenter le compte des juges
        'types': competition.competition_types.count(),
        'unassigned': competition.registrations.filter(categories__isnull=True).count(),
        'by_category': {}
    }
    
    # Statistiques par catégorie
    for category in competition.categories.all():
        stats['by_category'][category.id] = {
            'name': category.name,
            'count': category.registrations.count()
        }
    
    return JsonResponse(stats)