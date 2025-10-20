"""
Vues pour la gestion des types de compétition et catégories
"""

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext as _
from django.db import transaction
import json

from ..models import Competition, CompetitionType, CompetitionCategory
from ..forms import CompetitionCategoryForm


@login_required
@require_POST
def add_competition_type(request, pk):
    """Ajouter un type de compétition à une compétition"""
    try:
        competition = get_object_or_404(Competition, pk=pk)
        
        # Vérifier les permissions
        # Pour l'instant, permettre à tous les utilisateurs connectés de modifier
        # TODO: Implémenter une vérification des permissions appropriée
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être connecté pour modifier cette compétition.")
            })
        
        data = json.loads(request.body)
        competition_type_id = data.get('competition_type_id')
        
        if not competition_type_id:
            return JsonResponse({
                'success': False,
                'message': _("ID du type de compétition requis.")
            })
        
        competition_type = get_object_or_404(CompetitionType, id=competition_type_id)
        
        # Vérifier que le type appartient à la même discipline
        if competition_type.discipline != competition.discipline:
            return JsonResponse({
                'success': False,
                'message': _("Le type de compétition doit appartenir à la même discipline que la compétition.")
            })
        
        # Ajouter le type s'il n'est pas déjà présent
        if competition_type not in competition.competition_types.all():
            competition.competition_types.add(competition_type)
            return JsonResponse({
                'success': True,
                'message': _("Type de compétition ajouté avec succès.")
            })
        else:
            return JsonResponse({
                'success': False,
                'message': _("Ce type de compétition est déjà associé à cette compétition.")
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de l'ajout du type de compétition: {}").format(str(e))
        })


@login_required
@require_POST
def remove_competition_type(request, pk):
    """Supprimer un type de compétition d'une compétition"""
    try:
        competition = get_object_or_404(Competition, pk=pk)
        
        # Vérifier les permissions
        # Pour l'instant, permettre à tous les utilisateurs connectés de modifier
        # TODO: Implémenter une vérification des permissions appropriée
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être connecté pour modifier cette compétition.")
            })
        
        data = json.loads(request.body)
        competition_type_id = data.get('competition_type_id')
        
        if not competition_type_id:
            return JsonResponse({
                'success': False,
                'message': _("ID du type de compétition requis.")
            })
        
        competition_type = get_object_or_404(CompetitionType, id=competition_type_id)
        
        # Supprimer le type
        competition.competition_types.remove(competition_type)
        
        return JsonResponse({
            'success': True,
            'message': _("Type de compétition supprimé avec succès.")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la suppression du type de compétition: {}").format(str(e))
        })


@login_required
@require_POST
def add_competition_category(request, pk):
    """Ajouter une catégorie à une compétition"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Tentative d'ajout de catégorie pour la compétition {pk}")
        logger.info(f"POST data: {request.POST}")
        
        competition = get_object_or_404(Competition, pk=pk)
        
        # Vérifier les permissions
        # Pour l'instant, permettre à tous les utilisateurs connectés de modifier
        # TODO: Implémenter une vérification des permissions appropriée
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être connecté pour modifier cette compétition.")
            })
        
        # Créer la catégorie
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({
                'success': False,
                'message': _("Le nom de la catégorie est requis.")
            })
        
        # Récupérer le type de compétition sélectionné
        competition_type_id = request.POST.get('competition_type', '').strip()
        if not competition_type_id:
            return JsonResponse({
                'success': False,
                'message': _("Le type de compétition est requis.")
            })
        
        from apps.competitions.models import CompetitionType
        try:
            comp_type = CompetitionType.objects.get(id=competition_type_id)
            # Vérifier que le type appartient bien à la compétition
            if comp_type not in competition.competition_types.all():
                return JsonResponse({
                    'success': False,
                    'message': _("Le type de compétition sélectionné n'est pas associé à cette compétition.")
                })
        except CompetitionType.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _("Le type de compétition sélectionné n'existe pas.")
            })
        
        # Gérer les champs numériques optionnels
        min_age = request.POST.get('min_age')
        max_age = request.POST.get('max_age')
        min_weight = request.POST.get('min_weight')
        max_weight = request.POST.get('max_weight')
        
        # Convertir en int si non vide
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
        
        category = CompetitionCategory(
            competition=competition,
            competition_type=comp_type,
            name=name,
            gender=gender,
            min_age=min_age,
            max_age=max_age,
            min_weight=min_weight,
            max_weight=max_weight
        )
        
        # Valider la catégorie
        if category.min_age and category.max_age and category.min_age > category.max_age:
            return JsonResponse({
                'success': False,
                'message': _("L'âge minimum ne peut pas être supérieur à l'âge maximum.")
            })
        
        if category.min_weight and category.max_weight and category.min_weight > category.max_weight:
            return JsonResponse({
                'success': False,
                'message': _("Le poids minimum ne peut pas être supérieur au poids maximum.")
            })
        
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': _("Catégorie ajoutée avec succès.")
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de l'ajout de la catégorie: {}").format(str(e))
        })


@login_required
@require_POST
def remove_competition_category(request, pk):
    """Supprimer une catégorie d'une compétition (sans affecter les inscriptions)"""
    try:
        competition = get_object_or_404(Competition, pk=pk)
        
        # Vérifier les permissions
        # Pour l'instant, permettre à tous les utilisateurs connectés de modifier
        # TODO: Implémenter une vérification des permissions appropriée
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': _("Vous devez être connecté pour modifier cette compétition.")
            })
        
        data = json.loads(request.body)
        category_id = data.get('category_id')
        
        if not category_id:
            return JsonResponse({
                'success': False,
                'message': _("ID de la catégorie requis.")
            })
        
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)
        
        # Vérifier s'il y a des inscriptions liées à cette catégorie
        from apps.competitions.models import CompetitionRegistration
        registrations_count = CompetitionRegistration.objects.filter(
            competition=competition,
            category=category
        ).count()
        
        if registrations_count > 0:
            return JsonResponse({
                'success': False,
                'message': _("Impossible de supprimer cette catégorie car {} inscription(s) y sont liées. Veuillez d'abord réassigner ou supprimer ces inscriptions.").format(registrations_count)
            })
        
        # Supprimer la catégorie
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