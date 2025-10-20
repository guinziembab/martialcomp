from django.core.exceptions import PermissionDenied
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Sum, Min, Max, Count, Q, F
from django.utils import timezone
from django.contrib import messages

# Import from unified models instead of the old models
from apps.competitions.models.unified_scoring import (
    ScoringSystem, ScoringCriterion, CategoryScoringConfig,
    Performance, Score, JudgeSubmission, CompetitionRanking,
    CategoryRankingSnapshot, JudgeSettings
)

from apps.competitions.models.competitions import Competition, CompetitionCategory
from apps.competitions.models.practitioners import Practitioner
from apps.competitions.models.judges import Judge
from apps.competitions.models.users import User
from apps.competitions.models.club import Club

from apps.competitions.utils.decorators import judge_required, competition_staff_required
from apps.competitions.utils.scoring import ScoreCalculator, RankingGenerator

# Form imports - update these as needed
from apps.competitions.forms.scoring import (
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
    ScoringCriterionForm, ScoringConfigurationForm, 
    PerformanceForm, JudgeSettingsForm
)


@login_required
@competition_staff_required
def category_scoring_setup(request, competition_id, category_id):
    """Set up scoring criteria and configuration for a competition category."""
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Get or create scoring configuration
    config, created = CategoryScoringConfig.objects.get_or_create(
        category=category,
        defaults={
            'scoring_system': ScoringSystem.objects.first() or ScoringSystem.objects.create(
                name=f"System for {category.name}",
                system_type=ScoringSystem.STANDARD
            )
        }
    )
    
    if request.method == 'POST':
        if 'add_criterion' in request.POST:
            form = ScoringCriterionForm(request.POST)
            if form.is_valid():
                criterion = form.save(commit=False)
                criterion.category = category
                criterion.scoring_system = config.scoring_system
                criterion.save()
                messages.success(request, f"Criterion '{criterion.name}' added successfully.")
                return redirect('category_scoring_setup', competition_id=competition_id, category_id=category_id)
        
        elif 'update_config' in request.POST:
            form = ScoringConfigurationForm(request.POST, instance=config)
            if form.is_valid():
                form.save()
                messages.success(request, "Scoring configuration updated successfully.")
                return redirect('category_scoring_setup', competition_id=competition_id, category_id=category_id)
        
        elif 'generate_default' in request.POST:
            config.set_default_criteria()
            messages.success(request, "Default criteria generated based on discipline.")
            return redirect('category_scoring_setup', competition_id=competition_id, category_id=category_id)
    
    # Get criteria for this category
    criteria = ScoringCriterion.objects.filter(
        Q(category=category) | Q(scoring_system=config.scoring_system, category__isnull=True)
    ).order_by('order', 'name')
    
    criterion_form = ScoringCriterionForm()
    config_form = ScoringConfigurationForm(instance=config)
    
    return render(request, 'competitions/scoring/category_setup.html', {
        'competition': competition,
        'category': category,
        'config': config,
        'criteria': criteria,
        'criterion_form': criterion_form,
        'config_form': config_form,
    })


@login_required
@competition_staff_required
def manage_performances(request, competition_id, category_id):
    """Manage performances for a competition category."""
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Get all performances for this category
    performances = Performance.objects.filter(
        category=category
    ).order_by('round_type', 'round_number', 'performance_order')
    
    # Get all practitioners registered for this category
    practitioners = Practitioner.objects.filter(
        registrations__competition=competition,
        registrations__categories=category
    ).select_related('user')
    
    # Get judges assigned to this category
    judges = User.objects.filter(
        judge_assignments__competition=competition,
        judge_assignments__categories=category
    ).distinct()
    
    if request.method == 'POST':
        if 'add_performance' in request.POST:
            form = PerformanceForm(request.POST)
            if form.is_valid():
                performance = form.save(commit=False)
                performance.category = category
                performance.competition = competition
                performance.save()
                messages.success(request, f"Performance for {performance.practitioner} added.")
                return redirect('manage_performances', competition_id=competition_id, category_id=category_id)
        
        elif 'remove_performance' in request.POST:
            performance_id = request.POST.get('performance_id')
            if performance_id:
                performance = get_object_or_404(Performance, pk=performance_id)
                performance.delete()
                messages.success(request, "Performance removed successfully.")
                return redirect('manage_performances', competition_id=competition_id, category_id=category_id)
        
        elif 'start_performance' in request.POST:
            performance_id = request.POST.get('performance_id')
            if performance_id:
                performance = get_object_or_404(Performance, pk=performance_id)
                if performance.start_performance():
                    messages.success(request, f"Performance for {performance.practitioner} started.")
                else:
                    messages.error(request, "Could not start performance. It may already be in progress.")
                return redirect('monitor_performance', performance_id=performance_id)
    
    form = PerformanceForm()
    form.fields['practitioner'].queryset = practitioners
    
    return render(request, 'competitions/scoring/manage_performances.html', {
        'competition': competition,
        'category': category,
        'performances': performances,
        'form': form,
        'judges': judges,
    })


