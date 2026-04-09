from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum, Case, When, IntegerField, F
from django.utils import timezone

from apps.competitions.models import (
    Competition, CompetitionCategory, CompetitionRegistration, 
    Match, JudgeAssignment
)
from apps.competitions.models.schedule import CompetitionSchedule, CategorySchedule, TatamiSchedule
from apps.competitions.utils.decorators import competition_management_permission_required
from apps.competitions.utils.competitions import get_competition_progress, get_competition_statistics


@login_required
@competition_management_permission_required
def management_dashboard(request, competition_id):
    """
    Tableau de bord pour la gestion d'une compétition spécifique.
    """
    try:
        return _management_dashboard_impl(request, competition_id)
    except Exception as e:
        import traceback
        from django.http import HttpResponse
        return HttpResponse(f"<pre>{e}\n\n{traceback.format_exc()}</pre>", status=500)


def _management_dashboard_impl(request, competition_id):
    competition = get_object_or_404(Competition, pk=competition_id)

    # Récupérer les statistiques de la compétition
    statistics = get_competition_statistics(competition)
    
    # Récupérer la progression de la compétition
    progress = get_competition_progress(competition)
    
    # Récupérer les catégories de la compétition
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    # Ajouter des statistiques Ã  chaque catégorie
    for category in categories:
        category.participants_count = CompetitionRegistration.objects.filter(
            categories=category, 
            is_competitor=True
        ).count()
        
        from apps.competitions.models.combat import Combat as CombatModel
        category.matches_count = CombatModel.objects.filter(
            poule__category=category
        ).count()
        category.completed_matches_count = CombatModel.objects.filter(
            poule__category=category,
            status='termine'
        ).count()
        
        # Calculer le pourcentage de progression
        if category.matches_count > 0:
            category.progress_percentage = int((category.completed_matches_count / category.matches_count) * 100)
        else:
            category.progress_percentage = 0
    
    # Récupérer les juges assignés Ã  cette compétition
    judges = JudgeAssignment.objects.filter(
        category__competition=competition
    ).select_related('user', 'category').order_by('category')
    
    # Récupérer le planning de la compétition
    try:
        schedule = CompetitionSchedule.objects.get(competition=competition)
        tatamis = TatamiSchedule.objects.filter(competition_schedule=schedule)
        category_schedules = CategorySchedule.objects.filter(
            competition_schedule=schedule
        ).select_related('category', 'tatami')
    except CompetitionSchedule.DoesNotExist:
        schedule = None
        tatamis = None
        category_schedules = None
    
    # Récupérer les derniers matchs terminés
    from apps.competitions.models.combat import Combat as CombatModel2
    recent_matches = CombatModel2.objects.filter(
        competition=competition,
        status='termine'
    ).order_by('-date_planifiee')[:5]

    # Récupérer les prochains combats
    upcoming_matches = CombatModel2.objects.filter(
        competition=competition,
        status='planifie'
    ).order_by('date_planifiee')[:5]
    
    context = {
        'competition': competition,
        'statistics': statistics,
        'stats': statistics,
        'progress': progress,
        'categories': categories,
        'judges': judges,
        'schedule': schedule,
        'tatamis': tatamis,
        'category_schedules': category_schedules,
        'recent_matches': recent_matches,
        'upcoming_matches': upcoming_matches,
        'today': timezone.now().date(),
    }
    
    return render(request, 'competitions/management/dashboard.html', context)


@login_required
@competition_management_permission_required
def competition_status_update(request, competition_id):
    """
    Mettre Ã  jour le statut d'une compétition.
    """
    if request.method != 'POST':
        return redirect('competitions:management:dashboard', competition_id=competition_id)
    
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Vérifier si l'utilisateur a les permissions nécessaires
    if not request.user.has_perm('competitions.change_competition_status', competition):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier le statut de cette compétition."))
        return redirect('competitions:management:dashboard', competition_id=competition_id)
    
    # Récupérer le nouveau statut
    new_status = request.POST.get('status')
    if new_status not in dict(Competition.STATUS_CHOICES):
        messages.error(request, _("Statut invalide."))
        return redirect('competitions:management:dashboard', competition_id=competition_id)
    
    # Mise Ã  jour du statut
    competition.status = new_status
    competition.save(update_fields=['status'])
    
    messages.success(request, _("Le statut de la compétition a été mis Ã  jour."))
    return redirect('competitions:management:dashboard', competition_id=competition_id)


