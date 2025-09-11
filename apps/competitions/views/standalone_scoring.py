from django.core.exceptions import PermissionDenied
"""
Standalone scoring views that provide a complete scoring system for competitions.
These views work with the standalone scoring models to avoid model conflicts.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    View, ListView, DetailView, CreateView, UpdateView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.db.models import Q

from apps.competitions.models.standalone_scoring import (
    StandaloneScoringSystem,
    StandaloneScoringCriterion,
    StandaloneCategoryScoringConfig,
    StandalonePerformance,
    StandaloneScore,
    StandaloneJudgeSubmission,
    StandaloneJudgeSettings,
    StandaloneCompetitionRanking,
    StandaloneCategoryRankingSnapshot,
    StandaloneRankingSnapshotEntry
)
from apps.competitions.utils.standalone_scoring import StandaloneScoreCalculator
from apps.competitions.forms.standalone_scoring import (
    PerformanceForm,
    ScoringSystemForm,
    ScoringCriterionForm,
    CategoryScoringConfigForm,
    ScoreEntryForm,
    JudgeSettingsForm
)
from apps.competitions.models.categories import CompetitionCategory as Category
from apps.competitions.models.competitions import Competition
from apps.competitions.models.judges import Judge
from apps.competitions.models.practitioners import Practitioner
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Judge Views
class JudgePerformanceListView(LoginRequiredMixin, ListView):
    """List of performances available for judging."""
    template_name = 'competitions/standalone_scoring/judge/performance_list.html'
    context_object_name = 'performances'
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        # Get judge information for the current user
        try:
            judge = Judge.objects.get(user=self.request.user)
            judge_id = judge.id
        except Judge.DoesNotExist:
            return StandalonePerformance.objects.none()
        
        # Get competitions that this judge is assigned to
        competition_ids = list(judge.competitions.values_list('id', flat=True))
        if not competition_ids:
            return StandalonePerformance.objects.none()
        
        # Get all performances for these competitions that are pending or in progress
        performances = StandalonePerformance.objects.filter(
            competition_id__in=competition_ids,
            status__in=[StandalonePerformance.PENDING, StandalonePerformance.IN_PROGRESS]
        ).order_by('competition_id', 'round_type', 'round_number', 'performance_order')
        
        # Annotate each performance with judging status
        for performance in performances:
            # Check if the judge has submitted scores
            submission = StandaloneJudgeSubmission.objects.filter(
                performance=performance,
                judge_id=judge_id
            ).first()
            
            if submission and submission.is_submitted:
                performance.judging_status = 'submitted'
            else:
                # Check if any scores exist
                score_count = StandaloneScore.objects.filter(
                    performance=performance,
                    judge_id=judge_id
                ).count()
                
                if score_count > 0:
                    performance.judging_status = 'in_progress'
                else:
                    performance.judging_status = 'not_started'
            
            # Get practitioner name
            try:
                practitioner = Practitioner.objects.get(id=performance.practitioner_id)
                performance.practitioner_name = f"{practitioner.first_name} {practitioner.last_name}"
            except Practitioner.DoesNotExist:
                performance.practitioner_name = f"Practitioner #{performance.practitioner_id}"
            
            # Get category name
            try:
                category = Category.objects.get(id=performance.category_id)
                performance.category_name = category.name
            except Category.DoesNotExist:
                performance.category_name = f"Category #{performance.category_id}"
            
            # Get competition name
            try:
                competition = Competition.objects.get(id=performance.competition_id)
                performance.competition_name = competition.name
            except Competition.DoesNotExist:
                performance.competition_name = f"Competition #{performance.competition_id}"
        
        return performances

class JudgeScoreEntryView(LoginRequiredMixin, View):
    """View for judges to enter scores for a performance."""
    template_name = 'competitions/standalone_scoring/judge/score_entry.html'
    
    def get_judge(self):
        try:
            return Judge.objects.get(user=self.request.user)
        except Judge.DoesNotExist:
            return None
    
    def get(self, request, performance_id):
        # Get the judge
        judge = self.get_judge()
        if not judge:
            messages.error(request, _("You are not registered as a judge."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the performance
        performance = get_object_or_404(StandalonePerformance, id=performance_id)
        
        # Check if the judge is assigned to this competition
        if not judge.competitions.filter(id=performance.competition_id).exists():
            messages.error(request, _("You are not assigned to judge this competition."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Check if the performance is in a valid state for scoring
        if performance.status not in [StandalonePerformance.PENDING, StandalonePerformance.IN_PROGRESS]:
            messages.error(request, _("This performance is not open for scoring."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Check if the judge has already submitted scores
        submission = StandaloneJudgeSubmission.objects.filter(
            performance=performance,
            judge_id=judge.id
        ).first()
        
        if submission and submission.is_submitted:
            messages.info(request, _("You have already submitted scores for this performance."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the category config
        category_config = StandaloneCategoryScoringConfig.objects.filter(
            category_id=performance.category_id
        ).first()
        
        if not category_config:
            messages.error(request, _("No scoring configuration found for this category."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the scoring system
        scoring_system = category_config.scoring_system
        
        # Get the criteria
        criteria = StandaloneScoringCriterion.objects.filter(
            Q(scoring_system=scoring_system, category_id=None) |
            Q(scoring_system=scoring_system, category_id=performance.category_id)
        ).order_by('order', 'name')
        
        # Create a form for each criterion
        criterion_forms = []
        for criterion in criteria:
            # Check if a score already exists
            score = StandaloneScore.objects.filter(
                performance=performance,
                judge_id=judge.id,
                criterion=criterion
            ).first()
            
            # Create form with initial data if score exists
            if score:
                form = ScoreEntryForm(
                    criterion=criterion,
                    min_score=criterion.min_score or scoring_system.min_score,
                    max_score=criterion.max_score or scoring_system.max_score,
                    step=criterion.step or scoring_system.score_step,
                    initial={'score': score.value, 'notes': score.notes}
                )
                form.is_saved = True
            else:
                form = ScoreEntryForm(
                    criterion=criterion,
                    min_score=criterion.min_score or scoring_system.min_score,
                    max_score=criterion.max_score or scoring_system.max_score,
                    step=criterion.step or scoring_system.score_step
                )
                form.is_saved = False
            
            criterion_forms.append(form)
        
        # Get judge settings
        judge_settings, created = StandaloneJudgeSettings.objects.get_or_create(
            user_id=request.user.id,
            defaults={
                'display_mode': StandaloneJudgeSettings.DETAILED,
                'notification_sounds': True,
                'auto_submit': False,
                'theme': StandaloneJudgeSettings.LIGHT
            }
        )
        
        # Get practitioner info
        try:
            practitioner = Practitioner.objects.get(id=performance.practitioner_id)
            practitioner_name = f"{practitioner.first_name} {practitioner.last_name}"
        except Practitioner.DoesNotExist:
            practitioner_name = f"Practitioner #{performance.practitioner_id}"
        
        # Get category name
        try:
            category = Category.objects.get(id=performance.category_id)
            category_name = category.name
        except Category.DoesNotExist:
            category_name = f"Category #{performance.category_id}"
        
        # Get competition name
        try:
            competition = Competition.objects.get(id=performance.competition_id)
            competition_name = competition.name
        except Competition.DoesNotExist:
            competition_name = f"Competition #{performance.competition_id}"
        
        # Prepare context
        context = {
            'performance': performance,
            'criterion_forms': criterion_forms,
            'scoring_system': scoring_system,
            'category_config': category_config,
            'judge_settings': judge_settings,
            'practitioner_name': practitioner_name,
            'category_name': category_name,
            'competition_name': competition_name,
            'all_scores_entered': all(form.is_saved for form in criterion_forms)
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, performance_id):
        # Get the judge
        judge = self.get_judge()
        if not judge:
            messages.error(request, _("You are not registered as a judge."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the performance
        performance = get_object_or_404(StandalonePerformance, id=performance_id)
        
        # Check if the judge is assigned to this competition
        if not judge.competitions.filter(id=performance.competition_id).exists():
            messages.error(request, _("You are not assigned to judge this competition."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Check if the performance is in a valid state for scoring
        if performance.status not in [StandalonePerformance.PENDING, StandalonePerformance.IN_PROGRESS]:
            messages.error(request, _("This performance is not open for scoring."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Check if the judge has already submitted scores
        submission = StandaloneJudgeSubmission.objects.filter(
            performance=performance,
            judge_id=judge.id
        ).first()
        
        if submission and submission.is_submitted:
            messages.info(request, _("You have already submitted scores for this performance."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the category config
        category_config = StandaloneCategoryScoringConfig.objects.filter(
            category_id=performance.category_id
        ).first()
        
        if not category_config:
            messages.error(request, _("No scoring configuration found for this category."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the scoring system
        scoring_system = category_config.scoring_system
        
        # Get criterion ID and score from the form
        criterion_id = request.POST.get('criterion_id')
        score_value = request.POST.get('score')
        notes = request.POST.get('notes', '')
        
        if not criterion_id or not score_value:
            messages.error(request, _("Missing required data."))
            return redirect('competitions:standalone_scoring:judge_score_entry', performance_id=performance_id)
        
        # Get the criterion
        criterion = get_object_or_404(StandaloneScoringCriterion, id=criterion_id)
        
        # Save the score
        try:
            score, created = StandaloneScore.objects.update_or_create(
                performance=performance,
                judge_id=judge.id,
                criterion=criterion,
                defaults={
                    'value': score_value,
                    'notes': notes,
                    'is_locked': False,
                    'is_training_score': False,
                    'modified_by_id': None
                }
            )
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': _("Score saved successfully."),
                    'score_id': score.id,
                    'value': score.value
                })
            
            messages.success(request, _("Score saved successfully."))
            return redirect('competitions:standalone_scoring:judge_score_entry', performance_id=performance_id)
            
        except Exception as e:
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=400)
            
            messages.error(request, _("Error saving score: {0}").format(str(e)))
            return redirect('competitions:standalone_scoring:judge_score_entry', performance_id=performance_id)

class JudgeSubmitScoresView(LoginRequiredMixin, View):
    """View for judges to submit all scores for a performance."""
    
    def get_judge(self):
        try:
            return Judge.objects.get(user=self.request.user)
        except Judge.DoesNotExist:
            return None
    
    def post(self, request, performance_id):
        # Get the judge
        judge = self.get_judge()
        if not judge:
            messages.error(request, _("You are not registered as a judge."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Get the performance
        performance = get_object_or_404(StandalonePerformance, id=performance_id)
        
        # Check if the judge is assigned to this competition
        if not judge.competitions.filter(id=performance.competition_id).exists():
            messages.error(request, _("You are not assigned to judge this competition."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Check if the performance is in a valid state for scoring
        if performance.status not in [StandalonePerformance.PENDING, StandalonePerformance.IN_PROGRESS]:
            messages.error(request, _("This performance is not open for scoring."))
            return redirect('competitions:standalone_scoring:judge_performances')
        
        # Check if all criteria have scores
        category_config = StandaloneCategoryScoringConfig.objects.filter(
            category_id=performance.category_id
        ).first()
        
        if not category_config:
            messages.error(request, _("No scoring configuration found for this category."))
            return redirect('competitions:standalone_scoring:judge_score_entry', performance_id=performance_id)
        
        # Get all required criteria
        criteria = StandaloneScoringCriterion.objects.filter(
            Q(scoring_system=category_config.scoring_system, category_id=None) |
            Q(scoring_system=category_config.scoring_system, category_id=performance.category_id),
            is_active=True
        )
        
        # Count how many criteria have scores
        scored_criteria_count = StandaloneScore.objects.filter(
            performance=performance,
            judge_id=judge.id,
            criterion__in=criteria
        ).count()
        
        # Check if all criteria have been scored
        if scored_criteria_count < criteria.count():
            messages.error(
                request, 
                _("Not all criteria have been scored. Please complete all scores before submitting.")
            )
            return redirect('competitions:standalone_scoring:judge_score_entry', performance_id=performance_id)
        
        # Create or update submission
        submission, created = StandaloneJudgeSubmission.objects.get_or_create(
            performance=performance,
            judge_id=judge.id,
            defaults={'is_submitted': False}
        )
        
        # Submit scores
        submission.submit()
        
        messages.success(request, _("Scores submitted successfully."))
        return redirect('competitions:standalone_scoring:judge_performances')

class JudgeSettingsView(LoginRequiredMixin, View):
    """View for judges to manage their scoring interface settings."""
    template_name = 'competitions/standalone_scoring/judge/settings.html'
    
    def get(self, request):
        # Get or create judge settings
        settings, created = StandaloneJudgeSettings.objects.get_or_create(
            user_id=request.user.id,
            defaults={
                'display_mode': StandaloneJudgeSettings.DETAILED,
                'notification_sounds': True,
                'auto_submit': False,
                'theme': StandaloneJudgeSettings.LIGHT
            }
        )
        
        # Create form with initial data
        form = JudgeSettingsForm(instance=settings)
        
        context = {
            'form': form,
            'settings': settings
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        # Get or create judge settings
        settings, created = StandaloneJudgeSettings.objects.get_or_create(
            user_id=request.user.id,
            defaults={
                'display_mode': StandaloneJudgeSettings.DETAILED,
                'notification_sounds': True,
                'auto_submit': False,
                'theme': StandaloneJudgeSettings.LIGHT
            }
        )
        
        # Process form
        form = JudgeSettingsForm(request.POST, instance=settings)
        
        if form.is_valid():
            form.save()
            messages.success(request, _("Settings saved successfully."))
            return redirect('competitions:standalone_scoring:judge_settings')
        
        context = {
            'form': form,
            'settings': settings
        }
        
        return render(request, self.template_name, context)

# Admin/Manager Views
class StandaloneScoringDashboardView(LoginRequiredMixin, TemplateView):
    """Dashboard for competition administrators to manage scoring."""
    template_name = 'competitions/standalone_scoring/admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get competitions associated with current user's organization
        # This will need to be adjusted based on your application's structure
        competitions = Competition.objects.filter(
            status=Competition.ACTIVE
        ).order_by('-start_date')[:10]
        
        # Get recent performances
        recent_performances = get_organization_queryset(StandalonePerformance, self.request.user).order_by('-updated_at')[:10]
        
        # Add competition names to performances
        for performance in recent_performances:
            try:
                competition = Competition.objects.get(id=performance.competition_id)
                performance.competition_name = competition.name
            except Competition.DoesNotExist:
                performance.competition_name = f"Competition #{performance.competition_id}"
            
            try:
                category = Category.objects.get(id=performance.category_id)
                performance.category_name = category.name
            except Category.DoesNotExist:
                performance.category_name = f"Category #{performance.category_id}"
            
            try:
                practitioner = Practitioner.objects.get(id=performance.practitioner_id)
                performance.practitioner_name = f"{practitioner.first_name} {practitioner.last_name}"
            except Practitioner.DoesNotExist:
                performance.practitioner_name = f"Practitioner #{performance.practitioner_id}"
        
        # Get scoring systems
        scoring_systems = get_organization_queryset(StandaloneScoringSystem, self.request.user)
        
        # Get category configs
        category_configs = get_organization_queryset(StandaloneCategoryScoringConfig, self.request.user)[:10]
        
        # Add category names to configs
        for config in category_configs:
            try:
                category = Category.objects.get(id=config.category_id)
                config.category_name = category.name
            except Category.DoesNotExist:
                config.category_name = f"Category #{config.category_id}"
        
        context.update({
            'competitions': competitions,
            'recent_performances': recent_performances,
            'scoring_systems': scoring_systems,
            'category_configs': category_configs
        })
        
        return context

class PerformanceListView(LoginRequiredMixin, ListView):
    """List view for performances."""
    model = StandalonePerformance
    template_name = 'competitions/standalone_scoring/admin/performance_list.html'
    context_object_name = 'performances'
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        queryset = super().get_queryset()
        
        # Filter by competition if provided
        competition_id = self.request.GET.get('competition')
        if competition_id:
            queryset = queryset.filter(competition_id=competition_id)
        
        # Filter by category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by round type if provided
        round_type = self.request.GET.get('round_type')
        if round_type:
            queryset = queryset.filter(round_type=round_type)
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Order by competition, category, round type, round number, performance order
        queryset = queryset.order_by(
            'competition_id', 'category_id', 'round_type', 'round_number', 'performance_order'
        )
        
        # Add extra information to each performance
        for performance in queryset:
            try:
                competition = Competition.objects.get(id=performance.competition_id)
                performance.competition_name = competition.name
            except Competition.DoesNotExist:
                performance.competition_name = f"Competition #{performance.competition_id}"
            
            try:
                category = Category.objects.get(id=performance.category_id)
                performance.category_name = category.name
            except Category.DoesNotExist:
                performance.category_name = f"Category #{performance.category_id}"
            
            try:
                practitioner = Practitioner.objects.get(id=performance.practitioner_id)
                performance.practitioner_name = f"{practitioner.first_name} {practitioner.last_name}"
            except Practitioner.DoesNotExist:
                performance.practitioner_name = f"Practitioner #{performance.practitioner_id}"
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add competitions for filtering
        competitions = Competition.objects.filter(status=Competition.ACTIVE)
        context['competitions'] = competitions
        
        # Add categories for filtering
        categories = get_organization_queryset(Category, self.request.user)
        context['categories'] = categories
        
        # Add round types for filtering
        context['round_types'] = StandalonePerformance.ROUND_TYPES
        
        # Add statuses for filtering
        context['statuses'] = StandalonePerformance.STATUS_CHOICES
        
        # Add filter values
        context['selected_competition'] = self.request.GET.get('competition', '')
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_round_type'] = self.request.GET.get('round_type', '')
        context['selected_status'] = self.request.GET.get('status', '')
        
        return context

class PerformanceCreateView(LoginRequiredMixin, CreateView):
    """Create a new performance."""
    model = StandalonePerformance
    form_class = PerformanceForm
    template_name = 'competitions/standalone_scoring/admin/performance_form.html'
    
    def get_success_url(self):
        return reverse('competitions:standalone_scoring:performance_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Performance created successfully."))
        return super().form_valid(form)

class PerformanceUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing performance."""
    model = StandalonePerformance
    form_class = PerformanceForm
    template_name = 'competitions/standalone_scoring/admin/performance_form.html'
    
    def get_success_url(self):
        return reverse('competitions:standalone_scoring:performance_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, _("Performance updated successfully."))
        return super().form_valid(form)

class PerformanceDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a performance with scores."""
    model = StandalonePerformance
    template_name = 'competitions/standalone_scoring/admin/performance_detail.html'
    context_object_name = 'performance'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        performance = self.object
        
        # Get competition, category, and practitioner info
        try:
            competition = Competition.objects.get(id=performance.competition_id)
            context['competition'] = competition
        except Competition.DoesNotExist:
            context['competition_name'] = f"Competition #{performance.competition_id}"
        
        try:
            category = Category.objects.get(id=performance.category_id)
            context['category'] = category
        except Category.DoesNotExist:
            context['category_name'] = f"Category #{performance.category_id}"
        
        try:
            practitioner = Practitioner.objects.get(id=performance.practitioner_id)
            context['practitioner'] = practitioner
        except Practitioner.DoesNotExist:
            context['practitioner_name'] = f"Practitioner #{performance.practitioner_id}"
        
        # Get all scores for this performance grouped by criterion
        scores = StandaloneScore.objects.filter(
            performance=performance
        ).select_related('criterion')
        
        # Group scores by criterion
        criteria_scores = {}
        for score in scores:
            if score.criterion_id not in criteria_scores:
                criteria_scores[score.criterion_id] = {
                    'criterion': score.criterion,
                    'scores': []
                }
            
            # Get judge name if possible
            try:
                judge = Judge.objects.get(id=score.judge_id)
                judge_name = f"{judge.user.first_name} {judge.user.last_name}"
            except Judge.DoesNotExist:
                judge_name = f"Judge #{score.judge_id}"
            
            score.judge_name = judge_name
            criteria_scores[score.criterion_id]['scores'].append(score)
        
        context['criteria_scores'] = criteria_scores
        
        # Get judge submissions
        submissions = StandaloneJudgeSubmission.objects.filter(
            performance=performance
        )
        
        for submission in submissions:
            try:
                judge = Judge.objects.get(id=submission.judge_id)
                submission.judge_name = f"{judge.user.first_name} {judge.user.last_name}"
            except Judge.DoesNotExist:
                submission.judge_name = f"Judge #{submission.judge_id}"
        
        context['submissions'] = submissions
        
        # Get scores data for calculator
        calculator_data = []
        for criterion_id, data in criteria_scores.items():
            criterion = data['criterion']
            scores_list = [float(score.value) for score in data['scores']]
            
            calculator_data.append({
                'criterion_id': criterion_id,
                'criterion_name': criterion.name,
                'criterion_weight': float(criterion.weight),
                'judge_scores': scores_list
            })
        
        # Get scoring system type
        category_config = StandaloneCategoryScoringConfig.objects.filter(
            category_id=performance.category_id
        ).first()
        
        if category_config:
            scoring_system = category_config.scoring_system
            system_type = scoring_system.system_type
            exclude_extreme = category_config.get_effective_exclude_extreme_scores()
            
            # Calculate scores
            calculator = StandaloneScoreCalculator(
                min_score=float(category_config.get_effective_min_score()),
                max_score=float(category_config.get_effective_max_score()),
                exclude_extreme_scores=exclude_extreme
            )
            
            if system_type == StandaloneScoringSystem.STANDARD:
                result = calculator.calculate_weighted_average(calculator_data)
            elif system_type == StandaloneScoringSystem.POINT:
                result = calculator.calculate_point_score(calculator_data)
            else:
                result = {'final_score': 0, 'criteria_scores': {}, 'judges_count': 0}
            
            context['calculation_result'] = result
            context['scoring_system'] = scoring_system
            context['category_config'] = category_config
        
        return context

class ManagePerformanceStatusView(LoginRequiredMixin, View):
    """View for managing performance status (start, end, disqualify, cancel)."""
    
    def post(self, request, pk):
        performance = get_object_or_404(StandalonePerformance, pk=pk)
        action = request.POST.get('action')
        
        if action == 'start':
            if performance.start_performance():
                messages.success(request, _("Performance started."))
            else:
                messages.error(request, _("Unable to start performance."))
        
        elif action == 'end':
            if performance.end_performance():
                messages.success(request, _("Performance completed."))
            else:
                messages.error(request, _("Unable to complete performance."))
        
        elif action == 'disqualify':
            reason = request.POST.get('reason', '')
            if performance.disqualify(reason):
                messages.success(request, _("Performance disqualified."))
            else:
                messages.error(request, _("Unable to disqualify performance."))
        
        elif action == 'cancel':
            reason = request.POST.get('reason', '')
            if performance.cancel(reason):
                messages.success(request, _("Performance cancelled."))
            else:
                messages.error(request, _("Unable to cancel performance."))
        
        return redirect('competitions:standalone_scoring:performance_detail', pk=performance.pk)

class ScoringSystemListView(LoginRequiredMixin, ListView):
    """List view for scoring systems."""
    model = StandaloneScoringSystem
    template_name = 'competitions/standalone_scoring/admin/scoring_system_list.html'
    context_object_name = 'systems'

class ScoringSystemCreateView(LoginRequiredMixin, CreateView):
    """Create a new scoring system."""
    model = StandaloneScoringSystem
    form_class = ScoringSystemForm
    template_name = 'competitions/standalone_scoring/admin/scoring_system_form.html'
    
    def get_success_url(self):
        return reverse('competitions:standalone_scoring:scoring_system_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Scoring system created successfully."))
        return super().form_valid(form)

class ScoringSystemUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing scoring system."""
    model = StandaloneScoringSystem
    form_class = ScoringSystemForm
    template_name = 'competitions/standalone_scoring/admin/scoring_system_form.html'
    
    def get_success_url(self):
        return reverse('competitions:standalone_scoring:scoring_system_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Scoring system updated successfully."))
        return super().form_valid(form)

class ScoringCriterionListView(LoginRequiredMixin, ListView):
    """List view for scoring criteria."""
    model = StandaloneScoringCriterion
    template_name = 'competitions/standalone_scoring/admin/scoring_criterion_list.html'
    context_object_name = 'criteria'
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        queryset = super().get_queryset()
        
        # Filter by scoring system if provided
        system_id = self.request.GET.get('system')
        if system_id:
            queryset = queryset.filter(scoring_system_id=system_id)
        
        # Filter by category if provided
        category_id = self.request.GET.get('category')
        if category_id:
            if category_id == 'global':
                queryset = queryset.filter(category_id=None)
            else:
                queryset = queryset.filter(category_id=category_id)
        
        # Order by scoring system, category, order, name
        queryset = queryset.order_by('scoring_system', 'category_id', 'order', 'name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add scoring systems for filtering
        context['scoring_systems'] = get_organization_queryset(StandaloneScoringSystem, self.request.user)
        
        # Add categories for filtering
        context['categories'] = get_organization_queryset(Category, self.request.user)
        
        # Add filter values
        context['selected_system'] = self.request.GET.get('system', '')
        context['selected_category'] = self.request.GET.get('category', '')
        
        return context

class ScoringCriterionCreateView(LoginRequiredMixin, CreateView):
    """Create a new scoring criterion."""
    model = StandaloneScoringCriterion
    form_class = ScoringCriterionForm
    template_name = 'competitions/standalone_scoring/admin/scoring_criterion_form.html'
    
    def get_success_url(self):
        return reverse('competitions:standalone_scoring:scoring_criterion_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        
        # Pass scoring system ID if provided
        system_id = self.request.GET.get('system')
        if system_id:
            kwargs['initial'] = kwargs.get('initial', {})
            kwargs['initial']['scoring_system'] = system_id
        
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Scoring criterion created successfully."))
        return super().form_valid(form)

class ScoringCriterionUpdateView(LoginRequiredMixin, UpdateView):
    """Update an existing scoring criterion."""
    model = StandaloneScoringCriterion
    form_class = ScoringCriterionForm
    template_name = 'competitions/standalone_scoring/admin/scoring_criterion_form.html'
    
    def get_success_url(self):
        return reverse('competitions:standalone_scoring:scoring_criterion_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Scoring criterion updated successfully."))
        return super().form_valid(form)

class CategoryScoringConfigView(LoginRequiredMixin, View):
    """View for managing category scoring configuration."""
    template_name = 'competitions/standalone_scoring/admin/category_scoring_config.html'
    
    def get(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        
        # Get or create config
        config = StandaloneCategoryScoringConfig.objects.filter(category_id=category_id).first()
        
        if config:
            form = CategoryScoringConfigForm(instance=config)
        else:
            form = CategoryScoringConfigForm(initial={'category_id': category_id})
        
        # Get scoring systems for context
        scoring_systems = get_organization_queryset(StandaloneScoringSystem, self.request.user)
        
        context = {
            'form': form,
            'category': category,
            'config': config,
            'scoring_systems': scoring_systems
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        
        # Get or create config
        config = StandaloneCategoryScoringConfig.objects.filter(category_id=category_id).first()
        
        if config:
            form = CategoryScoringConfigForm(request.POST, instance=config)
        else:
            form = CategoryScoringConfigForm(request.POST, initial={'category_id': category_id})
        
        if form.is_valid():
            config = form.save(commit=False)
            config.category_id = category_id
            config.save()
            messages.success(request, _("Category scoring configuration saved successfully."))
            return redirect('competitions:standalone_scoring:category_scoring_config', category_id=category_id)
        
        # Get scoring systems for context
        scoring_systems = get_organization_queryset(StandaloneScoringSystem, self.request.user)
        
        context = {
            'form': form,
            'category': category,
            'config': config,
            'scoring_systems': scoring_systems
        }
        
        return render(request, self.template_name, context)

class ResultsCalculationView(LoginRequiredMixin, View):
    """View for calculating results for a category."""
    
    def post(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        competition_id = request.POST.get('competition_id')
        round_type = request.POST.get('round_type')
        
        if not competition_id:
            messages.error(request, _("Competition ID is required."))
            return redirect('competitions:standalone_scoring:scoring_dashboard')
        
        # Get category config
        config = StandaloneCategoryScoringConfig.objects.filter(category_id=category_id).first()
        
        if not config:
            messages.error(request, _("No scoring configuration found for this category."))
            return redirect('competitions:standalone_scoring:scoring_dashboard')
        
        # Get all performances for this category and competition
        performances_query = StandalonePerformance.objects.filter(
            category_id=category_id,
            competition_id=competition_id,
            status=StandalonePerformance.COMPLETED
        )
        
        # Filter by round type if provided
        if round_type:
            performances_query = performances_query.filter(round_type=round_type)
        
        performances = performances_query.order_by('round_type', 'round_number')
        
        if not performances:
            messages.warning(request, _("No completed performances found for this category."))
            return redirect('competitions:standalone_scoring:scoring_dashboard')
        
        try:
            with transaction.atomic():
                # Process each performance
                performance_scores = []
                
                for performance in performances:
                    # Get all scores for this performance
                    scores = StandaloneScore.objects.filter(performance=performance)
                    
                    # Group scores by criterion
                    criteria_data = {}
                    for score in scores:
                        if score.criterion_id not in criteria_data:
                            criterion = score.criterion
                            criteria_data[score.criterion_id] = {
                                'criterion_id': score.criterion_id,
                                'criterion_name': criterion.name,
                                'criterion_weight': float(criterion.weight),
                                'judge_scores': []
                            }
                        
                        criteria_data[score.criterion_id]['judge_scores'].append(float(score.value))
                    
                    # Skip if no scores
                    if not criteria_data:
                        continue
                    
                    # Convert to list for calculator
                    criteria_list = list(criteria_data.values())
                    
                    # Calculate final score
                    calculator = StandaloneScoreCalculator(
                        min_score=float(config.get_effective_min_score()),
                        max_score=float(config.get_effective_max_score()),
                        exclude_extreme_scores=config.get_effective_exclude_extreme_scores()
                    )
                    
                    if config.scoring_system.system_type == StandaloneScoringSystem.STANDARD:
                        result = calculator.calculate_weighted_average(criteria_list)
                    elif config.scoring_system.system_type == StandaloneScoringSystem.POINT:
                        result = calculator.calculate_point_score(criteria_list)
                    else:
                        # For direct elimination and custom scoring, just use the first result
                        # or implement custom logic here
                        continue
                    
                    # Add to performance scores list
                    performance_scores.append({
                        'performance_id': performance.id,
                        'practitioner_id': performance.practitioner_id,
                        'final_score': result['final_score']
                    })
                
                # Generate rankings
                rankings = calculator.generate_rankings(
                    performance_scores,
                    allow_ties=config.get_effective_allow_ties()
                )
                
                # Handle special case for third place ties (multiple bronze medals)
                rankings = calculator.handle_third_place_tie(rankings)
                
                # Save rankings to database
                for rank_data in rankings:
                    StandaloneCompetitionRanking.objects.update_or_create(
                        competition_id=competition_id,
                        category_id=category_id,
                        practitioner_id=rank_data['practitioner_id'],
                        defaults={
                            'performance_id': rank_data['performance_id'],
                            'rank': rank_data['rank'],
                            'final_score': rank_data['final_score'],
                            'is_tie': rank_data['is_tie'],
                            'medal': rank_data['medal'],
                            'is_published': False,
                            'notes': ''
                        }
                    )
                
                messages.success(
                    request, 
                    _("Results calculated and rankings created successfully for {0}.").format(category.name)
                )
                
        except Exception as e:
            messages.error(request, _("Error calculating results: {0}").format(str(e)))
        
        return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)

class RankingsListView(LoginRequiredMixin, ListView):
    """List view for rankings in a category."""
    template_name = 'competitions/standalone_scoring/admin/rankings_list.html'
    context_object_name = 'rankings'
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        category_id = self.kwargs.get('category_id')
        competition_id = self.request.GET.get('competition')
        
        queryset = StandaloneCompetitionRanking.objects.filter(category_id=category_id)
        
        if competition_id:
            queryset = queryset.filter(competition_id=competition_id)
        
        queryset = queryset.order_by('rank')
        
        # Add practitioner names
        for ranking in queryset:
            try:
                practitioner = Practitioner.objects.get(id=ranking.practitioner_id)
                ranking.practitioner_name = f"{practitioner.first_name} {practitioner.last_name}"
            except Practitioner.DoesNotExist:
                ranking.practitioner_name = f"Practitioner #{ranking.practitioner_id}"
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_id = self.kwargs.get('category_id')
        
        try:
            category = Category.objects.get(id=category_id)
            context['category'] = category
        except Category.DoesNotExist:
            context['category_name'] = f"Category #{category_id}"
        
        # Get competitions for filtering
        competitions = Competition.objects.filter(
            id__in=StandaloneCompetitionRanking.objects.filter(
                category_id=category_id
            ).values_list('competition_id', flat=True).distinct()
        )
        
        context['competitions'] = competitions
        context['selected_competition'] = self.request.GET.get('competition', '')
        
        # Check if rankings are published
        published = all(ranking.is_published for ranking in self.get_queryset())
        context['is_published'] = published
        
        # Get existing snapshots
        snapshots = StandaloneCategoryRankingSnapshot.objects.filter(
            category_id=category_id
        ).order_by('-created_at')
        
        context['snapshots'] = snapshots
        
        return context

class RankingsPublishView(LoginRequiredMixin, View):
    """View for publishing rankings."""
    
    def post(self, request, category_id):
        competition_id = request.POST.get('competition_id')
        
        if not competition_id:
            messages.error(request, _("Competition ID is required."))
            return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)
        
        # Get rankings
        rankings = StandaloneCompetitionRanking.objects.filter(
            category_id=category_id,
            competition_id=competition_id
        )
        
        if not rankings:
            messages.warning(request, _("No rankings found for this category and competition."))
            return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)
        
        # Update rankings to be published
        rankings.update(is_published=True)
        
        messages.success(request, _("Rankings published successfully."))
        return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)

class CreateRankingSnapshotView(LoginRequiredMixin, View):
    """View for creating a snapshot of current rankings."""
    
    def post(self, request, category_id):
        competition_id = request.POST.get('competition_id')
        name = request.POST.get('name', '')
        notes = request.POST.get('notes', '')
        is_final = 'is_final' in request.POST
        
        if not competition_id:
            messages.error(request, _("Competition ID is required."))
            return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)
        
        # Get rankings
        rankings = StandaloneCompetitionRanking.objects.filter(
            category_id=category_id,
            competition_id=competition_id
        ).order_by('rank')
        
        if not rankings:
            messages.warning(request, _("No rankings found for this category and competition."))
            return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)
        
        try:
            with transaction.atomic():
                # Create snapshot
                snapshot = StandaloneCategoryRankingSnapshot.objects.create(
                    category_id=category_id,
                    competition_id=competition_id,
                    created_by_id=request.user.id,
                    is_published=True,
                    is_final=is_final,
                    name=name,
                    notes=notes
                )
                
                # Create entries
                for ranking in rankings:
                    StandaloneRankingSnapshotEntry.objects.create(
                        snapshot=snapshot,
                        practitioner_id=ranking.practitioner_id,
                        rank=ranking.rank,
                        final_score=ranking.final_score,
                        is_tie=ranking.is_tie,
                        medal=ranking.medal
                    )
                
                messages.success(request, _("Ranking snapshot created successfully."))
                
        except Exception as e:
            messages.error(request, _("Error creating snapshot: {0}").format(str(e)))
        
        return redirect('competitions:standalone_scoring:rankings_list', category_id=category_id)
