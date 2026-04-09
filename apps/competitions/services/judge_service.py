# apps/competitions/services/judge_service.py
"""
Service class for technical judge operations.
Implements PROMPT 7 - Judge Dashboard Toggle feature.
"""

from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta

# Import AdHocJudge pour récupérer les assignations via ce modèle
try:
    from ..models.adhoc_judges import AdHocJudge
except ImportError:
    AdHocJudge = None


class JudgeService:
    """
    Service class providing business logic for technical judge dashboard.
    """

    @staticmethod
    def can_switch_to_judge_view(practitioner):
        """
        Check if a practitioner can switch to judge view.

        Returns True if:
        - Practitioner has a Judge profile
        - Judge.is_technical_judge is True
        - Judge.active is True

        Args:
            practitioner: Practitioner instance

        Returns:
            bool: True if can switch to judge view
        """
        if not practitioner:
            return False

        try:
            judge = practitioner.judge
            return (
                judge is not None and
                judge.is_technical_judge and
                judge.active
            )
        except Exception:
            return False

    @staticmethod
    def get_judge_for_practitioner(practitioner):
        """
        Get Judge profile for a practitioner.

        Args:
            practitioner: Practitioner instance

        Returns:
            Judge instance or None
        """
        if not practitioner:
            return None

        try:
            return practitioner.judge
        except Exception:
            return None

    @staticmethod
    def get_current_assignments(judge):
        """
        Get current competition assignments for a judge.
        Returns assignments for competitions happening today.
        Includes both JudgeAssignment and AdHocJudge assignments.

        Args:
            judge: Judge instance

        Returns:
            List of assignment-like objects (dict or JudgeAssignment)
        """
        from ..models import JudgeAssignment, CompetitionRegistration

        if not judge:
            return []

        today = timezone.now().date()
        assignments = []

        # 1. Try to get assignments via JudgeAssignment model
        try:
            # Construire le filtre Q en tenant compte que judge.user peut être None
            q_filter = Q(registration__practitioner=judge.practitioner)
            if judge.user:
                q_filter |= Q(user=judge.user)

            judge_assignments = JudgeAssignment.objects.filter(
                q_filter,
                category__competition__start_date__lte=today,
                category__competition__end_date__gte=today,
                status__in=['confirmed', 'pending']
            ).select_related(
                'category',
                'category__competition',
                'registration'
            ).order_by('category__competition__start_date', 'start_time')
            assignments.extend(list(judge_assignments))
        except Exception:
            pass

        # 2. Get assignments via AdHocJudge (assigned_categories)
        if AdHocJudge is not None:
            try:
                adhoc_assignments = AdHocJudge.objects.filter(
                    practitioner=judge.practitioner,
                    status='active',
                    competition__start_date__lte=today,
                    competition__end_date__gte=today
                ).prefetch_related('assigned_categories', 'assigned_categories__competition').select_related('competition')

                for adhoc in adhoc_assignments:
                    for category in adhoc.assigned_categories.all():
                        # Pré-calculer le display du type de juge
                        assignment_type_display = dict(AdHocJudge.JUDGE_TYPE_CHOICES).get(adhoc.judge_type, adhoc.judge_type)

                        # Créer un objet dict compatible avec JudgeAssignment
                        assignments.append({
                            'id': f'adhoc_{adhoc.id}_{category.id}',
                            'category': category,
                            'competition': adhoc.competition,
                            'assignment_type': adhoc.judge_type,
                            'assignment_type_display': assignment_type_display,
                            'status': 'confirmed',
                            'start_time': None,
                            'end_time': None,
                            'tatami': None,
                            'is_adhoc': True,
                            'adhoc_judge': adhoc,
                        })
            except Exception:
                pass

        return assignments

    @staticmethod
    def get_upcoming_assignments(judge):
        """
        Get upcoming competition assignments for a judge.
        Includes both JudgeAssignment and AdHocJudge assignments.

        Args:
            judge: Judge instance

        Returns:
            List of assignment-like objects (dict or JudgeAssignment)
        """
        from ..models import JudgeAssignment

        if not judge:
            return []

        today = timezone.now().date()
        assignments = []

        # 1. Get assignments via JudgeAssignment model
        try:
            # Construire le filtre Q en tenant compte que judge.user peut être None
            q_filter = Q(registration__practitioner=judge.practitioner)
            if judge.user:
                q_filter |= Q(user=judge.user)

            judge_assignments = JudgeAssignment.objects.filter(
                q_filter,
                category__competition__start_date__gt=today,
                status__in=['confirmed', 'pending']
            ).select_related(
                'category',
                'category__competition',
                'registration'
            ).order_by('category__competition__start_date')
            assignments.extend(list(judge_assignments))
        except Exception:
            pass

        # 2. Get assignments via AdHocJudge (assigned_categories)
        if AdHocJudge is not None:
            try:
                adhoc_assignments = AdHocJudge.objects.filter(
                    practitioner=judge.practitioner,
                    status='active',
                    competition__start_date__gt=today
                ).prefetch_related(
                    'assigned_categories',
                    'assigned_categories__competition'
                ).select_related('competition')

                for adhoc in adhoc_assignments:
                    for category in adhoc.assigned_categories.all():
                        # Pré-calculer le display du type de juge
                        type_display = dict(AdHocJudge.JUDGE_TYPE_CHOICES).get(
                            adhoc.judge_type, adhoc.judge_type
                        )
                        assignments.append({
                            'id': f'adhoc_{adhoc.id}_{category.id}',
                            'category': category,
                            'competition': adhoc.competition,
                            'assignment_type': adhoc.judge_type,
                            'assignment_type_display': type_display,
                            'status': 'confirmed',
                            'start_time': None,
                            'end_time': None,
                            'tatami': None,
                            'is_adhoc': True,
                            'adhoc_judge': adhoc,
                        })
            except Exception:
                pass

        return assignments

    @staticmethod
    def get_pending_performances(judge):
        """
        Get performances waiting to be scored by this judge.

        Args:
            judge: Judge instance

        Returns:
            QuerySet of Performance objects that need scoring
        """
        from ..models import JudgeAssignment, JudgeSubmissionStatus
        from ..models.technical_scoring import Performance

        if not judge:
            return Performance.objects.none()

        today = timezone.now().date()

        try:
            # Get categories where judge is assigned
            assigned_category_ids = JudgeAssignment.objects.filter(
                Q(registration__practitioner=judge.practitioner) | Q(user=judge.user),
                status='confirmed',
                category__competition__start_date__lte=today,
                category__competition__end_date__gte=today
            ).values_list('category_id', flat=True)

            # Get performances in those categories that are pending scoring
            pending_performances = Performance.objects.filter(
                category_id__in=assigned_category_ids,
                status__in=['ready', 'in_progress', 'pending_validation']
            ).exclude(
                # Exclude performances already scored by this judge
                id__in=JudgeSubmissionStatus.objects.filter(
                    judge=judge,
                    submitted=True
                ).values_list('performance_id', flat=True)
            ).select_related(
                'practitioner',
                'category',
                'category__competition'
            ).order_by('order', 'scheduled_time')

            return pending_performances
        except Exception:
            return Performance.objects.none()

    @staticmethod
    def get_pending_performances_count(judge):
        """
        Get count of pending performances for badge display.

        Args:
            judge: Judge instance

        Returns:
            int: Number of pending performances
        """
        performances = JudgeService.get_pending_performances(judge)
        return performances.count() if performances else 0

    @staticmethod
    def get_today_schedule(judge):
        """
        Get today's schedule for a judge including assigned categories and times.

        Args:
            judge: Judge instance

        Returns:
            List of schedule items with competition, category, time info
        """
        from ..models import JudgeAssignment
        from ..models.technical_scoring import Performance

        if not judge:
            return []

        today = timezone.now().date()
        schedule = []

        try:
            # Get today's assignments
            assignments = JudgeAssignment.objects.filter(
                Q(registration__practitioner=judge.practitioner) | Q(user=judge.user),
                category__competition__start_date__lte=today,
                category__competition__end_date__gte=today,
                status='confirmed'
            ).select_related(
                'category',
                'category__competition'
            ).order_by('start_time', 'category__competition__title')

            for assignment in assignments:
                # Count performances in this category
                total_performances = Performance.objects.filter(
                    category=assignment.category
                ).count()

                scored_performances = Performance.objects.filter(
                    category=assignment.category,
                    status='completed'
                ).count()

                schedule.append({
                    'assignment': assignment,
                    'competition': assignment.category.competition,
                    'category': assignment.category,
                    'start_time': assignment.start_time,
                    'end_time': assignment.end_time,
                    'tatami': assignment.tatami,
                    'assignment_type': assignment.get_assignment_type_display(),
                    'total_performances': total_performances,
                    'scored_performances': scored_performances,
                    'pending_performances': total_performances - scored_performances,
                })

            return schedule
        except Exception:
            return []

    @staticmethod
    def get_judge_stats(judge):
        """
        Get statistics for judge dashboard.

        Args:
            judge: Judge instance

        Returns:
            dict: Statistics including assignments count, experience, etc.
        """
        from ..models import JudgeAssignment
        from ..models.technical_scoring import TechnicalScore
        from django.db.models import Avg

        if not judge:
            return {
                'total_assignments': 0,
                'completed_assignments': 0,
                'upcoming_assignments': 0,
                'total_scores_given': 0,
                'total_competitions': 0,
                'average_score': None,
                'qualification_level': 'N/A',
                'experience_years': 0,
            }

        today = timezone.now().date()

        try:
            total_assignments = JudgeAssignment.objects.filter(
                Q(registration__practitioner=judge.practitioner) | Q(user=judge.user)
            ).count()

            completed_assignments = JudgeAssignment.objects.filter(
                Q(registration__practitioner=judge.practitioner) | Q(user=judge.user),
                status='completed'
            ).count()

            upcoming_count = JudgeAssignment.objects.filter(
                Q(registration__practitioner=judge.practitioner) | Q(user=judge.user),
                category__competition__start_date__gt=today,
                status__in=['confirmed', 'pending']
            ).count()

            # Resolve the actual user (judge.user may be None)
            actual_user = judge.user or (
                judge.practitioner.user if judge.practitioner else None
            )

            # Query TechnicalScore (judge is User FK)
            ts_qs = TechnicalScore.objects.filter(
                judge=actual_user,
                is_active_for_ranking=True
            ) if actual_user else TechnicalScore.objects.none()
            total_scores = ts_qs.count()
            total_competitions = ts_qs.values(
                'performance__competition'
            ).distinct().count()
            avg_score = ts_qs.aggregate(
                avg=Avg('value')
            )['avg']

            return {
                'total_assignments': total_assignments,
                'completed_assignments': completed_assignments,
                'upcoming_assignments': upcoming_count,
                'total_scores_given': total_scores,
                'total_competitions': total_competitions,
                'average_score': round(float(avg_score), 2) if avg_score else None,
                'qualification_level': judge.get_qualification_level_display() if judge else 'N/A',
                'experience_years': judge.years_experience if judge else 0,
            }
        except Exception:
            return {
                'total_assignments': 0,
                'completed_assignments': 0,
                'upcoming_assignments': 0,
                'total_scores_given': 0,
                'total_competitions': 0,
                'average_score': None,
                'qualification_level': judge.get_qualification_level_display() if judge else 'N/A',
                'experience_years': judge.years_experience if judge else 0,
            }

    @staticmethod
    def get_recent_competitions(judge, limit=5):
        """
        Get recent competitions where judge participated.

        Args:
            judge: Judge instance
            limit: Maximum number of competitions to return

        Returns:
            List of Competition objects
        """
        from ..models import JudgeAssignment, Competition
        from ..models.technical_scoring import TechnicalScore

        if not judge:
            return []

        try:
            # Resolve the actual user (judge.user may be None)
            actual_user = judge.user or (
                judge.practitioner.user if judge.practitioner else None
            )

            # Find competitions via JudgeAssignment (any status)
            q_filter = Q(registration__practitioner=judge.practitioner)
            if actual_user:
                q_filter = q_filter | Q(user=actual_user)
            assignment_comp_ids = set(
                JudgeAssignment.objects.filter(
                    q_filter
                ).values_list('category__competition_id', flat=True).distinct()
            )

            # Also find competitions via TechnicalScore (actual scoring data)
            scored_comp_ids = set()
            if actual_user:
                scored_comp_ids = set(
                    TechnicalScore.objects.filter(
                        judge=actual_user,
                        is_active_for_ranking=True
                    ).values_list(
                        'performance__competition_id', flat=True
                    ).distinct()
                )

            all_comp_ids = assignment_comp_ids | scored_comp_ids

            if not all_comp_ids:
                return []

            return Competition.objects.filter(
                id__in=all_comp_ids
            ).order_by('-end_date')[:limit]
        except Exception:
            return []

    @staticmethod
    def get_past_assignments(judge):
        """
        Get past competition assignments for a judge.
        Includes both JudgeAssignment and AdHocJudge assignments.

        Args:
            judge: Judge instance

        Returns:
            List of assignment-like objects
        """
        from ..models import JudgeAssignment

        if not judge:
            return []

        today = timezone.now().date()
        assignments = []

        # 1. JudgeAssignment records
        try:
            q_filter = Q(registration__practitioner=judge.practitioner)
            if judge.user:
                q_filter |= Q(user=judge.user)

            judge_assignments = JudgeAssignment.objects.filter(
                q_filter,
                category__competition__end_date__lt=today
            ).select_related(
                'category',
                'category__competition',
                'registration'
            ).order_by('-category__competition__end_date')[:20]
            assignments.extend(list(judge_assignments))
        except Exception:
            pass

        # 2. AdHocJudge assignments for past competitions
        if AdHocJudge is not None:
            try:
                adhoc_assignments = AdHocJudge.objects.filter(
                    practitioner=judge.practitioner,
                    status='active',
                    competition__end_date__lt=today
                ).prefetch_related(
                    'assigned_categories',
                    'assigned_categories__competition'
                ).select_related('competition')

                for adhoc in adhoc_assignments:
                    for category in adhoc.assigned_categories.all():
                        type_display = dict(AdHocJudge.JUDGE_TYPE_CHOICES).get(
                            adhoc.judge_type, adhoc.judge_type
                        )
                        assignments.append({
                            'id': f'adhoc_{adhoc.id}_{category.id}',
                            'category': category,
                            'competition': adhoc.competition,
                            'assignment_type': adhoc.judge_type,
                            'assignment_type_display': type_display,
                            'status': 'confirmed',
                            'start_time': None,
                            'end_time': None,
                            'tatami': None,
                            'is_adhoc': True,
                            'adhoc_judge': adhoc,
                        })
            except Exception:
                pass

        return assignments

    @staticmethod
    def get_scored_performances(judge):
        """
        Get performances that have been scored by this judge.

        Args:
            judge: Judge instance

        Returns:
            QuerySet of Performance objects that were scored
        """
        from ..models import JudgeSubmissionStatus
        from ..models.technical_scoring import Performance

        if not judge:
            return Performance.objects.none()

        try:
            # Get performances scored by this judge
            scored_performance_ids = JudgeSubmissionStatus.objects.filter(
                judge=judge,
                submitted=True
            ).values_list('performance_id', flat=True)

            return Performance.objects.filter(
                id__in=scored_performance_ids
            ).select_related(
                'practitioner',
                'category',
                'category__competition'
            ).order_by('-created_at')[:50]
        except Exception:
            return Performance.objects.none()
