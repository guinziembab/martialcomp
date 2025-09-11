import csv
import os
import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Migrates scoring data to the unified model using CSV export/import to avoid model conflicts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--export-only',
            action='store_true',
            help='Only export data to CSV without importing to new models'
        )
        parser.add_argument(
            '--import-only',
            action='store_true',
            help='Only import data from CSV to new models'
        )
        parser.add_argument(
            '--csv-dir',
            type=str,
            default='./data_migration',
            help='Directory to store CSV files'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Provide detailed output during migration'
        )

    def handle(self, *args, **options):
        export_only = options['export_only']
        import_only = options['import_only']
        csv_dir = options['csv_dir']
        verbose = options['verbose']
        
        # Create CSV directory if it doesn't exist
        if not os.path.exists(csv_dir):
            os.makedirs(csv_dir)
            
        if verbose:
            self.stdout.write(f"Using CSV directory: {csv_dir}")
        
        try:
            if not import_only:
                self.stdout.write("Exporting data to CSV...")
                self.export_scoring_systems(csv_dir, verbose)
                self.export_scoring_criteria(csv_dir, verbose)
                self.export_category_configs(csv_dir, verbose)
                self.export_performances(csv_dir, verbose)
                self.export_scores(csv_dir, verbose)
                self.export_judge_submissions(csv_dir, verbose)
                self.export_rankings(csv_dir, verbose)
                self.stdout.write(self.style.SUCCESS("Data export completed."))
            
            if not export_only:
                self.stdout.write("Importing data to new models...")
                with transaction.atomic():
                    self.import_scoring_systems(csv_dir, verbose)
                    self.import_scoring_criteria(csv_dir, verbose)
                    self.import_category_configs(csv_dir, verbose)
                    self.import_performances(csv_dir, verbose)
                    self.import_scores(csv_dir, verbose)
                    self.import_judge_submissions(csv_dir, verbose)
                    self.import_rankings(csv_dir, verbose)
                    self.stdout.write(self.style.SUCCESS("Data import completed."))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during migration: {str(e)}'))
            logger.exception('Migration failed')
            return

    def export_scoring_systems(self, csv_dir, verbose):
        """Export scoring systems to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'scoring_systems.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'name', 'description', 'system_type', 
                    'min_score', 'max_score', 'score_step', 
                    'exclude_extreme_scores', 'allow_ties'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from original scoring systems
                    cursor.execute("""
                        SELECT id, name, description, system_type, min_score, max_score, 
                               score_step, exclude_extreme_scores, allow_ties
                        FROM competitions_scoringsystem
                    """)
                    rows = cursor.fetchall()
                    
                    count = 0
                    for row in rows:
                        writer.writerow(row)
                        count += 1
                        
                    if verbose:
                        self.stdout.write(f"  Exported {count} scoring systems")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting scoring systems: {str(e)}"))

    def export_scoring_criteria(self, csv_dir, verbose):
        """Export scoring criteria to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'scoring_criteria.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'source_table', 'name', 'description', 'weight', 
                    'min_score', 'max_score', 'step', 'order',
                    'category_id', 'scoring_system_id'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from technical_scoring ScoringCriterion
                    try:
                        cursor.execute("""
                            SELECT id, 'technical_scoring', name, description, weight, 
                                   min_score, max_score, step, "order",
                                   category_id, NULL
                            FROM competitions_scoringcriterion
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} scoring criteria from technical_scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export criteria from competitions_scoringcriterion: {str(e)}"))
                    
                    # Get data from scoring_criteria ScoringCriterion
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring_criteria', name, description, weight, 
                                   min_score, max_score, step, 0 as "order",
                                   category_id, NULL
                            FROM competitions_scoringcriterion_criteria
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} scoring criteria from scoring_criteria")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export criteria from competitions_scoringcriterion_criteria: {str(e)}"))
                    
                    # Get data from scoring ScoringCriterion
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring', name, description, weight, 
                                   min_score, max_score, step, 0 as "order",
                                   NULL, scoring_system_id
                            FROM competitions_scoringcriterion_scoring
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} scoring criteria from scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export criteria from competitions_scoringcriterion_scoring: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting scoring criteria: {str(e)}"))

    def export_category_configs(self, csv_dir, verbose):
        """Export category scoring configs to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'category_configs.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'source_table', 'category_id', 'scoring_system_id',
                    'override_min_score', 'override_max_score', 'override_score_step',
                    'exclude_extreme_scores', 'allow_ties', 'real_time_results'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from scoring CategoryScoringConfig
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring', category_id, scoring_system_id,
                                   override_min_score, override_max_score, override_score_step,
                                   NULL, NULL, NULL
                            FROM competitions_categoryscoringconfig
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} category configs from scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export configs from competitions_categoryscoringconfig: {str(e)}"))
                    
                    # Get data from ScoringConfiguration
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring_criteria', category_id, NULL,
                                   min_score, max_score, score_step,
                                   exclude_extreme_scores, allow_ties, real_time_results
                            FROM competitions_scoringconfiguration
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} category configs from scoring_criteria")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export configs from competitions_scoringconfiguration: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting category configs: {str(e)}"))

    def export_performances(self, csv_dir, verbose):
        """Export performances to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'performances.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'source_table', 'category_id', 'practitioner_id', 
                    'round_type', 'round_number', 'performance_order',
                    'status', 'start_time', 'end_time', 'notes',
                    'disqualification_reason'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from scoring Performance
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring', category_id, practitioner_id,
                                   round_type, round_number, performance_order,
                                   status, start_time, end_time, notes,
                                   disqualification_reason
                            FROM competitions_performance
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} performances from scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export performances from competitions_performance: {str(e)}"))
                    
                    # Get data from technical_scoring TechnicalPerformance
                    try:
                        cursor.execute("""
                            SELECT id, 'technical_scoring', category_id, practitioner_id,
                                   'preliminary', 1, performance_order,
                                   status, start_time, end_time, notes,
                                   ''
                            FROM competitions_technicalperformance
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} performances from technical_scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export performances from competitions_technicalperformance: {str(e)}"))
                    
                    # Get data from scoring_results TechnicalPerformanceResult
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring_results', category_id, practitioner_id,
                                   'preliminary', 1, performance_order,
                                   status, start_time, end_time, notes,
                                   ''
                            FROM competitions_technicalperformanceresult
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} performances from scoring_results")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export performances from competitions_technicalperformanceresult: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting performances: {str(e)}"))

    def export_scores(self, csv_dir, verbose):
        """Export scores to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'scores.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'source_table', 'performance_id', 'judge_id', 'criterion_id',
                    'value', 'original_value', 'is_locked', 'is_training_score',
                    'modified_by_id', 'notes'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from scoring Score
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring', performance_id, judge_id, criterion_id,
                                   value, original_value, 0, is_training_score,
                                   NULL, ''
                            FROM competitions_score
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} scores from scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export scores from competitions_score: {str(e)}"))
                    
                    # Get data from technical_scoring TechnicalScore
                    try:
                        cursor.execute("""
                            SELECT id, 'technical_scoring', performance_id, judge_id, criterion_id,
                                   value, value, is_locked, 0,
                                   NULL, ''
                            FROM competitions_technicalscore
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} scores from technical_scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export scores from competitions_technicalscore: {str(e)}"))
                    
                    # Get data from scoring_results TechnicalScoreResult
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring_results', performance_id, judge_id, criterion_id,
                                   value, value, is_locked, 0,
                                   NULL, ''
                            FROM competitions_technicalscoreresult
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} scores from scoring_results")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export scores from competitions_technicalscoreresult: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting scores: {str(e)}"))

    def export_judge_submissions(self, csv_dir, verbose):
        """Export judge submissions to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'judge_submissions.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'source_table', 'performance_id', 'judge_id',
                    'is_submitted', 'submitted_at', 'notes'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from scoring JudgeSubmission
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring', performance_id, judge_id,
                                   is_submitted, submitted_at, ''
                            FROM competitions_judgesubmission
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} judge submissions from scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export judge submissions from competitions_judgesubmission: {str(e)}"))
                    
                    # Get data from technical_scoring JudgeSubmissionStatus
                    try:
                        cursor.execute("""
                            SELECT id, 'technical_scoring', performance_id, judge_id,
                                   is_submitted, submitted_at, ''
                            FROM competitions_judgesubmissionstatus
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} judge submissions from technical_scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export judge submissions from competitions_judgesubmissionstatus: {str(e)}"))
                    
                    # Get data from scoring_results JudgeSubmissionStatusResult
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring_results', performance_id, judge_id,
                                   is_submitted, submitted_at, ''
                            FROM competitions_judgesubmissionstatusresult
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} judge submissions from scoring_results")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export judge submissions from competitions_judgesubmissionstatusresult: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting judge submissions: {str(e)}"))

    def export_rankings(self, csv_dir, verbose):
        """Export rankings to CSV."""
        try:
            # Connect to database directly to avoid model conflicts
            from django.db import connection
            
            filename = os.path.join(csv_dir, 'rankings.csv')
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([
                    'id', 'source_table', 'category_id', 'practitioner_id',
                    'performance_id', 'rank', 'final_score', 'is_tie',
                    'medal', 'is_published', 'notes'
                ])
                
                with connection.cursor() as cursor:
                    # Get data from scoring CompetitionRanking
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring', category_id, practitioner_id,
                                   NULL, rank, final_score, 0,
                                   medal, 0, ''
                            FROM competitions_competitionranking
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} rankings from scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export rankings from competitions_competitionranking: {str(e)}"))
                    
                    # Get data from technical_scoring CompetitionRanking
                    try:
                        cursor.execute("""
                            SELECT id, 'technical_scoring', category_id, practitioner_id,
                                   NULL, rank, score as final_score, 0,
                                   medal, 0, ''
                            FROM competitions_competitionranking_technical
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} rankings from technical_scoring")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export rankings from competitions_competitionranking_technical: {str(e)}"))
                    
                    # Get data from scoring_results RankingEntry
                    try:
                        cursor.execute("""
                            SELECT id, 'scoring_results', r.category_id, e.practitioner_id,
                                   e.performance_id, e.rank, e.score as final_score, e.is_tie,
                                   '', r.is_published, ''
                            FROM competitions_rankingentry e
                            JOIN competitions_categoryranking r ON e.ranking_id = r.id
                        """)
                        rows = cursor.fetchall()
                        
                        count = 0
                        for row in rows:
                            writer.writerow(row)
                            count += 1
                        
                        if verbose:
                            self.stdout.write(f"  Exported {count} rankings from scoring_results")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not export rankings from competitions_rankingentry: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error exporting rankings: {str(e)}"))

    def import_scoring_systems(self, csv_dir, verbose):
        """Import scoring systems from CSV."""
        from apps.competitions.models.unified_scoring import ScoringSystem
        
        filename = os.path.join(csv_dir, 'scoring_systems.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Scoring systems CSV file not found: {filename}"))
            return
        
        count = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Check if system already exists
                if ScoringSystem.objects.filter(name=row['name']).exists():
                    if verbose:
                        self.stdout.write(f"  Scoring system '{row['name']}' already exists, skipping.")
                    continue
                
                # Create new system
                ScoringSystem.objects.create(
                    name=row['name'] or f"System {row['id']}",
                    description=row['description'] or '',
                    system_type=row['system_type'],
                    min_score=Decimal(row['min_score']) if row['min_score'] else Decimal('0.0'),
                    max_score=Decimal(row['max_score']) if row['max_score'] else Decimal('10.0'),
                    score_step=Decimal(row['score_step']) if row['score_step'] else Decimal('0.1'),
                    exclude_extreme_scores=row['exclude_extreme_scores'] == 'True',
                    allow_ties=row['allow_ties'] == 'True',
                    real_time_results=True,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                count += 1
        
        # If no systems were created, create a default one
        if count == 0 and not ScoringSystem.objects.exists():
            ScoringSystem.objects.create(
                name="Default Standard Scoring",
                description="Default scoring system created during migration",
                system_type='standard',
                min_score=Decimal('0.0'),
                max_score=Decimal('10.0'),
                score_step=Decimal('0.1'),
                exclude_extreme_scores=True,
                allow_ties=True,
                real_time_results=True,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            count = 1
            
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} scoring systems"))

    def import_scoring_criteria(self, csv_dir, verbose):
        """Import scoring criteria from CSV."""
        from apps.competitions.models.unified_scoring import ScoringCriterion, ScoringSystem
        from apps.competitions.models.competitions import CompetitionCategory
        
        filename = os.path.join(csv_dir, 'scoring_criteria.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Scoring criteria CSV file not found: {filename}"))
            return
        
        count = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Get category if specified
                category = None
                if row['category_id'] and row['category_id'] != 'None':
                    try:
                        category = CompetitionCategory.objects.get(pk=row['category_id'])
                    except CompetitionCategory.DoesNotExist:
                        if verbose:
                            self.stdout.write(f"  Category {row['category_id']} not found, skipping criterion.")
                        continue
                
                # Get scoring system
                scoring_system = None
                if row['scoring_system_id'] and row['scoring_system_id'] != 'None':
                    try:
                        scoring_system = ScoringSystem.objects.get(pk=row['scoring_system_id'])
                    except ScoringSystem.DoesNotExist:
                        pass
                
                if not scoring_system:
                    scoring_system = ScoringSystem.objects.first()
                    if not scoring_system:
                        if verbose:
                            self.stdout.write(f"  No scoring system found, skipping criterion.")
                        continue
                
                # Check if criterion already exists
                if category and ScoringCriterion.objects.filter(
                    category=category,
                    name=row['name']
                ).exists():
                    if verbose:
                        self.stdout.write(f"  Criterion '{row['name']}' already exists for category, skipping.")
                    continue
                
                # Create new criterion
                ScoringCriterion.objects.create(
                    scoring_system=scoring_system,
                    category=category,
                    name=row['name'],
                    description=row['description'] or '',
                    weight=Decimal(row['weight']) if row['weight'] else Decimal('1.0'),
                    min_score=Decimal(row['min_score']) if row['min_score'] and row['min_score'] != 'None' else None,
                    max_score=Decimal(row['max_score']) if row['max_score'] and row['max_score'] != 'None' else None,
                    step=Decimal(row['step']) if row['step'] and row['step'] != 'None' else None,
                    order=int(row['order']) if row['order'] else 0,
                    is_active=True,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                count += 1
        
        # If no criteria were created, create default ones
        if count == 0:
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
                        is_active=True,
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    count += 1
            
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} scoring criteria"))

    def import_category_configs(self, csv_dir, verbose):
        """Import category scoring configs from CSV."""
        from apps.competitions.models.unified_scoring import CategoryScoringConfig, ScoringSystem
        from apps.competitions.models.competitions import CompetitionCategory
        
        filename = os.path.join(csv_dir, 'category_configs.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Category configs CSV file not found: {filename}"))
            return
        
        count = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Get category
                try:
                    category = CompetitionCategory.objects.get(pk=row['category_id'])
                except CompetitionCategory.DoesNotExist:
                    if verbose:
                        self.stdout.write(f"  Category {row['category_id']} not found, skipping config.")
                    continue
                
                # Check if config already exists
                if CategoryScoringConfig.objects.filter(category=category).exists():
                    if verbose:
                        self.stdout.write(f"  Config for category {category} already exists, skipping.")
                    continue
                
                # Get scoring system
                scoring_system = None
                if row['scoring_system_id'] and row['scoring_system_id'] != 'None':
                    try:
                        scoring_system = ScoringSystem.objects.get(pk=row['scoring_system_id'])
                    except ScoringSystem.DoesNotExist:
                        pass
                
                if not scoring_system:
                    scoring_system = ScoringSystem.objects.first()
                    if not scoring_system:
                        if verbose:
                            self.stdout.write(f"  No scoring system found, skipping config.")
                        continue
                
                # Create new config
                CategoryScoringConfig.objects.create(
                    category=category,
                    scoring_system=scoring_system,
                    override_min_score=Decimal(row['override_min_score']) if row['override_min_score'] and row['override_min_score'] != 'None' else None,
                    override_max_score=Decimal(row['override_max_score']) if row['override_max_score'] and row['override_max_score'] != 'None' else None,
                    override_score_step=Decimal(row['override_score_step']) if row['override_score_step'] and row['override_score_step'] != 'None' else None,
                    exclude_extreme_scores=row['exclude_extreme_scores'] == 'True' if row['exclude_extreme_scores'] and row['exclude_extreme_scores'] != 'None' else None,
                    allow_ties=row['allow_ties'] == 'True' if row['allow_ties'] and row['allow_ties'] != 'None' else None,
                    real_time_results=row['real_time_results'] == 'True' if row['real_time_results'] and row['real_time_results'] != 'None' else None,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                count += 1
        
        # Create default configs for categories without them
        if count == 0:
            scoring_system = ScoringSystem.objects.first()
            if scoring_system:
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
                    count += 1
            
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} category scoring configs"))

    def import_performances(self, csv_dir, verbose):
        """Import performances from CSV."""
        from apps.competitions.models.unified_scoring import Performance
        from apps.competitions.models.competitions import CompetitionCategory
        from apps.competitions.models.practitioners import Practitioner
        
        filename = os.path.join(csv_dir, 'performances.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Performances CSV file not found: {filename}"))
            return
        
        performance_map = {}  # Map old IDs to new performances
        count = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Get category and practitioner
                try:
                    category = CompetitionCategory.objects.get(pk=row['category_id'])
                    practitioner = Practitioner.objects.get(pk=row['practitioner_id'])
                except (CompetitionCategory.DoesNotExist, Practitioner.DoesNotExist):
                    if verbose:
                        self.stdout.write(f"  Category or practitioner not found, skipping performance.")
                    continue
                
                # Check if performance already exists
                existing = Performance.objects.filter(
                    category=category,
                    practitioner=practitioner,
                    round_type=row['round_type'] or Performance.PRELIMINARY,
                    round_number=int(row['round_number']) if row['round_number'] else 1
                ).first()
                
                if existing:
                    if verbose:
                        self.stdout.write(f"  Performance for {practitioner} in {category} already exists, mapping old ID.")
                    performance_map[f"{row['source_table']}_{row['id']}"] = existing
                    continue
                
                # Map status
                status_map = {
                    'pending': Performance.PENDING,
                    'in_progress': Performance.IN_PROGRESS,
                    'completed': Performance.COMPLETED,
                    'disqualified': Performance.DISQUALIFIED,
                    'cancelled': Performance.CANCELLED,
                }
                status = status_map.get(row['status'], Performance.PENDING)
                
                # Create new performance
                performance = Performance.objects.create(
                    competition=category.competition,
                    category=category,
                    practitioner=practitioner,
                    round_type=row['round_type'] or Performance.PRELIMINARY,
                    round_number=int(row['round_number']) if row['round_number'] else 1,
                    performance_order=int(row['performance_order']) if row['performance_order'] else 0,
                    status=status,
                    start_time=row['start_time'] if row['start_time'] and row['start_time'] != 'None' else None,
                    end_time=row['end_time'] if row['end_time'] and row['end_time'] != 'None' else None,
                    notes=row['notes'] or '',
                    disqualification_reason=row['disqualification_reason'] or '',
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
                
                # Store mapping from old ID to new performance
                performance_map[f"{row['source_table']}_{row['id']}"] = performance
                count += 1
        
        # Save mapping to file for other imports to use
        with open(os.path.join(csv_dir, 'performance_map.csv'), 'w', newline='') as mapfile:
            writer = csv.writer(mapfile)
            writer.writerow(['old_key', 'new_id'])
            for key, perf in performance_map.items():
                writer.writerow([key, perf.id])
            
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} performances"))
        return performance_map

    def import_scores(self, csv_dir, verbose):
        """Import scores from CSV."""
        from apps.competitions.models.unified_scoring import Score, Performance, ScoringCriterion
        
        filename = os.path.join(csv_dir, 'scores.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Scores CSV file not found: {filename}"))
            return
        
        # Load performance mapping
        performance_map = {}
        map_filename = os.path.join(csv_dir, 'performance_map.csv')
        if os.path.exists(map_filename):
            with open(map_filename, 'r', newline='') as mapfile:
                reader = csv.DictReader(mapfile)
                for row in reader:
                    performance_map[row['old_key']] = row['new_id']
        
        count = 0
        errors = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Get performance
                    performance_key = f"{row['source_table']}_{row['performance_id']}"
                    if performance_key in performance_map:
                        try:
                            performance = Performance.objects.get(pk=performance_map[performance_key])
                        except Performance.DoesNotExist:
                            if verbose:
                                self.stdout.write(f"  Performance mapped to ID {performance_map[performance_key]} not found, skipping score.")
                            errors += 1
                            continue
                    else:
                        if verbose:
                            self.stdout.write(f"  No mapping found for performance {performance_key}, skipping score.")
                        errors += 1
                        continue
                    
                    # Get judge
                    try:
                        judge = User.objects.get(pk=row['judge_id'])
                    except User.DoesNotExist:
                        if verbose:
                            self.stdout.write(f"  Judge {row['judge_id']} not found, skipping score.")
                        errors += 1
                        continue
                    
                    # Get criterion
                    try:
                        criterion = ScoringCriterion.objects.get(pk=row['criterion_id'])
                    except ScoringCriterion.DoesNotExist:
                        # Try to find a criterion with the same name
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("""
                                SELECT name FROM competitions_scoringcriterion WHERE id = %s
                                UNION
                                SELECT name FROM competitions_scoringcriterion_criteria WHERE id = %s
                                UNION
                                SELECT name FROM competitions_scoringcriterion_scoring WHERE id = %s
                            """, [row['criterion_id'], row['criterion_id'], row['criterion_id']])
                            name_result = cursor.fetchone()
                        
                        if name_result:
                            criterion_name = name_result[0]
                            # Look for a criterion with this name for this category
                            criterion = ScoringCriterion.objects.filter(
                                category=performance.category,
                                name=criterion_name
                            ).first()
                            
                            if not criterion:
                                # Look for a global criterion with this name
                                criterion = ScoringCriterion.objects.filter(
                                    category__isnull=True,
                                    name=criterion_name
                                ).first()
                        
                        if not criterion:
                            if verbose:
                                self.stdout.write(f"  Criterion {row['criterion_id']} not found and couldn't find by name, skipping score.")
                            errors += 1
                            continue
                    
                    # Check if score already exists
                    if Score.objects.filter(
                        performance=performance,
                        judge=judge,
                        criterion=criterion
                    ).exists():
                        if verbose:
                            self.stdout.write(f"  Score already exists for this judge and criterion, skipping.")
                        continue
                    
                    # Create score
                    Score.objects.create(
                        performance=performance,
                        judge=judge,
                        criterion=criterion,
                        value=Decimal(row['value']),
                        original_value=Decimal(row['original_value']) if row['original_value'] and row['original_value'] != 'None' else Decimal(row['value']),
                        is_locked=row['is_locked'] == 'True' or row['is_locked'] == '1',
                        is_training_score=row['is_training_score'] == 'True' or row['is_training_score'] == '1',
                        modified_by=User.objects.get(pk=row['modified_by_id']) if row['modified_by_id'] and row['modified_by_id'] != 'None' else None,
                        notes=row['notes'] or '',
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    count += 1
                    
                except Exception as e:
                    if verbose:
                        self.stdout.write(f"  Error importing score: {str(e)}")
                    errors += 1
        
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} scores with {errors} errors"))

    def import_judge_submissions(self, csv_dir, verbose):
        """Import judge submissions from CSV."""
        from apps.competitions.models.unified_scoring import JudgeSubmission, Performance
        
        filename = os.path.join(csv_dir, 'judge_submissions.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Judge submissions CSV file not found: {filename}"))
            return
        
        # Load performance mapping
        performance_map = {}
        map_filename = os.path.join(csv_dir, 'performance_map.csv')
        if os.path.exists(map_filename):
            with open(map_filename, 'r', newline='') as mapfile:
                reader = csv.DictReader(mapfile)
                for row in reader:
                    performance_map[row['old_key']] = row['new_id']
        
        count = 0
        errors = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Get performance
                    performance_key = f"{row['source_table']}_{row['performance_id']}"
                    if performance_key in performance_map:
                        try:
                            performance = Performance.objects.get(pk=performance_map[performance_key])
                        except Performance.DoesNotExist:
                            if verbose:
                                self.stdout.write(f"  Performance mapped to ID {performance_map[performance_key]} not found, skipping submission.")
                            errors += 1
                            continue
                    else:
                        if verbose:
                            self.stdout.write(f"  No mapping found for performance {performance_key}, skipping submission.")
                        errors += 1
                        continue
                    
                    # Get judge
                    try:
                        judge = User.objects.get(pk=row['judge_id'])
                    except User.DoesNotExist:
                        if verbose:
                            self.stdout.write(f"  Judge {row['judge_id']} not found, skipping submission.")
                        errors += 1
                        continue
                    
                    # Check if submission already exists
                    if JudgeSubmission.objects.filter(
                        performance=performance,
                        judge=judge
                    ).exists():
                        if verbose:
                            self.stdout.write(f"  Submission already exists for this judge, skipping.")
                        continue
                    
                    # Create submission
                    JudgeSubmission.objects.create(
                        performance=performance,
                        judge=judge,
                        is_submitted=row['is_submitted'] == 'True' or row['is_submitted'] == '1',
                        submitted_at=row['submitted_at'] if row['submitted_at'] and row['submitted_at'] != 'None' else None,
                        notes=row['notes'] or '',
                    )
                    count += 1
                    
                except Exception as e:
                    if verbose:
                        self.stdout.write(f"  Error importing judge submission: {str(e)}")
                    errors += 1
        
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} judge submissions with {errors} errors"))

    def import_rankings(self, csv_dir, verbose):
        """Import rankings from CSV."""
        from apps.competitions.models.unified_scoring import CompetitionRanking, Performance
        from apps.competitions.models.competitions import CompetitionCategory
        from apps.competitions.models.practitioners import Practitioner
        
        filename = os.path.join(csv_dir, 'rankings.csv')
        if not os.path.exists(filename):
            self.stdout.write(self.style.WARNING(f"  Rankings CSV file not found: {filename}"))
            return
        
        # Load performance mapping
        performance_map = {}
        map_filename = os.path.join(csv_dir, 'performance_map.csv')
        if os.path.exists(map_filename):
            with open(map_filename, 'r', newline='') as mapfile:
                reader = csv.DictReader(mapfile)
                for row in reader:
                    performance_map[row['old_key']] = row['new_id']
        
        count = 0
        errors = 0
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Get category
                    try:
                        category = CompetitionCategory.objects.get(pk=row['category_id'])
                    except CompetitionCategory.DoesNotExist:
                        if verbose:
                            self.stdout.write(f"  Category {row['category_id']} not found, skipping ranking.")
                        errors += 1
                        continue
                    
                    # Get practitioner
                    try:
                        practitioner = Practitioner.objects.get(pk=row['practitioner_id'])
                    except Practitioner.DoesNotExist:
                        if verbose:
                            self.stdout.write(f"  Practitioner {row['practitioner_id']} not found, skipping ranking.")
                        errors += 1
                        continue
                    
                    # Check if ranking already exists
                    if CompetitionRanking.objects.filter(
                        category=category,
                        practitioner=practitioner
                    ).exists():
                        if verbose:
                            self.stdout.write(f"  Ranking already exists for this practitioner, skipping.")
                        continue
                    
                    # Get performance if specified
                    performance = None
                    if row['performance_id'] and row['performance_id'] != 'None':
                        performance_key = f"{row['source_table']}_{row['performance_id']}"
                        if performance_key in performance_map:
                            try:
                                performance = Performance.objects.get(pk=performance_map[performance_key])
                            except Performance.DoesNotExist:
                                pass
                    
                    # Create ranking
                    CompetitionRanking.objects.create(
                        competition=category.competition,
                        category=category,
                        practitioner=practitioner,
                        performance=performance,
                        rank=int(row['rank']) if row['rank'] else 0,
                        final_score=Decimal(row['final_score']) if row['final_score'] else Decimal('0.0'),
                        is_tie=row['is_tie'] == 'True' or row['is_tie'] == '1',
                        medal=row['medal'] if row['medal'] and row['medal'] != 'None' else CompetitionRanking.NONE,
                        is_published=row['is_published'] == 'True' or row['is_published'] == '1',
                        notes=row['notes'] or '',
                        created_at=timezone.now(),
                        updated_at=timezone.now(),
                    )
                    count += 1
                    
                except Exception as e:
                    if verbose:
                        self.stdout.write(f"  Error importing ranking: {str(e)}")
                    errors += 1
        
        self.stdout.write(self.style.SUCCESS(f"  Imported {count} rankings with {errors} errors"))
