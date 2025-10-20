"""
Vues pour la gestion des catégories de compétition - Version simplifiée
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
def manage_categories(request, competition_id):
    """Gérer les catégories d'une compétition - Vue simplifiée"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Récupérer les catégories existantes
    categories = competition.categories.all()
    
    # Récupérer les grades pour la discipline
    # TODO: Implémenter la récupération des grades depuis apps.grades si nécessaire
    grades = []
    
    context = {
        'competition': competition,
        'categories': categories,
        'grades': grades,
    }
    
    return render(request, 'competitions/club/competition_management_simple.html', context)


@login_required
@require_POST
def add_category(request, competition_id):
    """Ajouter une catégorie à une compétition - Version simplifiée"""
    competition = get_object_or_404(Competition, id=competition_id)
    
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
        min_grade = request.POST.get('min_grade')
        max_grade = request.POST.get('max_grade')
        
        # Convertir en types appropriés
        min_age = int(min_age) if min_age and min_age.strip() else None
        max_age = int(max_age) if max_age and max_age.strip() else None
        min_weight = float(min_weight) if min_weight and min_weight.strip() else None
        max_weight = float(max_weight) if max_weight and max_weight.strip() else None
        
        # Gérer le genre
        gender = request.POST.get('gender', 'mixed')
        if gender == 'male':
            gender = 'male'
        elif gender == 'female':
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
            max_weight=max_weight,
            min_grade=min_grade,
            max_grade=max_grade
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