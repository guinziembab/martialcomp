from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from ..models import GradeCategory, Grade
import logging

# PHASE 2 SECURITY: Import helpers de filtrage par discipline
from apps.competitions.utils.permission_helpers import (
    get_user_disciplines,
    check_discipline_access
)

logger = logging.getLogger('discipline_isolation')


@login_required
@require_GET
def categories_by_discipline(request):
    """API pour récupérer les catégories d'une discipline.
    PHASE 2 SECURITY: Verifie l'acces a la discipline.
    """
    discipline_id = request.GET.get('discipline')
    if not discipline_id:
        return JsonResponse({'categories': []})

    # PHASE 2 SECURITY: Verifier l'acces a cette discipline
    user = request.user
    if not user.is_superuser:
        accessible_disciplines = get_user_disciplines(user)
        accessible_ids = list(accessible_disciplines.values_list('id', flat=True))
        try:
            if int(discipline_id) not in accessible_ids:
                logger.warning(f"categories_by_discipline API: User {user} denied")
                return JsonResponse({'categories': [], 'error': 'Access denied'}, status=403)
        except (ValueError, TypeError):
            return JsonResponse({'categories': []})

    categories = GradeCategory.objects.filter(
        discipline_id=discipline_id,
        is_active=True
    )

    data = {
        'categories': [
            {'id': cat.id, 'name': cat.name}
            for cat in categories.order_by('order', 'name')
        ]
    }
    return JsonResponse(data)


@login_required
@require_GET
def grades_by_disciplines(request):
    """API pour récupérer les grades par disciplines.
    PHASE 2 SECURITY: Filtre par disciplines accessibles.
    """
    discipline_ids = request.GET.getlist('disciplines[]') or \
        request.GET.getlist('disciplines')

    if not discipline_ids:
        return JsonResponse({'grades': []})

    try:
        discipline_ids = [int(did) for did in discipline_ids if did]
    except (ValueError, TypeError):
        return JsonResponse({'grades': [], 'error': 'Invalid IDs'}, status=400)

    # PHASE 2 SECURITY: Filtrer par disciplines accessibles
    user = request.user
    if not user.is_superuser:
        accessible_disciplines = get_user_disciplines(user)
        accessible_ids = set(accessible_disciplines.values_list('id', flat=True))
        # Filtrer pour ne garder que les disciplines accessibles
        discipline_ids = [did for did in discipline_ids if did in accessible_ids]
        if not discipline_ids:
            logger.warning(f"grades_by_disciplines: User {user} has no access")
            return JsonResponse({'grades': []})

    grades = Grade.objects.filter(
        discipline_id__in=discipline_ids,
        is_active=True
    ).select_related('discipline', 'category').order_by('discipline', 'level')
    
    # Formater les données pour le JavaScript
    data = {
        'grades': [
            {
                'id': grade.id,
                'name': grade.name,
                'discipline_id': grade.discipline.id,
                'discipline_name': grade.discipline.name,
                'category': grade.category.name if grade.category else '',
                'level': grade.level or 0,
                'color': grade.color or '',
                'color_code': grade.color_code or '',
                'description': getattr(grade, 'requirements_text', '') or ''
            }
            for grade in grades
        ]
    }
    
    return JsonResponse(data)