@login_required
@competition_staff_required
def monitor_performance(request, performance_id):
    """Monitor a performance and view scores in real-time."""
    performance = get_object_or_404(Performance, pk=performance_id)
    category = performance.category
    competition = performance.competition
    
    # Get scoring configuration
    config = get_object_or_404(CategoryScoringConfig, category=category)
    
    # Get criteria for this category
    criteria = ScoringCriterion.objects.filter(
        Q(category=category) | Q(scoring_system=config.scoring_system, category__isnull=True)
    ).order_by('order', 'name')
    
    # Get judges assigned to this category
    judges = User.objects.filter(
        judge_assignments__competition=competition,
        judge_assignments__categories=category
    ).distinct()
    
    # Get submission status for each judge
    submissions = JudgeSubmission.objects.filter(
        performance=performance
    ).select_related('judge')
    
    # Create a dictionary of judge submission status
    judge_status = {j.id: {'submitted': False, 'time': None} for j in judges}
    for sub in submissions:
        judge_status[sub.judge.id] = {
            'submitted': sub.is_submitted,
            'time': sub.submitted_at
        }
    
    # Get all scores for this performance
    scores = Score.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Organize scores by judge and criterion
    score_matrix = {}
    for judge in judges:
        score_matrix[judge.id] = {criterion.id: None for criterion in criteria}
    
    for score in scores:
        if score.judge_id in score_matrix and score.criterion_id in score_matrix[score.judge_id]:
            score_matrix[score.judge_id][score.criterion_id] = score.value
    
    if request.method == 'POST':
        if 'end_performance' in request.POST:
            if performance.end_performance():
                messages.success(request, f"Performance for {performance.practitioner} completed.")
                # Calculate rankings
                generator = RankingGenerator(category)
                generator.generate_rankings()
                return redirect('performance_results', performance_id=performance_id)
            else:
                messages.error(request, "Could not end performance. It may not be in progress.")
    
    return render(request, 'competitions/scoring/monitor_performance.html', {
        'competition': competition,
        'category': category,
        'performance': performance,
        'criteria': criteria,
        'judges': judges,
        'judge_status': judge_status,
        'score_matrix': score_matrix,
        'config': config,
    })


@login_required
@competition_staff_required
def performance_results(request, performance_id):
    """View results for a completed performance."""
    performance = get_object_or_404(Performance, pk=performance_id, status=Performance.COMPLETED)
    category = performance.category
    competition = performance.competition
    
    # Get scoring configuration
    config = get_object_or_404(CategoryScoringConfig, category=category)
    
    # Get criteria for this category
    criteria = ScoringCriterion.objects.filter(
        Q(category=category) | Q(scoring_system=config.scoring_system, category__isnull=True)
    ).order_by('order', 'name')
    
    # Get all scores for this performance
    scores = Score.objects.filter(
        performance=performance
    ).select_related('judge', 'criterion')
    
    # Get judges who scored this performance
    judges = User.objects.filter(
        id__in=scores.values_list('judge_id', flat=True)
    ).distinct()
    
    # Organize scores by judge and criterion
    score_matrix = {}
    for judge in judges:
        score_matrix[judge.id] = {criterion.id: None for criterion in criteria}
    
    for score in scores:
        if score.judge_id in score_matrix and score.criterion_id in score_matrix[score.judge_id]:
            score_matrix[score.judge_id][score.criterion_id] = score.value
    
    # Calculate criterion averages
    criterion_averages = {}
    for criterion in criteria:
        criterion_scores = [s.value for s in scores if s.criterion_id == criterion.id]
        
        if criterion_scores:
            # Handle extreme score exclusion if configured
            if config.get_effective_exclude_extreme_scores() and len(criterion_scores) > 3:
                criterion_scores.remove(max(criterion_scores))
                criterion_scores.remove(min(criterion_scores))
            
            avg = sum(criterion_scores) / len(criterion_scores)
            criterion_averages[criterion.id] = {
                'average': avg,
                'weighted': avg * criterion.weight
            }
        else:
            criterion_averages[criterion.id] = {
                'average': None,
                'weighted': None
            }
    
    # Get final score
    calculator = ScoreCalculator(performance)
    final_score = calculator.calculate_final_score()
    
    # Get ranking
    ranking = CompetitionRanking.objects.filter(
        performance=performance
    ).first()
    
    if request.method == 'POST':
        if 'recalculate_rankings' in request.POST:
            # Recalculate all rankings for this category
            generator = RankingGenerator(category)
            generator.generate_rankings()
            generator.handle_third_place_tie()
            return redirect('performance_results', performance_id=performance_id)
        
        elif 'publish_results' in request.POST:
            # Create and publish a snapshot of current rankings
            generator = RankingGenerator(category)
            snapshot = generator.create_snapshot(
                user=request.user,
                name=f"Results published on {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                publish=True
            )
            messages.success(request, "Results published successfully.")
            return redirect('category_results', competition_id=competition.id, category_id=category.id)
    
    return render(request, 'competitions/scoring/performance_results.html', {
        'competition': competition,
        'category': category,
        'performance': performance,
        'criteria': criteria,
        'judges': judges,
        'score_matrix': score_matrix,
        'criterion_averages': criterion_averages,
        'final_score': final_score,
        'ranking': ranking,
        'config': config,
    })


