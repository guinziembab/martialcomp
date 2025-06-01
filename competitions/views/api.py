from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_GET
from django.contrib.admin.views.decorators import staff_member_required

from ..models import (
    Discipline, CompetitionType, Competition
)

# Import des modèles de grades depuis l'application grades
try:
    from grades.models import Grade, GradeCategory, GradingSystem
    GradeSystem = GradingSystem  # Alias pour compatibilité
except ImportError:
    Grade = None
    GradeCategory = None
    GradingSystem = None
    GradeSystem = None



# ======== API pour les types de compétition ========
# Fonction unique pour récupérer les types de compétition par discipline
@login_required
@require_GET
def get_competition_types_by_discipline(request, discipline_id):
    """Récupère les types de compétition pour une discipline donnée."""
    try:
        discipline = get_object_or_404(Discipline, pk=discipline_id)
        competition_types = CompetitionType.objects.filter(discipline=discipline)
        
        # Récupérer l'ID d'une compétition existante si fourni
        competition_id = request.GET.get('competition')
        selected_types = []
        
        if competition_id:
            try:
                competition = Competition.objects.get(pk=competition_id)
                selected_types = list(competition.competition_types.values_list('id', flat=True))
            except Competition.DoesNotExist:
                pass
        
        # Sérialisation en JSON avec toutes les informations nécessaires
        data = [
            {
                'id': ct.id,
                'name': ct.name,
                'description': getattr(ct, 'description', ''),  # Utiliser getattr pour éviter les erreurs si l'attribut n'existe pas
                'team_based': getattr(ct, 'team_based', False),
                'min_team_size': getattr(ct, 'min_team_size', None),
                'max_team_size': getattr(ct, 'max_team_size', None),
                'weight_category': getattr(ct, 'weight_category', False),
                'selected': ct.id in selected_types
            }
            for ct in competition_types
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        # Journaliser l'erreur pour le débogage
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des types de compétition: {str(e)}")
        
        # Retourner une réponse d'erreur explicite
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la récupération des types de compétition',
            'details': str(e)
        }, status=500)


# ======== Alias pour la compatibilité avec le code existant ========
# Ces fonctions appellent simplement la fonction principale pour assurer la compatibilité
@login_required
@require_GET
def competition_types_by_discipline(request, discipline_id):
    return get_competition_types_by_discipline(request, discipline_id)


@login_required
@require_GET
def get_competition_types(request):
    discipline_id = request.GET.get('discipline')
    if not discipline_id:
        return JsonResponse([], safe=False)
    
    # Rediriger vers la fonction principale
    response = get_competition_types_by_discipline(request, discipline_id)
    return response


# ======== API pour les systèmes de grades ========
@login_required
@require_GET
def get_grade_systems_by_discipline(request, discipline_id):
    """Récupère les systèmes de grades pour une discipline donnée."""
    try:
        discipline = get_object_or_404(Discipline, pk=discipline_id)
        systems = GradeSystem.objects.filter(discipline=discipline)
        
        # Sérialisation en JSON
        data = [
            {
                'id': system.id,
                'name': system.name,
                'description': system.description,
                'is_default': system.is_default
            }
            for system in systems
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des systèmes de grades: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la récupération des systèmes de grades',
            'details': str(e)
        }, status=500)


@login_required
@require_GET
def get_categories_by_system(request, system_id):
    """Récupère les catégories de grades pour un système donné."""
    try:
        system = get_object_or_404(GradeSystem, pk=system_id)
        categories = GradeCategory.objects.filter(system=system).order_by('order')
        
        # Sérialisation en JSON
        data = [
            {
                'id': category.id,
                'name': category.name,
                'order': category.order,
                'color_hex': category.color_hex
            }
            for category in categories
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des catégories de grades: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la récupération des catégories de grades',
            'details': str(e)
        }, status=500)


@login_required
@require_GET
def get_grades_by_category(request, category_id):
    """Récupère les grades pour une catégorie donnée."""
    try:
        category = get_object_or_404(GradeCategory, pk=category_id)
        grades = Grade.objects.filter(category=category).order_by('order')
        
        # Sérialisation en JSON
        data = [
            {
                'id': grade.id,
                'name': grade.name,
                'level': grade.level,
                'order': grade.order,
                'color': grade.color,
                'description': grade.description,
                'accessible_to_clubs': grade.accessible_to_clubs
            }
            for grade in grades
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des grades: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la récupération des grades',
            'details': str(e)
        }, status=500)


