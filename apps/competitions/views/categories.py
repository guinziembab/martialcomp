"""
Vues pour la gestion des catégories de compétition - Version corrigée
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from ..models import Competition, CompetitionCategory, CompetitionType
from apps.grades.models import Grade


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
    
    # Récupérer les grades pour la discipline
    # TODO: Implémenter la récupération des grades si nécessaire
    grades = []  # Pour le moment, liste vide
    
    context = {
        'competition': competition,
        'categories': categories,
        'competition_types': competition_types,
        'grades': grades,
    }
    
    return render(request, 'competitions/categories/manage.html', context)


@login_required
@require_POST
def add_category(request, competition_id):
    """Ajouter une catégorie à une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions - pour l'instant autoriser tous les utilisateurs connectés
    # TODO: Ajouter le champ created_by au modèle Competition pour une vraie vérification
    pass
    
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
        
        # Gérer le genre - CORRECTION ICI
        gender = request.POST.get('gender', '').strip()
        # Convertir les valeurs du formulaire HTML vers les valeurs du modèle
        if gender == 'M':
            gender = 'male'
        elif gender == 'F':
            gender = 'female'
        elif gender == 'male' or gender == 'female':
            # Si déjà au bon format, garder tel quel
            gender = gender
        else:
            # Par défaut, catégorie mixte
            gender = 'mixed'
        
        # Récupérer les grades (AJOUT DES VARIABLES MANQUANTES)
        min_grade = request.POST.get('min_grade', '').strip()
        max_grade = request.POST.get('max_grade', '').strip()
        
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
            min_grade=min_grade if min_grade else '',  # Chaîne vide pour NOT NULL
            max_grade=max_grade if max_grade else ''   # Chaîne vide pour NOT NULL
        )
        
        return JsonResponse({
            'success': True,
            'message': _("Catégorie ajoutée avec succès."),
            'category_id': category.id
        })
        
    except Exception as e:
        # Log l'erreur pour le debugging
        import traceback
        print(f"Erreur lors de l'ajout de la catégorie: {str(e)}")
        print(traceback.format_exc())
        
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de l'ajout de la catégorie: {}").format(str(e))
        })


@login_required
@require_POST
def delete_category(request, competition_id):
    """Supprimer une catégorie d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions - pour l'instant autoriser tous les utilisateurs connectés
    # TODO: Ajouter le champ created_by au modèle Competition pour une vraie vérification
    pass
    
    # Vérifier que c'est une requête AJAX
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return redirect('competitions:competitions:detail', pk=competition_id)
    
    try:
        data = json.loads(request.body)
        category_id = data.get('category_id')
        
        if not category_id:
            return JsonResponse({
                'success': False,
                'message': _("ID de la catégorie requis.")
            })
        
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)
        category_name = category.name
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la suppression de la catégorie: {}").format(str(e))
        })
    
    # Supprimer la catégorie - directement via SQL pour éviter les problèmes de relations
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM competitions_competitioncategory WHERE id = %s", [category_id])
        
        return JsonResponse({
            'success': True,
            'message': _("Catégorie '{}' supprimée avec succès.").format(category_name)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de la suppression de la catégorie: {}").format(str(e))
        })


@login_required
def get_discipline_grades(request, competition_id):
    """Récupérer les grades disponibles pour la discipline d'une compétition"""
    competition = get_object_or_404(Competition, id=competition_id)
    
    try:
        # Récupérer les grades pour la discipline
        grades = Grade.objects.filter(discipline=competition.discipline).order_by('order')
        
        # Formatter les grades pour le JSON
        grades_data = []
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'name': grade.name,
                'color': grade.color if hasattr(grade, 'color') else None,
                'order': grade.order
            })
        
        return JsonResponse({
            'success': True,
            'grades': grades_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })