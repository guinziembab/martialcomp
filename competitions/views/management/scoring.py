from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Avg, Sum, Max, Min, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db import transaction

from competitions.models import (
    Competition, CompetitionCategory, Match, CompetitionRegistration,
    JudgeAssignment
)
from competitions.models.technical_scoring import (
    ScoringCriterion, JudgeSubmissionStatus, ScoringConfiguration,
    CompetitionRanking, TechnicalPerformance, TechnicalScore
)
from competitions.utils.decorators import competition_management_permission_required
from competitions.forms.scoring import (
    ScoringCriterionForm, ScoringConfigurationForm,
    TechnicalPerformanceForm, ScoringForm
)


@login_required
@competition_management_permission_required
def scoring_dashboard(request, competition_id):
    """
    Tableau de bord du système de notation pour une compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer les catégories de la compétition
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    # Ajouter des statistiques à chaque catégorie
    for category in categories:
        # Nombre de critères de notation
        category.scoring_criteria_count = ScoringCriterion.objects.filter(
            category=category
        ).count()
        
        # Nombre de performances
        category.performances_count = TechnicalPerformance.objects.filter(
            category=category
        ).count()
        
        # Nombre de performances terminées
        category.completed_performances_count = TechnicalPerformance.objects.filter(
            category=category,
            status='completed'
        ).count()
        
        # Progression
        if category.performances_count > 0:
            category.scoring_progress = int((category.completed_performances_count / category.performances_count) * 100)
        else:
            category.scoring_progress = 0
    
    # Récupérer les juges assignés
    judges = JudgeAssignment.objects.filter(
        category__competition=competition,
        assignment_type__in=['technical_judge', 'chief_judge']
    ).select_related('user', 'category')
    
    # Récupérer les performances récentes
    recent_performances = TechnicalPerformance.objects.filter(
        category__competition=competition
    ).select_related('practitioner', 'category').order_by('-end_time')[:5]
    
    context = {
        'competition': competition,
        'categories': categories,
        'judges': judges,
        'recent_performances': recent_performances,
    }
    
    return render(request, 'competitions/management/scoring_dashboard.html', context)


@login_required
@competition_management_permission_required
def category_scoring_setup(request, competition_id, category_id):
    """
    Configure le système de notation pour une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer la configuration de notation existante
    
    try:
        scoring_config = ScoringConfiguration.objects.get(category=category)
    except ScoringConfiguration.DoesNotExist:
        scoring_config = None
    
    if request.method == 'POST':
        config_form = ScoringConfigurationForm(request.POST, instance=scoring_config)
        if config_form.is_valid():
            config = config_form.save(commit=False)
            config.category = category
            config.save()
            
            messages.success(request, _("La configuration de notation a été mise à jour."))
            return redirect('competitions:management:category_scoring_setup', 
                          competition_id=competition_id, 
                          category_id=category_id)
    else:
        config_form = ScoringConfigurationForm(instance=scoring_config)
    
    # Récupérer les critères de notation
    criteria = ScoringCriterion.objects.filter(category=category).order_by('order')
    
    context = {
        'competition': competition,
        'category': category,
        'scoring_config': scoring_config,
        'config_form': config_form,
        'criteria': criteria,
    }
    
    return render(request, 'competitions/management/category_scoring_setup.html', context)


