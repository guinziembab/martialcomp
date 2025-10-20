"""
Vues pour la gestion des catégories de compétition
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from ..models import Competition, CompetitionCategory, CompetitionType


@login_required
def competition_categories(request, competition_id):
    """Gérer les catégories d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions - pour l'instant autoriser tous les utilisateurs connectés
    # TODO: Ajouter le champ created_by au modèle Competition pour une vraie vérification
    pass
    
    # Récupérer les catégories existantes
    categories = competition.categories.all()
    
    # Récupérer les types de compétition pour la discipline
    competition_types = CompetitionType.objects.filter(discipline=competition.discipline)
    
    context = {
        'competition': competition,
        'categories': categories,
        'competition_types': competition_types,
    }
    
    return render(request, 'competitions/categories/manage.html', context)


@login_required
@require_POST
def add_category(request, competition_id):
    """Ajouter une catégorie à une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions
    if not request.user.is_staff and hasattr(competition, 'created_by') and competition.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("Vous n'avez pas les droits pour modifier cette compétition.")
        })
    
    try:
        # Récupérer les données
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({
                'success': False,
                'message': _("Le nom de la catégorie est requis.")
            })
        
        # Récupérer un type de compétition par défaut
        comp_type = CompetitionType.objects.filter(discipline=competition.discipline).first()
        if not comp_type:
            return JsonResponse({
                'success': False,
                'message': _("Aucun type de compétition trouvé pour cette discipline.")
            })
        
        # Gérer les champs optionnels
        min_age = request.POST.get('min_age')
        max_age = request.POST.get('max_age')
        min_weight = request.POST.get('min_weight')
        max_weight = request.POST.get('max_weight')
        
        # Convertir en types appropriés
        min_age = int(min_age) if min_age and min_age.strip() else None
        max_age = int(max_age) if max_age and max_age.strip() else None
        min_weight = float(min_weight) if min_weight and min_weight.strip() else None
        max_weight = float(max_weight) if max_weight and max_weight.strip() else None
        
        # Gérer le genre
        gender = request.POST.get('gender', 'mixed')
        if gender == 'M':
            gender = 'male'
        elif gender == 'F':
            gender = 'female'
        else:
            gender = 'mixed'
        
        # Créer la catégorie
        category = CompetitionCategory.objects.create(
            competition=competition,
            competition_type=comp_type,
            name=name,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            min_weight=min_weight,
            max_weight=max_weight
        )
        
        return JsonResponse({
            'success': True,
            'message': _("Catégorie ajoutée avec succès."),
            'category_id': category.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de l'ajout de la catégorie: {}").format(str(e))
        })


@login_required
@require_POST
def delete_category(request, competition_id):
    """Supprimer une catégorie d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions
    if not request.user.is_staff and hasattr(competition, 'created_by') and competition.created_by != request.user:
        return JsonResponse({
            'success': False,
            'message': _("Vous n'avez pas les droits pour modifier cette compétition.")
        })
    
    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        
        if not category_id:
            return JsonResponse({
                'success': False,
                'message': _("ID de la catégorie requis.")
            })
        
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)
        
        # Vérifier s'il y a des inscriptions liées
        from apps.competitions.models import CompetitionRegistration
        registrations_count = CompetitionRegistration.objects.filter(
            competition=competition,
            category=category
        ).count()
        
        if registrations_count > 0:
            return JsonResponse({
                'success': False,
                'message': _("Impossible de supprimer cette catégorie car {} inscription(s) y sont liées.").format(registrations_count)
            })
        
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': _("Catégorie '{}' supprimée avec succès.").format(category_name)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la suppression de la catégorie: {}").format(str(e))
        })