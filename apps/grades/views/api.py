from django.core.exceptions import PermissionDenied
"""
API pour la gestion des grades dans le système.
Fournit des endpoints pour récupérer les grades par discipline.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q

import json
import logging

# Configurer le logger
logger = logging.getLogger(__name__)

# Import des modèles
from apps.competitions.models import Discipline

# Dictionnaire des grades par défaut pour chaque discipline
# Structure améliorée avec organisation par catégories
DEFAULT_GRADES = {
    'Karaté': {
        'Débutant': [
            {"name": "Ceinture Blanche", "color": "#FFFFFF", "level": 1},
            {"name": "Ceinture Jaune", "color": "#FFFF00", "level": 2},
            {"name": "Ceinture Orange", "color": "#FFA500", "level": 3},
        ],
        'Intermédiaire': [
            {"name": "Ceinture Verte", "color": "#008000", "level": 4},
            {"name": "Ceinture Bleue", "color": "#0000FF", "level": 5},
        ],
        'Avancé': [
            {"name": "Ceinture Marron", "color": "#A52A2A", "level": 6},
        ],
        'Expert': [
            {"name": "Ceinture Noire 1er Dan", "color": "#000000", "level": 7},
            {"name": "Ceinture Noire 2ème Dan", "color": "#000000", "level": 8},
        ]
    },
    'Judo': {
        'Débutant': [
            {"name": "Ceinture Blanche", "color": "#FFFFFF", "level": 1},
            {"name": "Ceinture Jaune", "color": "#FFFF00", "level": 2},
            {"name": "Ceinture Orange", "color": "#FFA500", "level": 3},
        ],
        'Intermédiaire': [
            {"name": "Ceinture Verte", "color": "#008000", "level": 4},
            {"name": "Ceinture Bleue", "color": "#0000FF", "level": 5},
        ],
        'Avancé': [
            {"name": "Ceinture Marron", "color": "#A52A2A", "level": 6},
        ],
        'Expert': [
            {"name": "Ceinture Noire 1er Dan", "color": "#000000", "level": 7},
        ]
    },
    'Taekwondo': {
        'Débutant': [
            {"name": "Ceinture Blanche", "color": "#FFFFFF", "level": 1},
            {"name": "Ceinture Jaune", "color": "#FFFF00", "level": 2},
        ],
        'Intermédiaire': [
            {"name": "Ceinture Verte", "color": "#008000", "level": 3},
            {"name": "Ceinture Bleue", "color": "#0000FF", "level": 4},
        ],
        'Avancé': [
            {"name": "Ceinture Rouge", "color": "#FF0000", "level": 5},
        ],
        'Expert': [
            {"name": "Ceinture Noire 1er Dan", "color": "#000000", "level": 6},
        ]
    },
    'Qwan Ki Do': {
        'Cap Jaune': [
            {"name": "1er Cap Jaune", "color": "#FFEB3B", "level": 1},
            {"name": "2ème Cap Jaune", "color": "#FFEB3B", "level": 2},
            {"name": "3ème Cap Jaune", "color": "#FFEB3B", "level": 3},
            {"name": "4ème Cap Jaune", "color": "#FFEB3B", "level": 4},
        ],
        'Cap Rouge': [
            {"name": "1er Cap Rouge", "color": "#F44336", "level": 5},
            {"name": "2ème Cap Rouge", "color": "#F44336", "level": 6},
            {"name": "3ème Cap Rouge", "color": "#F44336", "level": 7},
            {"name": "4ème Cap Rouge", "color": "#F44336", "level": 8},
        ],
        'Cap Blanc': [
            {"name": "1er Cap Blanc", "color": "#FFFFFF", "level": 9},
            {"name": "2ème Cap Blanc", "color": "#FFFFFF", "level": 10},
            {"name": "3ème Cap Blanc", "color": "#FFFFFF", "level": 11},
            {"name": "4ème Cap Blanc", "color": "#FFFFFF", "level": 12},
        ],
        'Cap Bleu': [
            {"name": "1er Cap Bleu", "color": "#2196F3", "level": 13},
            {"name": "2ème Cap Bleu", "color": "#2196F3", "level": 14},
            {"name": "3ème Cap Bleu", "color": "#2196F3", "level": 15},
            {"name": "4ème Cap Bleu", "color": "#2196F3", "level": 16},
            {"name": "Ã‰charpe Bleue", "color": "#2196F3", "level": 17},
        ],
        'Dang': [
            {"name": "1er Dang", "color": "#000000", "level": 18},
            {"name": "2ème Dang", "color": "#000000", "level": 19},
            {"name": "3ème Dang", "color": "#000000", "level": 20},
            {"name": "4ème Dang", "color": "#000000", "level": 21},
            {"name": "5ème Dang", "color": "#000000", "level": 22},
            {"name": "6ème Dang", "color": "#000000", "level": 23},
            {"name": "7ème Dang", "color": "#000000", "level": 24},
            {"name": "8ème Dang", "color": "#000000", "level": 25},
            {"name": "9ème Dang", "color": "#000000", "level": 26},
            {"name": "10ème Dang", "color": "#000000", "level": 27},
        ]
    },
    'default': {
        'Niveau 1': [
            {"name": "Débutant", "color": "#FFFFFF", "level": 1},
        ],
        'Niveau 2': [
            {"name": "Intermédiaire", "color": "#FFFF00", "level": 2},
        ],
        'Niveau 3': [
            {"name": "Avancé", "color": "#008000", "level": 3},
        ],
        'Niveau 4': [
            {"name": "Expert", "color": "#000000", "level": 4},
        ]
    }
}

# Grades Ã  utiliser en cas d'erreur critique
FALLBACK_GRADES = [
    {"id": -1, "name": "Débutant", "nom": "Débutant", "category": "Niveau 1", "color": "#FFFFFF", "level": 1},
    {"id": -2, "name": "Intermédiaire", "nom": "Intermédiaire", "category": "Niveau 2", "color": "#FFFF00", "level": 2},
    {"id": -3, "name": "Avancé", "nom": "Avancé", "category": "Niveau 3", "color": "#008000", "level": 3},
    {"id": -4, "name": "Expert", "nom": "Expert", "category": "Niveau 4", "color": "#000000", "level": 4}
]

from apps.grades.models import Grade, GradeCategory
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
def get_default_grades_for_discipline(discipline_name):
    """
    Récupère les grades par défaut pour une discipline donnée.
    
    Args:
        discipline_name (str): Nom de la discipline
        
    Returns:
        list: Liste des grades transformés au format attendu par l'API
    """
    result = []
    grade_id = -1
    
    # Récupérer la structure de grades de la discipline ou celle par défaut
    discipline_grades = DEFAULT_GRADES.get(discipline_name, DEFAULT_GRADES.get('default', {}))
    
    # Parcourir les catégories et grades
    for category_name, grades in discipline_grades.items():
        for grade in grades:
            # Créer une copie pour éviter de modifier le dictionnaire original
            grade_data = grade.copy()
            
            # Ajouter les champs supplémentaires
            grade_data.update({
                'id': grade_id,
                'nom': grade['name'],  # Ajouter le champ 'nom' comme alias de 'name'
                'discipline': discipline_name,
                'category': category_name,
                'description': grade.get('description', ''),
                'min_age': grade.get('min_age', None),
                'min_experience_months': grade.get('min_experience_months', None)
            })
            
            result.append(grade_data)
            grade_id -= 1  # Décrémenter pour avoir des IDs uniques négatifs
    
    # Trier par niveau et nom
    result.sort(key=lambda x: (x.get('level', 99), x.get('name', '')))
    return result


def get_grades_for_discipline(discipline):
    """
    Récupère les grades pour une discipline donnée.
    
    Args:
        discipline: Instance de la discipline
        
    Returns:
        list: Liste des grades pour cette discipline
    """
    # Récupérer les grades depuis la base de données
    grades = Grade.objects.filter(discipline=discipline).order_by('level')
    
    # Si aucun grade n'est trouvé, retourner une liste vide
    if not grades.exists():
        return []
    
    return grades


@login_required
@require_GET
def get_grades_by_disciplines(request):
    """
    Endpoint API pour récupérer les grades correspondant Ã  une ou plusieurs disciplines.
    Accepte Ã  la fois les requÃªtes GET et POST.
    
    Args:
        request: RequÃªte HTTP
        
    Returns:
        JsonResponse: Liste des grades pour les disciplines demandées
    """
    try:
        # Récupérer l'ID de discipline
        discipline_id = request.GET.get('discipline_id')
        
        # Si aucun ID de discipline n'est spécifié, essayer d'autres paramètres
        if not discipline_id:
            discipline_ids = request.GET.getlist('disciplines[]', [])
            if not discipline_ids:
                discipline_ids_str = request.GET.get('disciplines', '')
                if discipline_ids_str:
                    discipline_ids = discipline_ids_str.split(',')
        else:
            discipline_ids = [discipline_id]
            
        # Filtrer les valeurs vides
        discipline_ids = [d for d in discipline_ids if d]
        
        if not discipline_ids:
            return JsonResponse({'error': 'Aucune discipline spécifiée', 'grades': []}, status=400)
        
        grades_data = []
        
        # Récupérer les grades pour chaque discipline
        for discipline_id in discipline_ids:
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                
                # D'abord, essayer de récupérer les grades depuis la base de données
                db_grades = Grade.objects.filter(discipline=discipline).order_by('level')
                
                if db_grades.exists():
                    for grade in db_grades:
                        grades_data.append({
                            'id': grade.id,
                            'name': grade.name,
                            'nom': grade.name,  # Pour la compatibilité
                            'category': grade.category.name if grade.category else "",
                            'discipline': discipline.name,
                            'color': grade.color,
                            'color_code': grade.color_code if hasattr(grade, 'color_code') else grade.color,
                            'level': grade.level,
                            'description': grade.requirements if hasattr(grade, 'requirements') else "",
                            'min_age': grade.min_age,
                            'min_time_in_previous_grade': grade.min_time_in_previous_grade
                        })
                else:
                    # Si aucun grade n'est trouvé, utiliser les grades par défaut
                    default_grades = get_default_grades_for_discipline(discipline.name)
                    grades_data.extend(default_grades)
                    
            except Discipline.DoesNotExist:
                logger.warning(f"Discipline ID {discipline_id} non trouvée")
        
        # Si aucun grade n'a été trouvé après toutes les tentatives
        if not grades_data:
            grades_data = FALLBACK_GRADES
        
        # Trier les grades par niveau et nom
        grades_data.sort(key=lambda x: (x.get('level', 99), x.get('name', '')))
        
        return JsonResponse({'grades': grades_data})
        
    except Exception as e:
        logger.exception("Erreur dans get_grades_by_disciplines")
        return JsonResponse({'error': str(e), 'grades': []}, status=500)


@login_required
def get_grades_by_discipline(request, discipline_id):
    """
    Endpoint API pour récupérer les grades d'une discipline spécifique.
    
    Args:
        request: RequÃªte HTTP
        discipline_id: ID de la discipline
        
    Returns:
        JsonResponse: Liste des grades pour la discipline
    """
    try:
        # Récupérer la discipline
        discipline = get_object_or_404(Discipline, id=discipline_id)
        
        # Récupérer les grades depuis la base de données
        db_grades = Grade.objects.filter(discipline=discipline).order_by('level')
        
        grades_data = []
        
        if db_grades.exists():
            for grade in db_grades:
                grades_data.append({
                    'id': grade.id,
                    'name': grade.name,
                    'nom': grade.name,  # Pour la compatibilité
                    'category': grade.category.name if grade.category else "",
                    'discipline': discipline.name,
                    'color': grade.color,
                    'color_code': grade.color_code if hasattr(grade, 'color_code') else grade.color,
                    'level': grade.level,
                    'description': grade.requirements if hasattr(grade, 'requirements') else "",
                    'min_age': grade.min_age,
                    'min_time_in_previous_grade': grade.min_time_in_previous_grade
                })
        else:
            # Si aucun grade n'est trouvé, utiliser les grades par défaut
            default_grades = get_default_grades_for_discipline(discipline.name)
            grades_data.extend(default_grades)
        
        # Si aucun grade n'a été trouvé après toutes les tentatives
        if not grades_data:
            grades_data = FALLBACK_GRADES
        
        # Trier les grades par niveau et nom
        grades_data.sort(key=lambda x: (x.get('level', 99), x.get('name', '')))
        
        return JsonResponse({'grades': grades_data})
        
    except Discipline.DoesNotExist:
        return JsonResponse({'error': 'Discipline non trouvée', 'grades': []}, status=404)
    except Exception as e:
        logger.exception("Erreur dans get_grades_by_discipline")
        return JsonResponse({'error': str(e), 'grades': []}, status=500)


@login_required
@require_POST
def create_grade_for_discipline(request):
    """
    Endpoint API pour créer un nouveau grade pour une discipline.
    
    Args:
        request: RequÃªte HTTP avec un corps JSON contenant les informations du grade
        
    Returns:
        JsonResponse: Informations sur le grade créé
    """
    try:
        # Analyser le corps de la requÃªte
        data = json.loads(request.body)
        
        discipline_id = data.get('discipline_id')
        grade_name = data.get('name')
        category_name = data.get('category')
        
        if not all([discipline_id, grade_name]):
            return JsonResponse({
                'error': 'Informations de grade incomplètes. Discipline et nom sont requis.'
            }, status=400)
        
        # Récupérer la discipline
        discipline = get_object_or_404(Discipline, id=discipline_id)
        
        with transaction.atomic():
            # Récupérer ou créer la catégorie si spécifiée
            category = None
            if category_name:
                category, _ = GradeCategory.objects.get_or_create(
                    name=category_name,
                    discipline=discipline,
                    defaults={"order": 0}
                )
            
            # Vérifier si le grade existe déjÃ 
            existing_grade = Grade.objects.filter(
                name=grade_name,
                discipline=discipline
            ).first()
            
            if existing_grade:
                # Si le grade existe déjÃ , le retourner
                grade = existing_grade
                created = False
            else:
                # Déterminer le niveau et la couleur en fonction du nom et de la catégorie
                level = data.get('level', 0)
                color = data.get('color', '#000000')
                
                # Pour les grades Qwan Ki Do
                if 'Cap Jaune' in grade_name or (category and 'Jaune' in category_name):
                    color = '#FFEB3B'
                elif 'Cap Rouge' in grade_name or (category and 'Rouge' in category_name):
                    color = '#F44336'
                elif 'Cap Blanc' in grade_name or (category and 'Blanc' in category_name):
                    color = '#FFFFFF'
                elif 'Cap Bleu' in grade_name or (category and 'Bleu' in category_name):
                    color = '#2196F3'
                elif 'Dang' in grade_name or (category and 'Dang' in category_name):
                    color = '#000000'
                
                # Créer le grade
                grade = Grade.objects.create(
                    name=grade_name,
                    category=category,
                    discipline=discipline,
                    order=data.get('order', 0),
                    level=level,
                    color=color,
                    color_code=data.get('color_code', color),
                    description=data.get('description', ''),
                    min_age=data.get('min_age', 0),
                    min_time_in_previous_grade=data.get('min_time_in_previous_grade', 0),
                    is_active=True
                )
                created = True
            
            # Préparer la réponse
            grade_data = {
                'id': grade.id,
                'name': grade.name,
                'nom': grade.name,  # Pour la compatibilité
                'discipline': discipline.name,
                'category': category.name if category else "",
                'color': grade.color,
                'level': grade.level,
                'created': created
            }
            
            return JsonResponse({'grade': grade_data})
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Format JSON invalide'}, status=400)
    except Discipline.DoesNotExist:
        return JsonResponse({'error': 'Discipline non trouvée'}, status=404)
    except Exception as e:
        logger.exception("Erreur lors de la création du grade")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def search_grades(request):
    """
    Endpoint API pour rechercher des grades selon divers critères.
    
    Args:
        request: RequÃªte HTTP avec des paramètres de recherche
        
    Returns:
        JsonResponse: Liste des grades correspondant aux critères
    """
    try:
        # Récupérer les paramètres de recherche
        query = request.GET.get('q', '')
        discipline_id = request.GET.get('discipline')
        category_id = request.GET.get('category')
        
        # Construire la requête via l'isolation par discipline
        try:
            disciplines = get_organization_queryset(Discipline, request.user)
            grades = Grade.objects.filter(discipline__in=disciplines)
        except Exception:
            # Fallback : tous les grades si erreur
            grades = Grade.objects.all()
        
        if query:
            grades = grades.filter(name__icontains=query)
        
        if discipline_id:
            # Filtrer par discipline
            try:
                discipline = Discipline.objects.get(id=discipline_id)
                grades = grades.filter(discipline=discipline)
            except Discipline.DoesNotExist:
                return JsonResponse({'error': 'Discipline non trouvée'}, status=404)
        
        if category_id:
            # Filtrer par catégorie
            try:
                category = GradeCategory.objects.get(id=category_id)
                grades = grades.filter(category=category)
            except GradeCategory.DoesNotExist:
                return JsonResponse({'error': 'Catégorie non trouvée'}, status=404)
        
        # Limiter le nombre de résultats
        limit = int(request.GET.get('limit', 20))
        grades = grades[:limit]
        
        # Transformer en données JSON
        grades_data = []
        for grade in grades:
            grades_data.append({
                'id': grade.id,
                'name': grade.name,
                'category': grade.category.name if grade.category else "",
                'discipline': grade.discipline.name,
                'color': grade.color,
                'level': grade.level
            })
        
        return JsonResponse({'grades': grades_data})
        
    except Exception as e:
        logger.exception("Erreur dans search_grades")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_GET
def categories_by_discipline(request):
    """
    Endpoint API pour récupérer les catégories de grade d'une discipline.
    
    Args:
        request: RequÃªte HTTP avec paramètre discipline_id
        
    Returns:
        JsonResponse: Liste des catégories de grade
    """
    try:
        discipline_id = request.GET.get('discipline_id')
        
        if not discipline_id:
            return JsonResponse({'error': 'Discipline ID requis', 'categories': []}, status=400)
        
        # Récupérer la discipline
        discipline = get_object_or_404(Discipline, id=discipline_id)
        
        # Récupérer les catégories
        categories = GradeCategory.objects.filter(discipline=discipline).order_by('order')
        
        categories_data = []
        for category in categories:
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'order': category.order,
                'discipline_id': discipline.id,
                'discipline_name': discipline.name
            })
        
        return JsonResponse({'categories': categories_data})
    
    except Discipline.DoesNotExist:
        return JsonResponse({'error': 'Discipline non trouvée', 'categories': []}, status=404)
    except Exception as e:
        logger.exception("Erreur dans categories_by_discipline")
        return JsonResponse({'error': str(e), 'categories': []}, status=500)

