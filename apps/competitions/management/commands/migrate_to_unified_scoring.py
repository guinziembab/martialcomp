import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

logger = logging.getLogger(__name__)

# Import User model directly to avoid import errors
try:
    from apps.competitions.models.users import User
except ImportError:
    # Fallback to Django's default user model
    from django.contrib.auth import get_user_model
    User = get_user_model()

class Command(BaseCommand):
    help = 'Migrates data from old scoring models to the new unified scoring system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry run mode without making any actual changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Provide detailed output during migration'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode. No changes will be made.'))
        
        try:
            with transaction.atomic():
                self.migrate_scoring_systems(verbose)
                self.migrate_scoring_criteria(verbose)
                self.migrate_category_configs(verbose)
                self.migrate_performances(verbose)
                self.migrate_scores(verbose)
                self.migrate_judge_submissions(verbose)
                self.migrate_rankings(verbose)
                
                if dry_run:
                    # Rollback transaction in dry run mode
                    self.stdout.write(self.style.WARNING('DRY RUN completed. Rolling back changes.'))
                    transaction.set_rollback(True)
                else:
                    self.stdout.write(self.style.SUCCESS('Migration completed successfully.'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during migration: {str(e)}'))
            logger.exception('Migration failed')
            return
    
    def migrate_scoring_systems(self, verbose):
        """
        Migrate scoring systems from old models to the new unified model.
        """
        try:
            from apps.competitions.models.scoring import ScoringSystem as OldScoringSystem
            from apps.competitions.models.unified_scoring import ScoringSystem
            
            old_systems = OldScoringSystem.objects.all()
            self.stdout.write(f'Migrating {old_systems.count()} scoring systems...')
            
            systems_created = 0
            
            for old_system in old_systems:
                # Check if a system with the same name already exists
                existing = ScoringSystem.objects.filter(name=old_system.name).first()
                
                if existing:
                    if verbose:
                        self.stdout.write(f'  Scoring system "{old_system.name}" already exists, skipping.')
                    continue
                
                # Create new scoring system
                ScoringSystem.objects.create(
                    name=old_system.name or f"System {old_system.id}",
                    description=old_system.description or '',
                    system_type=old_system.system_type,
                    min_score=old_system.min_score,
                    max_score=old_system.max_score,
                    score_step=old_system.score_step,
                    exclude_extreme_scores=old_system.exclude_extreme_scores,
                    allow_ties=old_system.allow_ties,
                    real_time_results=True,  # Default to true for old systems
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                systems_created += 1
                
                if verbose:
                    self.stdout.write(f'  Created scoring system: {old_system.name}')
            
            self.stdout.write(self.style.SUCCESS(f'Created {systems_created} new scoring systems.'))
            return systems_created
            
        except ImportError:
            self.stdout.write(self.style.WARNING('Could not import ScoringSystem from scoring.py. Creating default system instead.'))
            from apps.competitions.models.unified_scoring import ScoringSystem
            
            # Create default scoring system
            if not ScoringSystem.objects.exists():
                ScoringSystem.objects.create(
                    name="Default Standard Scoring",
                    description="Default scoring system created during migration",
                    system_type='standard',
                    min_score=0.0,
                    max_score=10.0,
                    score_step=0.1,
                    exclude_extreme_scores=True,
                    allow_ties=True,
                    real_time_results=True
                )
                self.stdout.write(self.style.SUCCESS('Created default scoring system.'))
                systems_created = 1
            else:
                self.stdout.write(self.style.SUCCESS('Scoring system already exists, skipping.'))
                systems_created = 0
            
            return systems_created
    
    def migrate_scoring_criteria(self, verbose):
        """
        Migrate scoring criteria from old models to the new unified model.
        """
        # Try to import from all potential sources
        old_criteria_sources = []
        
        try:
            from apps.competitions.models.scoring_criteria import ScoringCriterion as OldScoringCriterion1
            old_criteria_sources.append(OldScoringCriterion1.objects.all())
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import ScoringCriterion from scoring_criteria.py'))
        
        try:
            from apps.competitions.models.scoring import ScoringCriterion as OldScoringCriterion2
            old_criteria_sources.append(OldScoringCriterion2.objects.all())
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import ScoringCriterion from scoring.py'))
        
        try:
            from apps.competitions.models.technical_scoring import ScoringCriterion as OldScoringCriterion3
            old_criteria_sources.append(OldScoringCriterion3.objects.all())
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import ScoringCriterion from technical_scoring.py'))
        
        from apps.competitions.models.unified_scoring import ScoringCriterion, ScoringSystem
        
        criteria_created = 0
        
        for old_criteria_source in old_criteria_sources:
            if not old_criteria_source.exists():
                continue
                
            self.stdout.write(f'Migrating {old_criteria_source.count()} scoring criteria...')
            
            for old_criterion in old_criteria_source:
                # Try to find an appropriate scoring system
                if hasattr(old_criterion, 'scoring_system') and old_criterion.scoring_system:
                    # Try to find the matching new scoring system
                    try:
                        scoring_system = ScoringSystem.objects.get(name=old_criterion.scoring_system.name)
                    except (ScoringSystem.DoesNotExist, AttributeError):
                        # Use the first scoring system as a fallback
                        scoring_system = ScoringSystem.objects.first()
                        if not scoring_system:
                            # Create a default scoring system if none exists
                            scoring_system = ScoringSystem.objects.create(
                                name="Default System",
                                system_type=ScoringSystem.STANDARD,
                                min_score=0.0,
                                max_score=10.0,
                                score_step=0.1,
                            )
                else:
                    # Use the first scoring system
                    scoring_system = ScoringSystem.objects.first()
                
                # Get the category if it exists
                category = None
                if hasattr(old_criterion, 'category') and old_criterion.category:
                    category = old_criterion.category
                
                # Skip if this criterion already exists for this category
                if category and ScoringCriterion.objects.filter(
                    category=category,
                    name=old_criterion.name
                ).exists():
                    if verbose:
                        self.stdout.write(f'  Criterion "{old_criterion.name}" already exists for this category, skipping.')
                    continue
                
                # Create the new criterion
                ScoringCriterion.objects.create(
                    scoring_system=scoring_system,
                    category=category,
                    name=old_criterion.name,
                    description=getattr(old_criterion, 'description', '') or '',
                    weight=getattr(old_criterion, 'weight', 1.0),
                    min_score=getattr(old_criterion, 'min_score', scoring_system.min_score),
                    max_score=getattr(old_criterion, 'max_score', scoring_system.max_score),
                    step=getattr(old_criterion, 'step', scoring_system.score_step),
                    order=getattr(old_criterion, 'order', 0),
                    is_active=True,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                criteria_created += 1
                
                if verbose:
                    self.stdout.write(f'  Created criterion: {old_criterion.name}')
        
        if criteria_created == 0:
            # Create default criteria if none were migrated
            scoring_system = ScoringSystem.objects.first()
            if scoring_system:
                default_criteria = [
                    {'name': 'Technique', 'weight': 1.0, 'order': 1},
                    {'name': 'Power', 'weight': 0.8, 'order': 2},
                    {'name': 'Balance', 'weight': 0.7, 'order': 3},
                    {'name': 'Overall Impression', 'weight': 1.2, 'order': 4},
                ]
                
                for crit in default_criteria:
                    ScoringCriterion.objects.create(
                        scoring_system=scoring_system,
                        name=crit['name'],
                        weight=crit['weight'],
                        order=crit['order'],
                        min_score=scoring_system.min_score,
                        max_score=scoring_system.max_score,
                        step=scoring_system.score_step,
                        is_active=True
                    )
                    criteria_created += 1
                    
                    if verbose:
                        self.stdout.write(f'  Created default criterion: {crit["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {criteria_created} new scoring criteria.'))
    
    def migrate_category_configs(self, verbose):
        """
        Migrate category scoring configurations from old models to the new unified model.
        """
        try:
            from apps.competitions.models.scoring import CategoryScoringConfig as OldCategoryScoringConfig
            old_configs = OldCategoryScoringConfig.objects.all()
        except (ImportError, AttributeError):
            self.stdout.write('No old CategoryScoringConfig model found, creating defaults if needed.')
            old_configs = []
        
        from apps.competitions.models.unified_scoring import CategoryScoringConfig, ScoringSystem
        from apps.competitions.models.competitions import CompetitionCategory
        
        if old_configs:
            self.stdout.write(f'Migrating {len(old_configs)} category scoring configurations...')
        
        configs_created = 0
        
        for old_config in old_configs:
            # Check if config already exists for this category
            if CategoryScoringConfig.objects.filter(category=old_config.category).exists():
                if verbose:
                    self.stdout.write(f'  Config for category {old_config.category} already exists, skipping.')
                continue
            
            # Try to find the matching new scoring system
            try:
                scoring_system = ScoringSystem.objects.get(name=old_config.scoring_system.name)
            except (ScoringSystem.DoesNotExist, AttributeError):
                # Use the first scoring system as a fallback
                scoring_system = ScoringSystem.objects.first()
                if not scoring_system:
                    self.stdout.write(self.style.WARNING('  No scoring system found, skipping category config.'))
                    continue
            
            # Create new config
            CategoryScoringConfig.objects.create(
                category=old_config.category,
                scoring_system=scoring_system,
                override_min_score=old_config.override_min_score,
                override_max_score=old_config.override_max_score,
                override_score_step=old_config.override_score_step,
                exclude_extreme_scores=getattr(old_config, 'exclude_extreme_scores', None),
                allow_ties=getattr(old_config, 'allow_ties', None),
                real_time_results=getattr(old_config, 'real_time_results', None),
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            configs_created += 1
            
            if verbose:
                self.stdout.write(f'  Created config for category: {old_config.category}')
        
        # Create default configs for categories without them
        if configs_created == 0:
            # Get default scoring system
            scoring_system = ScoringSystem.objects.first()
            if not scoring_system:
                self.stdout.write(self.style.WARNING('No scoring system found, skipping default configs.'))
                return
            
            # Get categories without configs
            categories_without_configs = CompetitionCategory.objects.exclude(
                id__in=CategoryScoringConfig.objects.values_list('category_id', flat=True)
            )
            
            for category in categories_without_configs:
                CategoryScoringConfig.objects.create(
                    category=category,
                    scoring_system=scoring_system,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                configs_created += 1
                
                if verbose:
                    self.stdout.write(f'  Created default config for category: {category}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {configs_created} new category scoring configurations.'))
    
    def migrate_performances(self, verbose):
        """
        Migrate performances from old models to the new unified model.
        """
        # Try to import from all potential sources
        performance_sources = []
        
        try:
            from apps.competitions.models.scoring import Performance as OldPerformance1
            performance_sources.append(('scoring.Performance', OldPerformance1.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import Performance from scoring.py'))
        
        try:
            from apps.competitions.models.technical_scoring import TechnicalPerformance as OldPerformance2
            performance_sources.append(('technical_scoring.TechnicalPerformance', OldPerformance2.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import TechnicalPerformance from technical_scoring.py'))
        
        try:
            from apps.competitions.models.scoring_results import TechnicalPerformanceResult as OldPerformance3
            performance_sources.append(('scoring_results.TechnicalPerformanceResult', OldPerformance3.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import TechnicalPerformanceResult from scoring_results.py'))
        
        from apps.competitions.models.unified_scoring import Performance
        
        performances_created = 0
        
        for source_name, old_performances in performance_sources:
            if not old_performances.exists():
                continue
                
            self.stdout.write(f'Migrating {old_performances.count()} performances from {source_name}...')
            
            for old_perf in old_performances:
                # Skip if this performance already exists
                existing = Performance.objects.filter(
                    category=old_perf.category,
                    practitioner=old_perf.practitioner,
                    round_type=getattr(old_perf, 'round_type', Performance.PRELIMINARY),
                    round_number=getattr(old_perf, 'round_number', 1)
                ).first()
                
                if existing:
                    if verbose:
                        self.stdout.write(f'  Performance for {old_perf.practitioner} in {old_perf.category} already exists, skipping.')
                    continue
                
                # Map old status to new status
                status_map = {
                    'pending': Performance.PENDING,
                    'in_progress': Performance.IN_PROGRESS,
                    'completed': Performance.COMPLETED,
                    'disqualified': Performance.DISQUALIFIED,
                    'cancelled': Performance.CANCELLED,
                }
                old_status = getattr(old_perf, 'status', 'pending')
                new_status = status_map.get(old_status, Performance.PENDING)
                
                # Create new performance
                try:
                    Performance.objects.create(
                        competition=old_perf.category.competition,
                        category=old_perf.category,
                        practitioner=old_perf.practitioner,
                        round_type=getattr(old_perf, 'round_type', Performance.PRELIMINARY),
                        round_number=getattr(old_perf, 'round_number', 1),
                        performance_order=getattr(old_perf, 'performance_order', 0) or getattr(old_perf, 'order', 0) or 0,
                        status=new_status,
                        start_time=getattr(old_perf, 'start_time', None),
                        end_time=getattr(old_perf, 'end_time', None),
                        duration=getattr(old_perf, 'duration', None),
                        notes=getattr(old_perf, 'notes', '') or '',
                        disqualification_reason=getattr(old_perf, 'disqualification_reason', '') or '',
                        created_at=getattr(old_perf, 'created_at', timezone.now()),
                        updated_at=timezone.now(),
                    )
                    performances_created += 1
                    
                    if verbose:
                        self.stdout.write(f'  Created performance for: {old_perf.practitioner} in {old_perf.category}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  Error creating performance: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'Created {performances_created} new performances.'))
    
    def migrate_scores(self, verbose):
        """
        Migrate scores from old models to the new unified model.
        """
        # Try to import from all potential sources
        score_sources = []
        
        try:
            from apps.competitions.models.scoring import Score as OldScore1
            score_sources.append(('scoring.Score', OldScore1.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import Score from scoring.py'))
        
        try:
            from apps.competitions.models.technical_scoring import TechnicalScore as OldScore2
            score_sources.append(('technical_scoring.TechnicalScore', OldScore2.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import TechnicalScore from technical_scoring.py'))
        
        try:
            from apps.competitions.models.scoring_results import TechnicalScoreResult as OldScore3
            score_sources.append(('scoring_results.TechnicalScoreResult', OldScore3.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import TechnicalScoreResult from scoring_results.py'))
        
        from apps.competitions.models.unified_scoring import Score, Performance, ScoringCriterion
        
        scores_created = 0
        errors = 0
        
        for source_name, old_scores in score_sources:
            if not old_scores.exists():
                continue
                
            self.stdout.write(f'Migrating {old_scores.count()} scores from {source_name}...')
            
            for old_score in old_scores:
                try:
                    # Find the corresponding new performance
                    if hasattr(old_score, 'performance') and old_score.performance:
                        old_perf = old_score.performance
                        
                        # Try to find the matching new performance
                        try:
                            performance = Performance.objects.get(
                                category=old_perf.category,
                                practitioner=old_perf.practitioner,
                                round_type=getattr(old_perf, 'round_type', Performance.PRELIMINARY),
                                round_number=getattr(old_perf, 'round_number', 1)
                            )
                        except Performance.DoesNotExist:
                            if verbose:
                                self.stdout.write(self.style.WARNING(
                                    f'  Cannot find matching performance for score in {old_perf.category}, skipping.'
                                ))
                            errors += 1
                            continue
                    else:
                        if verbose:
                            self.stdout.write(self.style.WARNING('  Score has no performance, skipping.'))
                        errors += 1
                        continue
                    
                    # Find the criterion
                    if hasattr(old_score, 'criterion') and old_score.criterion:
                        old_criterion = old_score.criterion
                        
                        # Try to find the matching new criterion
                        criterion = ScoringCriterion.objects.filter(
                            Q(category=old_perf.category) | Q(category__isnull=True),
                            name=old_criterion.name
                        ).first()
                        
                        if not criterion:
                            # Create a new criterion if none exists
                            from apps.competitions.models.unified_scoring import ScoringSystem
                            system = ScoringSystem.objects.first()
                            
                            criterion = ScoringCriterion.objects.create(
                                scoring_system=system,
                                category=old_perf.category,
                                name=old_criterion.name,
                                weight=getattr(old_criterion, 'weight', 1.0),
                                min_score=getattr(old_criterion, 'min_score', 0.0),
                                max_score=getattr(old_criterion, 'max_score', 10.0),
                                step=getattr(old_criterion, 'step', 0.1),
                            )
                    else:
                        if verbose:
                            self.stdout.write(self.style.WARNING('  Score has no criterion, skipping.'))
                        errors += 1
                        continue
                    
                    # Skip if this score already exists
                    existing = Score.objects.filter(
                        performance=performance,
                        judge=old_score.judge,
                        criterion=criterion
                    ).first()
                    
                    if existing:
                        if verbose:
                            self.stdout.write(f'  Score already exists for this judge and criterion, skipping.')
                        continue
                    
                    # Create the new score
                    Score.objects.create(
                        performance=performance,
                        judge=old_score.judge,
                        criterion=criterion,
                        value=old_score.value,
                        original_value=getattr(old_score, 'original_value', old_score.value),
                        is_locked=getattr(old_score, 'is_locked', False),
                        is_training_score=getattr(old_score, 'is_training_score', False),
                        modified_by=getattr(old_score, 'modified_by', None),
                        notes=getattr(old_score, 'notes', '') or '',
                        created_at=getattr(old_score, 'created_at', timezone.now()),
                        updated_at=timezone.now(),
                    )
                    scores_created += 1
                    
                    if verbose:
                        self.stdout.write(f'  Created score for: {old_score.judge} - {criterion.name}')
                
                except Exception as e:
                    if verbose:
                        self.stdout.write(self.style.ERROR(f'  Error migrating score: {str(e)}'))
                    errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {scores_created} new scores with {errors} errors.'))
    
    def migrate_judge_submissions(self, verbose):
        """
        Migrate judge submission statuses from old models to the new unified model.
        """
        # Try to import from all potential sources
        submission_sources = []
        
        try:
            from apps.competitions.models.scoring import JudgeSubmission as OldSubmission1
            submission_sources.append(('scoring.JudgeSubmission', OldSubmission1.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import JudgeSubmission from scoring.py'))
        
        try:
            from apps.competitions.models.technical_scoring import JudgeSubmissionStatus as OldSubmission2
            submission_sources.append(('technical_scoring.JudgeSubmissionStatus', OldSubmission2.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import JudgeSubmissionStatus from technical_scoring.py'))
        
        try:
            from apps.competitions.models.scoring_results import JudgeSubmissionStatusResult as OldSubmission3
            submission_sources.append(('scoring_results.JudgeSubmissionStatusResult', OldSubmission3.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import JudgeSubmissionStatusResult from scoring_results.py'))
        
        from apps.competitions.models.unified_scoring import JudgeSubmission, Performance
        
        submissions_created = 0
        errors = 0
        
        for source_name, old_submissions in submission_sources:
            if not old_submissions.exists():
                continue
                
            self.stdout.write(f'Migrating {old_submissions.count()} judge submissions from {source_name}...')
            
            for old_sub in old_submissions:
                try:
                    # Find the corresponding new performance
                    if hasattr(old_sub, 'performance') and old_sub.performance:
                        old_perf = old_sub.performance
                        
                        # Try to find the matching new performance
                        try:
                            performance = Performance.objects.get(
                                category=old_perf.category,
                                practitioner=old_perf.practitioner,
                                round_type=getattr(old_perf, 'round_type', Performance.PRELIMINARY),
                                round_number=getattr(old_perf, 'round_number', 1)
                            )
                        except Performance.DoesNotExist:
                            if verbose:
                                self.stdout.write(self.style.WARNING(
                                    f'  Cannot find matching performance for submission in {old_perf.category}, skipping.'
                                ))
                            errors += 1
                            continue
                    else:
                        if verbose:
                            self.stdout.write(self.style.WARNING('  Submission has no performance, skipping.'))
                        errors += 1
                        continue
                    
                    # Skip if this submission already exists
                    existing = JudgeSubmission.objects.filter(
                        performance=performance,
                        judge=old_sub.judge
                    ).first()
                    
                    if existing:
                        if verbose:
                            self.stdout.write(f'  Submission already exists for this judge, skipping.')
                        continue
                    
                    # Create the new submission
                    JudgeSubmission.objects.create(
                        performance=performance,
                        judge=old_sub.judge,
                        is_submitted=getattr(old_sub, 'is_submitted', False),
                        submitted_at=getattr(old_sub, 'submitted_at', None),
                        notes=getattr(old_sub, 'notes', '') or '',
                    )
                    submissions_created += 1
                    
                    if verbose:
                        self.stdout.write(f'  Created submission for: {old_sub.judge} - {performance}')
                
                except Exception as e:
                    if verbose:
                        self.stdout.write(self.style.ERROR(f'  Error migrating submission: {str(e)}'))
                    errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {submissions_created} new judge submissions with {errors} errors.'))
    
    def migrate_rankings(self, verbose):
        """
        Migrate rankings from old models to the new unified model.
        """
        # Try to import from all potential sources
        ranking_sources = []
        
        try:
            from apps.competitions.models.scoring import CompetitionRanking as OldRanking1
            ranking_sources.append(('scoring.CompetitionRanking', OldRanking1.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import CompetitionRanking from scoring.py'))
        
        try:
            from apps.competitions.models.technical_scoring import CompetitionRanking as OldRanking2
            ranking_sources.append(('technical_scoring.CompetitionRanking', OldRanking2.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import CompetitionRanking from technical_scoring.py'))
        
        try:
            from apps.competitions.models.scoring_results import RankingEntry as OldRanking3
            ranking_sources.append(('scoring_results.RankingEntry', OldRanking3.objects.all()))
        except (ImportError, AttributeError):
            if verbose:
                self.stdout.write(self.style.WARNING('Could not import RankingEntry from scoring_results.py'))
        
        from apps.competitions.models.unified_scoring import CompetitionRanking, Performance
        
        rankings_created = 0
        errors = 0
        
        for source_name, old_rankings in ranking_sources:
            if not old_rankings.exists():
                continue
                
            self.stdout.write(f'Migrating {old_rankings.count()} rankings from {source_name}...')
            
            for old_rank in old_rankings:
                try:
                    # Get category and competition
                    category = getattr(old_rank, 'category', None)
                    
                    if not category:
                        # Try to get category from ranking object
                        if hasattr(old_rank, 'ranking') and hasattr(old_rank.ranking, 'category'):
                            category = old_rank.ranking.category
                    
                    if not category:
                        if verbose:
                            self.stdout.write(self.style.WARNING('  Ranking has no category, skipping.'))
                        errors += 1
                        continue
                    
                    competition = category.competition
                    
                    # Get practitioner
                    practitioner = getattr(old_rank, 'practitioner', None)
                    
                    if not practitioner:
                        if verbose:
                            self.stdout.write(self.style.WARNING('  Ranking has no practitioner, skipping.'))
                        errors += 1
                        continue
                    
                    # Try to find the performance
                    performance = None
                    if hasattr(old_rank, 'performance') and old_rank.performance:
                        old_perf = old_rank.performance
                        
                        try:
                            performance = Performance.objects.get(
                                category=category,
                                practitioner=practitioner
                            )
                        except Performance.DoesNotExist:
                            # It's okay if we can't find the performance, we'll just leave it null
                            pass
                    
                    # Skip if this ranking already exists
                    existing = CompetitionRanking.objects.filter(
                        category=category,
                        practitioner=practitioner
                    ).first()
                    
                    if existing:
                        if verbose:
                            self.stdout.write(f'  Ranking already exists for this practitioner, skipping.')
                        continue
                    
                    # Create the new ranking
                    CompetitionRanking.objects.create(
                        competition=competition,
                        category=category,
                        practitioner=practitioner,
                        performance=performance,
                        rank=getattr(old_rank, 'rank', 0),
                        final_score=getattr(old_rank, 'final_score', 0.0) or getattr(old_rank, 'score', 0.0) or 0.0,
                        is_tie=getattr(old_rank, 'is_tie', False),
                        medal=getattr(old_rank, 'medal', CompetitionRanking.NONE),
                        is_published=getattr(old_rank, 'is_published', False),
                        notes=getattr(old_rank, 'notes', '') or '',
                        created_at=getattr(old_rank, 'created_at', timezone.now()),
                        updated_at=timezone.now(),
                    )
                    rankings_created += 1
                    
                    if verbose:
                        self.stdout.write(f'  Created ranking for: {practitioner} - Rank {getattr(old_rank, "rank", 0)}')
                
                except Exception as e:
                    if verbose:
                        self.stdout.write(self.style.ERROR(f'  Error migrating ranking: {str(e)}'))
                    errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {rankings_created} new rankings with {errors} errors.'))