@login_required
@competition_management_permission_required
def add_scoring_criterion(request, competition_id, category_id):
    """
    Ajoute un critère de notation pour une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    if request.method == 'POST':
        form = ScoringCriterionForm(request.POST)
        if form.is_valid():
            criterion = form.save(commit=False)
            criterion.category = category
            
            # Déterminer l'ordre si non spécifié
            if not criterion.order:
                # Prendre le dernier ordre + 1
                last_order = ScoringCriterion.objects.filter(
                    category=category
                ).order_by('-order').values_list('order', flat=True).first() or 0
                criterion.order = last_order + 1
            
            criterion.save()
            
            messages.success(request, _("Le critère de notation a été ajouté."))
            return redirect('competitions:management:category_scoring_setup', 
                          competition_id=competition_id, 
                          category_id=category_id)
    else:
        form = ScoringCriterionForm()
    
    context = {
        'competition': competition,
        'category': category,
        'form': form,
    }
    
    return render(request, 'competitions/management/add_scoring_criterion.html', context)


@login_required
@competition_management_permission_required
def edit_scoring_criterion(request, competition_id, criterion_id):
    """
    Modifie un critère de notation.
    """
    # Récupérer la compétition et le critère
    competition = get_object_or_404(Competition, pk=competition_id)
    criterion = get_object_or_404(
        ScoringCriterion, 
        pk=criterion_id, 
        category__competition=competition
    )
    
    if request.method == 'POST':
        form = ScoringCriterionForm(request.POST, instance=criterion)
        if form.is_valid():
            form.save()
            
            messages.success(request, _("Le critère de notation a été mis à jour."))
            return redirect('competitions:management:category_scoring_setup', 
                          competition_id=competition_id, 
                          category_id=criterion.category.id)
    else:
        form = ScoringCriterionForm(instance=criterion)
    
    context = {
        'competition': competition,
        'category': criterion.category,
        'criterion': criterion,
        'form': form,
    }
    
    return render(request, 'competitions/management/edit_scoring_criterion.html', context)


@login_required
@competition_management_permission_required
@require_POST
def delete_scoring_criterion(request, competition_id, criterion_id):
    """
    Supprime un critère de notation.
    """
    # Récupérer la compétition et le critère
    competition = get_object_or_404(Competition, pk=competition_id)
    criterion = get_object_or_404(
        ScoringCriterion, 
        pk=criterion_id, 
        category__competition=competition
    )
    
    category_id = criterion.category.id
    
    # Vérifier si des scores existent pour ce critère
    scores_exist = TechnicalScore.objects.filter(criterion=criterion).exists()
    
    if scores_exist:
        messages.error(request, _("Impossible de supprimer ce critère car des scores existent déjà."))
    else:
        criterion.delete()
        messages.success(request, _("Le critère de notation a été supprimé."))
    
    return redirect('competitions:management:category_scoring_setup', 
                  competition_id=competition_id, 
                  category_id=category_id)


@login_required
@competition_management_permission_required
def reorder_scoring_criteria(request, competition_id, category_id):
    """
    Réorganise l'ordre des critères de notation.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    if request.method == 'POST':
        # Récupérer les données JSON
        import json
        try:
            data = json.loads(request.body)
            criteria_orders = data.get('criteriaOrders', [])
            
            with transaction.atomic():
                for item in criteria_orders:
                    criterion_id = item.get('id')
                    new_order = item.get('order')
                    
                    if criterion_id and new_order is not None:
                        ScoringCriterion.objects.filter(
                            id=criterion_id,
                            category=category
                        ).update(order=new_order)
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # Si méthode GET, afficher la page de réorganisation
    criteria = ScoringCriterion.objects.filter(
        category=category
    ).order_by('order')
    
    context = {
        'competition': competition,
        'category': category,
        'criteria': criteria,
    }
    
    return render(request, 'competitions/management/reorder_criteria.html', context)


@login_required
@competition_management_permission_required
def manage_performances(request, competition_id, category_id):
    """
    Gère les performances pour une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer les performances existantes
    performances = TechnicalPerformance.objects.filter(
        category=category
    ).select_related('practitioner').order_by('performance_order')
    
    # Récupérer les participants inscrits qui n'ont pas encore de performance
    participants = CompetitionRegistration.objects.filter(
        competition=competition,
        categories=category,
        is_competitor=True,
        status='approved'
    ).select_related('practitioner').exclude(
        practitioner__id__in=performances.values_list('practitioner__id', flat=True)
    )
    
    context = {
        'competition': competition,
        'category': category,
        'performances': performances,
        'participants': participants,
    }
    
    return render(request, 'competitions/management/manage_performances.html', context)


@login_required
@competition_management_permission_required
def add_performance(request, competition_id, category_id):
    """
    Ajoute une performance pour un participant.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    if request.method == 'POST':
        form = TechnicalPerformanceForm(request.POST, competition=competition, category=category)
        if form.is_valid():
            performance = form.save(commit=False)
            performance.competition = competition
            performance.category = category
            
            # Déterminer l'ordre si non spécifié
            if not performance.performance_order:
                # Prendre le dernier ordre + 1
                last_order = TechnicalPerformance.objects.filter(
                    category=category
                ).order_by('-performance_order').values_list('performance_order', flat=True).first() or 0
                performance.performance_order = last_order + 1
            
            performance.save()
            
            messages.success(request, _("La performance a été ajoutée."))
            return redirect('competitions:management:manage_performances', 
                          competition_id=competition_id, 
                          category_id=category_id)
    else:
        form = TechnicalPerformanceForm(competition=competition, category=category)
    
    context = {
        'competition': competition,
        'category': category,
        'form': form,
    }
    
    return render(request, 'competitions/management/add_performance.html', context)