@login_required
@competition_management_permission_required
def category_progress_update(request, competition_id, category_id):
    """
    Mettre Ã  jour la progression d'une catégorie.
    """
    if request.method != 'POST':
        return redirect('competitions:management:dashboard', competition_id=competition_id)
    
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition_id=competition_id)
    
    # Vérifier si l'utilisateur a les permissions nécessaires
    if not request.user.has_perm('competitions.change_category_status', category.competition):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier le statut de cette catégorie."))
        return redirect('competitions:management:dashboard', competition_id=competition_id)
    
    # Récupérer le nouveau statut
    new_status = request.POST.get('status')
    if new_status not in ['pending', 'in_progress', 'completed']:
        messages.error(request, _("Statut invalide."))
        return redirect('competitions:management:dashboard', competition_id=competition_id)
    
    # Mise Ã  jour du statut de la catégorie
    category.status = new_status
    category.save(update_fields=['status'])
    
    messages.success(request, _("Le statut de la catégorie a été mis Ã  jour."))
    return redirect('competitions:management:dashboard', competition_id=competition_id)


@login_required
@competition_management_permission_required
def quick_stats(request, competition_id):
    """
    Retourne des statistiques rapides pour le tableau de bord en AJAX.
    """
    from django.http import JsonResponse

    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Statistiques générales
    total_participants = CompetitionRegistration.objects.filter(
        competition=competition,
        is_competitor=True
    ).count()
    
    total_matches = Match.objects.filter(
        category__competition=competition
    ).count()
    
    completed_matches = Match.objects.filter(
        category__competition=competition,
        status='completed'
    ).count()
    
    total_categories = CompetitionCategory.objects.filter(
        competition=competition
    ).count()
    
    active_categories = CompetitionCategory.objects.filter(
        competition=competition,
        status='in_progress'
    ).count()
    
    # Progression globale
    if total_matches > 0:
        progress_percentage = int((completed_matches / total_matches) * 100)
    else:
        progress_percentage = 0
    
    # Récupérer le statut actuel
    status = competition.get_status_display()
    
    data = {
        'total_participants': total_participants,
        'total_matches': total_matches,
        'completed_matches': completed_matches,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'progress_percentage': progress_percentage,
        'status': status,
    }
    
    return JsonResponse(data)


@login_required
@competition_management_permission_required
def close_competition(request, competition_id):
    """
    Clôture une compétition et génère les résultats finaux.
    Accessible uniquement en POST.
    """
    from django.http import JsonResponse
    from apps.competitions.services import CompetitionClosureService

    competition = get_object_or_404(Competition, pk=competition_id)

    # Vérifier les permissions
    if not request.user.has_perm('competitions.change_competition_status', competition):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour clôturer cette compétition."))
        return redirect('competitions:management:dashboard', competition_id=competition_id)

    if request.method == 'GET':
        # Retourner les infos de pré-clôture (pour le modal)
        can_close, warnings = CompetitionClosureService.can_close(competition)

        return JsonResponse({
            'can_close': can_close,
            'warnings': [str(w) for w in warnings],
            'competition_status': competition.status,
            'competition_title': competition.title,
        })

    elif request.method == 'POST':
        # Effectuer la clôture
        success, result_messages = CompetitionClosureService.close_competition(
            competition, request.user
        )

        if success:
            messages.success(request, _("La compétition a été clôturée avec succès."))
            for msg in result_messages:
                messages.info(request, str(msg))
        else:
            messages.error(request, _("Impossible de clôturer la compétition."))
            for msg in result_messages:
                messages.warning(request, str(msg))

        return redirect('competitions:management:dashboard', competition_id=competition_id)

    return redirect('competitions:management:dashboard', competition_id=competition_id)


@login_required
@competition_management_permission_required
def close_competition_api(request, competition_id):
    """
    API pour obtenir les informations de clôture (JSON).
    """
    from django.http import JsonResponse
    from apps.competitions.services import CompetitionClosureService

    competition = get_object_or_404(Competition, pk=competition_id)

    can_close, warnings = CompetitionClosureService.can_close(competition)

    return JsonResponse({
        'can_close': can_close,
        'warnings': [str(w) for w in warnings],
        'competition_status': competition.status,
        'competition_title': competition.title,
    })