@login_required
@competition_staff_required
def category_results(request, competition_id, category_id):
    """View results for an entire category."""
    competition = get_object_or_404(Competition, pk=competition_id)
    category = get_object_or_404(CompetitionCategory, pk=category_id, competition=competition)
    
    # Get all rankings for this category
    rankings = CompetitionRanking.objects.filter(
        category=category
    ).order_by('rank')
    
    # Get the latest snapshot if available
    latest_snapshot = CategoryRankingSnapshot.objects.filter(
        category=category,
        is_published=True
    ).order_by('-created_at').first()
    
    return render(request, 'competitions/scoring/category_results.html', {
        'competition': competition,
        'category': category,
        'rankings': rankings,
        'latest_snapshot': latest_snapshot,
    })


@login_required
@judge_required
def judge_dashboard(request):
    """Dashboard for judges to view and score performances."""
    user = request.user
    
    # Get judge's assignments
    assignments = user.judge_assignments.all().select_related('competition')
    
    # Get upcoming performances
    performances = Performance.objects.filter(
        category__in=assignments.values_list('categories', flat=True),
        status__in=[Performance.PENDING, Performance.IN_PROGRESS]
    ).order_by('category', 'round_type', 'round_number', 'performance_order')
    
    # Get judge settings
    settings, created = JudgeSettings.objects.get_or_create(
        user=user,
        defaults={
            'display_mode': JudgeSettings.DETAILED,
            'notification_sounds': True,
            'auto_submit': False,
            'theme': JudgeSettings.LIGHT
        }
    )
    
    if request.method == 'POST':
        form = JudgeSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully.")
            return redirect('judge_dashboard')
    else:
        form = JudgeSettingsForm(instance=settings)
    
    return render(request, 'competitions/judge/dashboard.html', {
        'assignments': assignments,
        'performances': performances,
        'settings': settings,
        'form': form,
    })


@login_required
@judge_required
def score_performance(request, performance_id):
    """Score a performance as a judge."""
    performance = get_object_or_404(
        Performance, 
        pk=performance_id, 
        status=Performance.IN_PROGRESS
    )
    category = performance.category
    competition = performance.competition
    
    # Verify judge is assigned to this category
    if not request.user.judge_assignments.filter(
        competition=competition,
        categories=category
    ).exists():
        raise Http404("You are not assigned to judge this category.")
    
    # Get scoring configuration
    config = get_object_or_404(CategoryScoringConfig, category=category)
    
    # Get criteria for this category
    criteria = ScoringCriterion.objects.filter(
        Q(category=category) | Q(scoring_system=config.scoring_system, category__isnull=True)
    ).order_by('order', 'name')
    
    # Get or create judge submission status
    submission, created = JudgeSubmission.objects.get_or_create(
        performance=performance,
        judge=request.user
    )
    
    # Get existing scores
    scores = Score.objects.filter(
        performance=performance,
        judge=request.user
    ).select_related('criterion')
    
    # Create a dictionary of existing scores
    existing_scores = {score.criterion_id: score for score in scores}
    
    if request.method == 'POST':
        if 'submit_scores' in request.POST:
            scores_submitted = 0
            
            with transaction.atomic():
                for criterion in criteria:
                    score_value = request.POST.get(f'score_{criterion.id}')
                    if score_value:
                        try:
                            score_value = Decimal(score_value)
                            
                            # Ensure score is within allowed range
                            min_score = criterion.min_score or config.get_effective_min_score()
                            max_score = criterion.max_score or config.get_effective_max_score()
                            
                            if score_value < min_score:
                                score_value = min_score
                            elif score_value > max_score:
                                score_value = max_score
                            
                            # Create or update score
                            if criterion.id in existing_scores:
                                score = existing_scores[criterion.id]
                                if not score.is_locked:
                                    score.value = score_value
                                    score.save()
                                    scores_submitted += 1
                            else:
                                score = Score.objects.create(
                                    performance=performance,
                                    judge=request.user,
                                    criterion=criterion,
                                    value=score_value
                                )
                                scores_submitted += 1
                        except (ValueError, TypeError):
                            pass
                
                # Submit if all criteria are scored or if force submit
                all_scored = len(criteria) == scores_submitted + sum(1 for s in scores if s.is_locked)
                force_submit = 'force_submit' in request.POST
                
                if all_scored or force_submit:
                    submission.submit()
                    messages.success(request, "Scores submitted successfully.")
                    return redirect('judge_dashboard')
                else:
                    messages.warning(
                        request, 
                        f"Please score all criteria. {scores_submitted} of {len(criteria)} submitted."
                    )
    
    # Get judge settings
    settings = JudgeSettings.objects.filter(user=request.user).first()
    display_mode = settings.display_mode if settings else JudgeSettings.DETAILED
    
    return render(request, 'competitions/judge/score_performance.html', {
        'performance': performance,
        'category': category,
        'competition': competition,
        'criteria': criteria,
        'config': config,
        'existing_scores': existing_scores,
        'submission': submission,
        'display_mode': display_mode,
    })