@login_required
@competition_management_permission_required
def edit_performance(request, competition_id, performance_id):
    """
    Modifie une performance.
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition
    )
    
    if request.method == 'POST':
        form = TechnicalPerformanceForm(
            request.POST, 
            instance=performance, 
            competition=competition, 
            category=performance.category
        )
        if form.is_valid():
            form.save()
            
            messages.success(request, _("La performance a été mise à jour."))
            return redirect('competitions:management:manage_performances', 
                          competition_id=competition_id, 
                          category_id=performance.category.id)
    else:
        form = TechnicalPerformanceForm(
            instance=performance, 
            competition=competition, 
            category=performance.category
        )
    
    context = {
        'competition': competition,
        'category': performance.category,
        'performance': performance,
        'form': form,
    }
    
    return render(request, 'competitions/management/edit_performance.html', context)


@login_required
@competition_management_permission_required
@require_POST
def delete_performance(request, competition_id, performance_id):
    """
    Supprime une performance.
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition
    )
    
    category_id = performance.category.id
    
    # Vérifier si des scores existent pour cette performance
    scores_exist = TechnicalScore.objects.filter(performance=performance).exists()
    
    if scores_exist:
        messages.error(request, _("Impossible de supprimer cette performance car des scores existent déjà."))
    else:
        performance.delete()
        messages.success(request, _("La performance a été supprimée."))
    
    return redirect('competitions:management:manage_performances', 
                  competition_id=competition_id, 
                  category_id=category_id)


@login_required
@competition_management_permission_required
@require_POST
def start_performance(request, competition_id, performance_id):
    """
    Démarre une performance (pour le chronométrage).
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition
    )
    
    # Démarrer la performance
    performance.start_performance()
    
    messages.success(request, _("La performance a démarré."))
    
    # Redirection selon le paramètre next
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect('competitions:management:manage_performances', 
                  competition_id=competition_id, 
                  category_id=performance.category.id)


@login_required
@competition_management_permission_required
@require_POST
def end_performance(request, competition_id, performance_id):
    """
    Termine une performance (pour le chronométrage).
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition,
        status='in_progress'
    )
    
    # Terminer la performance
    performance.end_performance()
    
    messages.success(request, _("La performance est terminée."))
    
    # Redirection selon le paramètre next
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect('competitions:management:manage_performances', 
                  competition_id=competition_id, 
                  category_id=performance.category.id)


@login_required
@competition_management_permission_required
def reorder_performances(request, competition_id, category_id):
    """
    Réorganise l'ordre des performances.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    if request.method == 'POST':
        # Récupérer les données JSON
        import json
        try:
            data = json.loads(request.body)
            performance_orders = data.get('performanceOrders', [])
            
            with transaction.atomic():
                for item in performance_orders:
                    performance_id = item.get('id')
                    new_order = item.get('order')
                    
                    if performance_id and new_order is not None:
                        TechnicalPerformance.objects.filter(
                            id=performance_id,
                            category=category
                        ).update(performance_order=new_order)
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    # Si méthode GET, afficher la page de réorganisation
    performances = TechnicalPerformance.objects.filter(
        category=category
    ).select_related('practitioner').order_by('performance_order')
    
    context = {
        'competition': competition,
        'category': category,
        'performances': performances,
    }
    
    return render(request, 'competitions/management/reorder_performances.html', context)


@login_required
@competition_management_permission_required
def performance_scores(request, competition_id, performance_id):
    """
    Affiche les scores d'une performance.
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition
    )
    
    # Récupérer les scores par juge et par critère
    scores = TechnicalScore.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Organiser les scores par juge et par critère
    judges = {}
    criteria = ScoringCriterion.objects.filter(
        category=performance.category
    ).order_by('order')
    
    for score in scores:
        judge_id = score.judge.id
        criterion_id = score.criterion.id
        
        if judge_id not in judges:
            judges[judge_id] = {
                'name': f"{score.judge.first_name} {score.judge.last_name}",
                'scores': {}
            }
        
        judges[judge_id]['scores'][criterion_id] = score.value
    
    context = {
        'competition': competition,
        'performance': performance,
        'category': performance.category,
        'criteria': criteria,
        'judges': judges,
        'scores': scores,
    }
    
    return render(request, 'competitions/management/performance_scores.html', context)


