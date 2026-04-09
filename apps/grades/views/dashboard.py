from django.core.exceptions import PermissionDenied
"""
Module pour le tableau de bord des grades.
Fournit une vue d'ensemble des pratiquants et de leurs grades.
PHASE 2 SECURITY: Filtrage par disciplines accessibles.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
import logging

from apps.competitions.models import Practitioner, Discipline
from apps.grades.utils_module import get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# PHASE 2 SECURITY: Import helpers de filtrage par discipline
from apps.competitions.utils.permission_helpers import (
    get_user_disciplines,
    check_discipline_access
)

logger = logging.getLogger('discipline_isolation')

@login_required
def grades_dashboard(request):
    """
    Tableau de bord principal pour la gestion des grades.
    Affiche une vue d'ensemble des pratiquants et de leurs grades actuels.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer l'organisation associée au club
    # Si club est déjà une Organization, l'utiliser directement
    if hasattr(club, '__class__') and club.__class__.__name__ == 'Organization':
        organization = club
    else:
        # Sinon, récupérer l'organisation du club
        organization = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
    
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer tous les pratiquants du club
    practitioners = Practitioner.objects.filter(organization=organization)
    
    # Filtrer par discipline si demande
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        try:
            discipline = Discipline.objects.get(id=discipline_id)
            # PHASE 2 SECURITY: Verifier l'acces a cette discipline
            if not request.user.is_superuser:
                if not check_discipline_access(request.user, discipline):
                    logger.warning(f"grades_dashboard: User {request.user} denied access to discipline {discipline_id}")
                    discipline_id = None  # Ignorer le filtre discipline
                else:
                    practitioners = practitioners.filter(disciplines=discipline)
            else:
                practitioners = practitioners.filter(disciplines=discipline)
        except Discipline.DoesNotExist:
            pass
    
    # Filtrer par statut si demandé
    grade_status = request.GET.get('grade_status')
    if grade_status:
        if grade_status == 'with_grade':
            practitioners = practitioners.exclude(grade=None)
        elif grade_status == 'without_grade':
            practitioners = practitioners.filter(grade=None)
    
    # Filtrer par nom si recherche
    search_query = request.GET.get('q')
    if search_query:
        practitioners = practitioners.filter(
            Q(first_name__icontains=search_query) | 
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(practitioners.order_by('last_name', 'first_name'), 20)  # 20 pratiquants par page
    page = request.GET.get('page')
    practitioners_page = paginator.get_page(page)
    
    # Récupérer les disciplines accessibles Ã  l'utilisateur
    # PHASE 2 SECURITY: Utilise get_user_disciplines (import en haut du fichier)
    disciplines = get_user_disciplines(request.user).order_by('name')
    
    return render(request, 'grades/dashboard.html', {
        'practitioners': practitioners_page,
        'club': club,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
        'selected_grade_status': grade_status,
        'search_query': search_query,
    })