def calculate_rankings(category):
    """Calculate rankings for a category based on completed performances."""
    # Use the RankingGenerator utility
    generator = RankingGenerator(category)
    rankings = generator.generate_rankings()
    
    # Handle potential ties for third place
    generator.handle_third_place_tie()
    
    return rankings


# API endpoints

@login_required
def get_performance_scores(request, performance_id):
    """AJAX endpoint to get scores for a performance."""
    try:
        performance = Performance.objects.get(pk=performance_id)
        
        # Check permissions
        is_manager = request.user.is_staff or request.user.competition_staff.filter(
            competition=performance.competition
        ).exists()
        
        is_judge = request.user.judge_assignments.filter(
            competition=performance.competition,
            categories=performance.category
        ).exists()
        
        if not (is_manager or is_judge):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get all scores for this performance
        scores = Score.objects.filter(
            performance=performance
        ).select_related('judge', 'criterion')
        
        # Get judge submission status
        submissions = JudgeSubmission.objects.filter(
            performance=performance
        )
        
        # Calculate final score if performance is completed
        final_score = None
        if performance.status == Performance.COMPLETED:
            calculator = ScoreCalculator(performance)
            final_score = calculator.calculate_final_score()
        
        # Format the data for response
        score_data = []
        for score in scores:
            score_data.append({
                'id': score.id,
                'judge_id': score.judge_id,
                'judge_name': score.judge.get_full_name() or score.judge.username,
                'criterion_id': score.criterion_id,
                'criterion_name': score.criterion.name,
                'value': float(score.value),
                'is_locked': score.is_locked,
            })
        
        submission_data = []
        for sub in submissions:
            submission_data.append({
                'judge_id': sub.judge_id,
                'judge_name': sub.judge.get_full_name() or sub.judge.username,
                'is_submitted': sub.is_submitted,
                'submitted_at': sub.submitted_at.isoformat() if sub.submitted_at else None,
            })
        
        return JsonResponse({
            'performance': {
                'id': performance.id,
                'practitioner_id': performance.practitioner_id,
                'practitioner_name': str(performance.practitioner),
                'status': performance.status,
                'start_time': performance.start_time.isoformat() if performance.start_time else None,
                'end_time': performance.end_time.isoformat() if performance.end_time else None,
            },
            'scores': score_data,
            'submissions': submission_data,
            'final_score': float(final_score) if final_score else None,
        })
        
    except Performance.DoesNotExist:
        return JsonResponse({'error': 'Performance not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_category_results(request, category_id):
    """AJAX endpoint to get results for a category."""
    try:
        category = CompetitionCategory.objects.get(pk=category_id)
        
        # Check permissions
        is_manager = request.user.is_staff or request.user.competition_staff.filter(
            competition=category.competition
        ).exists()
        
        is_judge = request.user.judge_assignments.filter(
            competition=category.competition,
            categories=category
        ).exists()
        
        if not (is_manager or is_judge):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get all rankings for this category
        rankings = CompetitionRanking.objects.filter(
            category=category
        ).order_by('rank')
        
        # Format the data for response
        ranking_data = []
        for rank in rankings:
            ranking_data.append({
                'rank': rank.rank,
                'practitioner_id': rank.practitioner_id,
                'practitioner_name': str(rank.practitioner),
                'club': str(rank.practitioner.club) if rank.practitioner.club else None,
                'final_score': float(rank.final_score),
                'is_tie': rank.is_tie,
                'medal': rank.medal,
            })
        
        return JsonResponse({
            'category': {
                'id': category.id,
                'name': category.name,
                'competition_id': category.competition_id,
                'competition_name': category.competition.title,
            },
            'rankings': ranking_data,
            'timestamp': timezone.now().isoformat(),
        })
        
    except CompetitionCategory.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