@login_required
@require_GET
def get_grades_by_discipline(request, discipline_id):
    """Récupère tous les grades disponibles pour une discipline donnée."""
    try:
        discipline = get_object_or_404(Discipline, pk=discipline_id)
        
        # Récupérer le système par défaut, ou le premier si aucun n'est par défaut
        system = GradeSystem.objects.filter(discipline=discipline, is_default=True).first()
        if not system:
            system = GradeSystem.objects.filter(discipline=discipline).first()
        
        if not system:
            return JsonResponse({
                'system': None,
                'grades': []
            })
        
        # Récupérer tous les grades pour ce système
        grades = Grade.objects.filter(
            category__system=system,
            accessible_to_clubs=True
        ).select_related('category').order_by('category__order', 'order')
        
        # Sérialisation en JSON
        grades_data = [
            {
                'id': grade.id,
                'name': grade.name,
                'category': grade.category.name,
                'color': grade.color,
                'level': grade.level
            }
            for grade in grades
        ]
        
        return JsonResponse({
            'system': {
                'id': system.id,
                'name': system.name
            },
            'grades': grades_data
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des grades par discipline: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la récupération des grades',
            'details': str(e)
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def import_grades(request):
    """Importe des grades à partir de données JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
    try:
        import json
        from django.db import transaction
        
        # Récupérer et valider les données JSON
        data = json.loads(request.body)
        discipline_id = data.get('discipline_id')
        grades_data = data.get('grades_data')
        
        if not discipline_id or not grades_data:
            return JsonResponse({'error': 'Données incomplètes'}, status=400)
        
        discipline = get_object_or_404(Discipline, pk=discipline_id)
        
        # Importer les données dans une transaction
        with transaction.atomic():
            for system_name, categories_data in grades_data.items():
                # Créer ou récupérer le système
                system, created = GradeSystem.objects.get_or_create(
                    name=system_name,
                    discipline=discipline,
                    defaults={'description': f"Système de grades importé pour {discipline.name}"}
                )
                
                # Créer les catégories et grades
                for category_name, grades_list in categories_data.items():
                    category, _ = GradeCategory.objects.get_or_create(
                        name=category_name,
                        system=system,
                        defaults={'order': 0}
                    )
                    
                    # Créer les grades
                    for i, grade_name in enumerate(grades_list, 1):
                        Grade.objects.get_or_create(
                            name=grade_name,
                            category=category,
                            defaults={
                                'level': i,
                                'order': i,
                                'accessible_to_clubs': True
                            }
                        )
        
        return JsonResponse({'success': True, 'message': 'Importation réussie'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format JSON invalide'}, status=400)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de l'importation des grades: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de l\'importation',
            'details': str(e)
        }, status=500)


@login_required
@require_GET
def search_grades(request):
    """Recherche des grades selon divers critères."""
    try:
        # Paramètres de recherche
        discipline_id = request.GET.get('discipline')
        system_id = request.GET.get('system')
        category_id = request.GET.get('category')
        query = request.GET.get('q', '')
        
        # Construire la requête de base
        grades = Grade.objects.select_related('category__system__discipline')
        
        # Appliquer les filtres
        if discipline_id:
            grades = grades.filter(category__system__discipline_id=discipline_id)
        
        if system_id:
            grades = grades.filter(category__system_id=system_id)
        
        if category_id:
            grades = grades.filter(category_id=category_id)
        
        if query:
            grades = grades.filter(name__icontains=query)
        
        # Limiter le nombre de résultats
        grades = grades[:50]
        
        # Sérialisation en JSON
        data = [
            {
                'id': grade.id,
                'name': grade.name,
                'category': grade.category.name,
                'system': grade.category.system.name,
                'discipline': grade.category.system.discipline.name,
                'color': grade.color
            }
            for grade in grades
        ]
        
        return JsonResponse(data, safe=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la recherche de grades: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la recherche',
            'details': str(e)
        }, status=500)
        

@staff_member_required
def grade_systems(request):
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        systems = GradeSystem.objects.filter(discipline_id=discipline_id)
        return JsonResponse([{'id': system.id, 'name': system.name} for system in systems], safe=False)
    return JsonResponse([], safe=False)

@staff_member_required
def grade_categories(request):
    system_id = request.GET.get('system')
    if system_id:
        categories = GradeCategory.objects.filter(system_id=system_id)
        return JsonResponse([{'id': category.id, 'name': category.name} for category in categories], safe=False)
    return JsonResponse([], safe=False)


@login_required
@require_GET
def get_grades_for_disciplines(request):
    """Récupère les grades de l'application grades pour les disciplines sélectionnées."""
    try:
        # Import conditionnel du module grades
        try:
            from grades.models import Grade as GradesGrade
        except ImportError:
            return JsonResponse({'error': 'Module grades non disponible'}, status=404)
        
        # Récupérer les IDs des disciplines depuis les paramètres GET
        discipline_ids = request.GET.getlist('disciplines[]')
        
        if not discipline_ids:
            return JsonResponse([], safe=False)
        
        # Récupérer les disciplines
        disciplines = Discipline.objects.filter(id__in=discipline_ids, is_active=True)
        
        # Récupérer les grades pour ces disciplines
        grades = GradesGrade.objects.filter(
            discipline__in=disciplines,
            is_active=True
        ).select_related('discipline').order_by('discipline__name', 'level')
        
        # Sérialisation en JSON
        data = [
            {
                'id': grade.id,
                'name': grade.name,
                'discipline_id': grade.discipline.id,
                'discipline_name': grade.discipline.name,
                'level': getattr(grade, 'level', 0),
                'color': getattr(grade, 'color', ''),
                'description': getattr(grade, 'requirements_text', '')
            }
            for grade in grades
        ]
        
        return JsonResponse({'grades': data}, safe=False)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la récupération des grades pour disciplines: {str(e)}")
        
        return JsonResponse({
            'error': 'Une erreur est survenue lors de la récupération des grades',
            'details': str(e)
        }, status=500)