@login_required
@competition_management_permission_required
def add_score(request, competition_id, performance_id):
    """
    Ajoute un score pour une performance (pour les administrateurs).
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition
    )
    
    if request.method == 'POST':
        form = ScoringForm(request.POST, performance=performance)
        if form.is_valid():
            judge = form.cleaned_data['judge']
            criterion = form.cleaned_data['criterion']
            value = form.cleaned_data['value']
            
            # Vérifier si un score existe déjà
            try:
                score = TechnicalScore.objects.get(
                    performance=performance,
                    judge=judge,
                    criterion=criterion
                )
                score.value = value
                score.save()
                messages.success(request, _("Le score a été mis à jour."))
            except TechnicalScore.DoesNotExist:
                # Créer un nouveau score
                TechnicalScore.objects.create(
                    performance=performance,
                    judge=judge,
                    criterion=criterion,
                    value=value
                )
                messages.success(request, _("Le score a été ajouté."))
            
            return redirect('competitions:management:performance_scores', 
                          competition_id=competition_id, 
                          performance_id=performance_id)
    else:
        form = ScoringForm(performance=performance)
    
    context = {
        'competition': competition,
        'performance': performance,
        'category': performance.category,
        'form': form,
    }
    
    return render(request, 'competitions/management/add_score.html', context)


@login_required
@competition_management_permission_required
@require_POST
def delete_score(request, competition_id, score_id):
    """
    Supprime un score.
    """
    # Récupérer la compétition et le score
    competition = get_object_or_404(Competition, pk=competition_id)
    score = get_object_or_404(
        TechnicalScore, 
        pk=score_id, 
        performance__competition=competition
    )
    
    performance_id = score.performance.id
    
    # Supprimer le score
    score.delete()
    
    messages.success(request, _("Le score a été supprimé."))
    return redirect('competitions:management:performance_scores', 
                  competition_id=competition_id, 
                  performance_id=performance_id)


@login_required
@competition_management_permission_required
def calculate_results(request, competition_id, category_id):
    """
    Calcule les résultats pour une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Calcul en masse des scores finaux
    performances = TechnicalPerformance.objects.filter(
        category=category,
        status='completed'
    ).select_related('practitioner')
    
    # Récupérer la configuration de notation
    try:
        config = ScoringConfiguration.objects.get(category=category)
        exclude_extreme_scores = config.exclude_extreme_scores
        allow_ties = config.allow_ties
    except ScoringConfiguration.DoesNotExist:
        exclude_extreme_scores = False
        allow_ties = True
    
    # Supprimer les classements existants
    CompetitionRanking.objects.filter(
        competition=competition,
        category=category
    ).delete()
    
    # Recalculer les scores finaux pour chaque performance
    for performance in performances:
        # Calcul du score final
        final_score = performance.calculate_final_score()
        
        # Compter les premières places (applicable si plusieurs juges)
        first_places = 0
        
        # Créer le classement (sans rang pour l'instant)
        CompetitionRanking.objects.create(
            competition=competition,
            category=category,
            practitioner=performance.practitioner,
            rank=0,  # Sera mis à jour plus tard
            final_score=final_score,
            first_places=first_places
        )
    
    # Attribuer les rangs
    rankings = CompetitionRanking.objects.filter(
        competition=competition,
        category=category
    ).order_by('-final_score', '-first_places')
    
    current_rank = 1
    previous_score = None
    previous_first_places = None
    for i, ranking in enumerate(rankings):
        if i > 0 and ranking.final_score == previous_score and ranking.first_places == previous_first_places:
            # Ex-aequo
            if not allow_ties and current_rank == 3:
                # Si les ex-aequo ne sont pas autorisés pour la 3e place
                ranking.rank = 4
            else:
                ranking.rank = current_rank
            ranking.is_tie = True
        else:
            ranking.rank = current_rank
            ranking.is_tie = False
            current_rank += 1
        
        ranking.save()
        previous_score = ranking.final_score
        previous_first_places = ranking.first_places
    
    messages.success(request, _("Les résultats ont été calculés avec succès."))
    return redirect('competitions:management:category_results', 
                   competition_id=competition_id, 
                   category_id=category_id)


