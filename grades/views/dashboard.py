"""
Module pour le tableau de bord des grades.
Fournit une vue d'ensemble des pratiquants et de leurs grades.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator

from competitions.models import Practitioner, Discipline
from grades.utils import get_user_club

@login_required
def grades_dashboard(request):
    """
    Tableau de bord principal pour la gestion des grades.
    Affiche une vue d'ensemble des pratiquants et de leurs grades actuels.
    """
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('dashboard:index')
    
    # Récupérer l'organisation associée au club
    organization = club.organization or club.as_organization
    if not organization:
        messages.error(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('dashboard:index')
    
    # Récupérer tous les pratiquants du club
    practitioners = Practitioner.objects.filter(organization=organization)
    
    # Filtrer par discipline si demandé
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        try:
            discipline = Discipline.objects.get(id=discipline_id)
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
    
    # Récupérer les disciplines du club
    disciplines = Discipline.objects.filter(
        is_active=True
    ).order_by('name')
    
    return render(request, 'grades/dashboard.html', {
        'practitioners': practitioners_page,
        'club': club,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
        'selected_grade_status': grade_status,
        'search_query': search_query,
    })