@login_required
@competition_management_permission_required
def export_results(request, competition_id, category_id):
    """
    Exporte les résultats d'une catégorie au format CSV.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer les résultats
    rankings = CompetitionRanking.objects.filter(
        competition=competition,
        category=category
    ).select_related('practitioner').order_by('rank')
    
    # Exporter en CSV
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{category.name}_results.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        _('Rang'), _('Nom'), _('Prénom'), _('Club'), 
        _('Score final'), _('Ex-aequo')
    ])
    
    for ranking in rankings:
        p = ranking.practitioner
        writer.writerow([
            ranking.rank,
            p.last_name,
            p.first_name,
            p.club.name if p.club else "",
            ranking.final_score,
            _('Oui') if ranking.is_tie else _('Non')
        ])
    
    return response


@login_required
@competition_management_permission_required
def judge_scoring_interface(request, competition_id, category_id, judge_id):
    """
    Interface de notation pour un juge spécifique (vue administrateur).
    """
    # Récupérer la compétition, la catégorie et le juge
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    judge = get_object_or_404(User, pk=judge_id)
    
    # Vérifier que le juge est bien assigné à cette catégorie
    assignment = get_object_or_404(
        JudgeAssignment,
        category=category,
        user=judge,
        assignment_type__in=['technical_judge', 'chief_judge']
    )
    
    # Récupérer les performances en cours ou à venir
    performances = TechnicalPerformance.objects.filter(
        category=category,
        status__in=['pending', 'in_progress']
    ).select_related('practitioner').order_by('performance_order')
    
    # Récupérer la performance actuelle
    current_performance = performances.filter(status='in_progress').first()
    
    # Sinon, prendre la première performance en attente
    if not current_performance and performances.exists():
        current_performance = performances.first()
    
    # Récupérer les critères de notation
    criteria = ScoringCriterion.objects.filter(
        category=category
    ).order_by('order')
    
    # Si une performance est en cours, récupérer les scores existants
    scores = {}
    if current_performance:
        existing_scores = TechnicalScore.objects.filter(
            performance=current_performance,
            judge=judge
        )
        
        for score in existing_scores:
            scores[score.criterion.id] = score.value
    
    context = {
        'competition': competition,
        'category': category,
        'judge': judge,
        'assignment': assignment,
        'performances': performances,
        'current_performance': current_performance,
        'criteria': criteria,
        'scores': scores,
    }
    
    return render(request, 'competitions/management/judge_scoring_interface.html', context)


@login_required
@competition_management_permission_required
@require_POST
def save_judge_scores(request, competition_id, category_id, judge_id, performance_id):
    """
    Sauvegarde les scores d'un juge pour une performance.
    """
    # Récupérer la compétition, la catégorie, le juge et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    judge = get_object_or_404(User, pk=judge_id)
    performance = get_object_or_404(TechnicalPerformance, pk=performance_id, category=category)
    
    # Vérifier que le juge est bien assigné à cette catégorie
    assignment = get_object_or_404(
        JudgeAssignment,
        category=category,
        user=judge,
        assignment_type__in=['technical_judge', 'chief_judge']
    )
    
    # Récupérer les critères et leurs scores
    criteria = ScoringCriterion.objects.filter(category=category)
    
    with transaction.atomic():
        for criterion in criteria:
            score_key = f'score_{criterion.id}'
            if score_key in request.POST:
                try:
                    score_value = float(request.POST[score_key])
                    
                    # Vérifier les bornes du score
                    if score_value < criterion.min_score or score_value > criterion.max_score:
                        messages.error(request, _("Le score pour {} doit être entre {} et {}.").format(
                            criterion.name, criterion.min_score, criterion.max_score))
                        continue
                    
                    # Vérifier si un score existe déjà
                    try:
                        score = TechnicalScore.objects.get(
                            performance=performance,
                            judge=judge,
                            criterion=criterion
                        )
                        score.value = score_value
                        score.save()
                    except TechnicalScore.DoesNotExist:
                        # Créer un nouveau score
                        TechnicalScore.objects.create(
                            performance=performance,
                            judge=judge,
                            criterion=criterion,
                            value=score_value
                        )
                except ValueError:
                    messages.error(request, _("Valeur de score invalide pour {}.").format(criterion.name))
    
    messages.success(request, _("Les scores ont été enregistrés avec succès."))
    
    # Redirection vers l'interface de notation
    return redirect('competitions:management:judge_scoring_interface', 
                   competition_id=competition_id, 
                   category_id=category_id, 
                   judge_id=judge_id)


@login_required
@competition_management_permission_required
def performance_scorecard(request, competition_id, performance_id):
    """
    Affiche une fiche de scores détaillée pour une performance.
    """
    # Récupérer la compétition et la performance
    competition = get_object_or_404(Competition, pk=competition_id)
    performance = get_object_or_404(
        TechnicalPerformance, 
        pk=performance_id, 
        competition=competition
    )
    
    # Récupérer la catégorie
    category = performance.category
    
    # Récupérer les critères de notation
    criteria = ScoringCriterion.objects.filter(
        category=category
    ).order_by('order')
    
    # Récupérer les juges et leurs scores
    scores = TechnicalScore.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Organiser les scores dans une matrice juge/critère
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    judge_assignments = JudgeAssignment.objects.filter(
        category=category,
        assignment_type__in=['technical_judge', 'chief_judge']
    ).select_related('user')
    
    judges = {}
    for assignment in judge_assignments:
        judge = assignment.user
        judges[judge.id] = {
            'name': f"{judge.first_name} {judge.last_name}",
            'role': assignment.get_assignment_type_display(),
            'scores': {}
        }
    
    # Ajouter les scores à la matrice
    for score in scores:
        judge_id = score.judge.id
        criterion_id = score.criterion.id
        
        if judge_id in judges:
            judges[judge_id]['scores'][criterion_id] = score.value
    
    # Calculer les statistiques de score
    stats = {}
    for criterion in criteria:
        criterion_scores = [j['scores'].get(criterion.id) for j in judges.values() 
                           if criterion.id in j['scores']]
        if criterion_scores:
            stats[criterion.id] = {
                'min': min(criterion_scores),
                'max': max(criterion_scores),
                'avg': sum(criterion_scores) / len(criterion_scores),
                'count': len(criterion_scores)
            }
    
    context = {
        'competition': competition,
        'performance': performance,
        'category': category,
        'criteria': criteria,
        'judges': judges,
        'stats': stats,
    }
    
    return render(request, 'competitions/management/performance_scorecard.html', context)


@login_required
@competition_management_permission_required
def scoring_statistics(request, competition_id, category_id):
    """
    Affiche des statistiques détaillées sur la notation d'une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer les performances
    performances = TechnicalPerformance.objects.filter(
        category=category
    ).select_related('practitioner')
    
    # Récupérer les juges
    judge_assignments = JudgeAssignment.objects.filter(
        category=category,
        assignment_type__in=['technical_judge', 'chief_judge']
    ).select_related('user')
    
    # Récupérer les critères
    criteria = ScoringCriterion.objects.filter(
        category=category
    ).order_by('order')
    
    # Récupérer tous les scores
    scores = TechnicalScore.objects.filter(
        performance__in=performances
    ).select_related('judge', 'criterion', 'performance')
    
    # Analyser les tendances des juges
    judge_stats = {}
    for assignment in judge_assignments:
        judge = assignment.user
        judge_id = judge.id
        
        judge_scores = [s for s in scores if s.judge.id == judge_id]
        if not judge_scores:
            continue
        
        avg_score = sum(s.value for s in judge_scores) / len(judge_scores) if judge_scores else 0
        score_count = len(judge_scores)
        
        # Calculer l'écart-type
        if score_count > 1:
            import math
            variance = sum((s.value - avg_score) ** 2 for s in judge_scores) / score_count
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0
        
        judge_stats[judge_id] = {
            'name': f"{judge.first_name} {judge.last_name}",
            'role': assignment.get_assignment_type_display(),
            'avg_score': avg_score,
            'score_count': score_count,
            'std_dev': std_dev,
        }
    
    # Analyser les tendances par critère
    criteria_stats = {}
    for criterion in criteria:
        criterion_id = criterion.id
        
        criterion_scores = [s for s in scores if s.criterion.id == criterion_id]
        if not criterion_scores:
            continue
        
        avg_score = sum(s.value for s in criterion_scores) / len(criterion_scores) if criterion_scores else 0
        score_count = len(criterion_scores)
        
        # Calculer l'écart-type
        if score_count > 1:
            import math
            variance = sum((s.value - avg_score) ** 2 for s in criterion_scores) / score_count
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0
        
        criteria_stats[criterion_id] = {
            'name': criterion.name,
            'weight': criterion.weight,
            'avg_score': avg_score,
            'score_count': score_count,
            'std_dev': std_dev,
        }
    
    context = {
        'competition': competition,
        'category': category,
        'judge_stats': judge_stats,
        'criteria_stats': criteria_stats,
        'performances_count': performances.count(),
        'total_scores': scores.count(),
    }
    
    return render(request, 'competitions/management/scoring_statistics.html', context)


@login_required
@competition_management_permission_required
def generate_all_results(request, competition_id):
    """
    Calcule les résultats pour toutes les catégories de la compétition.
    """
    # Récupérer la compétition
    competition = get_object_or_404(Competition, pk=competition_id)
    
    # Récupérer toutes les catégories
    categories = CompetitionCategory.objects.filter(competition=competition)
    
    # Compteurs pour les statistiques
    total_categories = categories.count()
    processed_categories = 0
    
    for category in categories:
        try:
            # Récupérer les performances terminées
            performances = TechnicalPerformance.objects.filter(
                category=category,
                status='completed'
            ).exists()
            
            if performances:
                # Utiliser la vue de calcul des résultats pour cette catégorie
                calculate_results(request._request, competition_id, category.id)
                processed_categories += 1
        except Exception as e:
            # Enregistrer l'erreur mais continuer avec les autres catégories
            messages.warning(request, _("Erreur pour la catégorie {}: {}").format(category.name, str(e)))
    
    messages.success(request, _("Résultats calculés pour {}/{} catégories.").format(
        processed_categories, total_categories))
    
    return redirect('competitions:management:scoring_dashboard', competition_id=competition_id)


@login_required
@competition_management_permission_required
def publish_results(request, competition_id, category_id):
    """
    Publie les résultats d'une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    if request.method == 'POST':
        # Marquer la catégorie comme terminée
        category.status = 'completed'
        category.save()
        
        # Récupérer la configuration de notation
        from competitions.models.technical_scoring import ScoringConfiguration
        try:
            config = ScoringConfiguration.objects.get(category=category)
            config.real_time_results = True
            config.save()
        except ScoringConfiguration.DoesNotExist:
            # Créer une configuration de base
            ScoringConfiguration.objects.create(
                category=category,
                real_time_results=True
            )
        
        messages.success(request, _("Les résultats ont été publiés."))
    
    return redirect('competitions:management:category_results', 
                   competition_id=competition_id, 
                   category_id=category_id)


@login_required
@competition_management_permission_required
def podium_view(request, competition_id, category_id):
    """
    Affiche une vue podium pour une catégorie (pour l'affichage public).
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer les 3 premiers
    podium = CompetitionRanking.objects.filter(
        competition=competition,
        category=category,
        rank__lte=3
    ).select_related('practitioner').order_by('rank')
    
    context = {
        'competition': competition,
        'category': category,
        'podium': podium,
        'is_fullscreen': request.GET.get('fullscreen') == '1',
    }
    
    return render(request, 'competitions/management/podium_view.html', context)

@login_required
@competition_management_permission_required
def category_results(request, competition_id, category_id):
    """
    Affiche les résultats finaux d'une catégorie.
    """
    # Récupérer la compétition et la catégorie
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Récupérer les performances terminées
    performances = TechnicalPerformance.objects.filter(
        category=category,
        status='completed'
    ).select_related('practitioner')
    
    # Récupérer les résultats
    rankings = CompetitionRanking.objects.filter(
        competition=competition,
        category=category
    ).select_related('practitioner').order_by('rank')
    
    # Vérifier si les résultats ont été calculés
    results_calculated = rankings.exists()
    
    # Récupérer la configuration de notation
    try:
        config = ScoringConfiguration.objects.get(category=category)
        are_results_public = config.real_time_results
    except (ImportError, ScoringConfiguration.DoesNotExist):
        are_results_public = False
    
    context = {
        'competition': competition,
        'category': category,
        'performances': performances,
        'rankings': rankings,
        'results_calculated': results_calculated,
        'are_results_public': are_results_public,
    }
    
    return render(request, 'competitions/management/category_results.html', context)