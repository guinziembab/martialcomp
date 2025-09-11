import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Import directly from models to avoid conflicts
from apps.competitions.models.standalone_scoring import (
    StandaloneScoringSystem, StandaloneScoringCriterion
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initializes the standalone scoring system with default data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Provide detailed output during initialization'
        )

    def handle(self, *args, **options):
        verbose = options['verbose']
        
        try:
            with transaction.atomic():
                self.create_default_scoring_systems(verbose)
                self.create_default_criteria(verbose)
                
                self.stdout.write(self.style.SUCCESS('Standalone scoring system initialized successfully.'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during initialization: {str(e)}'))
            logger.exception('Initialization failed')
            return
    
    def create_default_scoring_systems(self, verbose):
        """Create default scoring systems."""
        # Check if any scoring systems exist
        if StandaloneScoringSystem.objects.exists():
            if verbose:
                self.stdout.write('Scoring systems already exist, skipping.')
            return
        
        # Create default systems
        systems = [
            {
                'name': 'Standard Technical Scoring',
                'description': 'Standard weighted average scoring system for technical competitions',
                'system_type': StandaloneScoringSystem.STANDARD,
                'min_score': 0.0,
                'max_score': 10.0,
                'score_step': 0.1,
                'exclude_extreme_scores': True,
                'allow_ties': True,
                'real_time_results': True,
            },
            {
                'name': 'Point-Based Scoring',
                'description': 'Simple point-based scoring system',
                'system_type': StandaloneScoringSystem.POINT,
                'min_score': 0.0,
                'max_score': 10.0,
                'score_step': 0.5,
                'exclude_extreme_scores': False,
                'allow_ties': False,
                'real_time_results': True,
            },
            {
                'name': 'Direct Elimination',
                'description': 'Direct elimination scoring system',
                'system_type': StandaloneScoringSystem.DIRECT_ELIMINATION,
                'min_score': 0.0,
                'max_score': 1.0,
                'score_step': 1.0,
                'exclude_extreme_scores': False,
                'allow_ties': False,
                'real_time_results': False,
            },
        ]
        
        count = 0
        for system_data in systems:
            StandaloneScoringSystem.objects.create(
                **system_data,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            count += 1
            
            if verbose:
                self.stdout.write(f'  Created scoring system: {system_data["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} default scoring systems'))
    
    def create_default_criteria(self, verbose):
        """Create default scoring criteria."""
        # Get the standard scoring system
        standard_system = StandaloneScoringSystem.objects.filter(
            system_type=StandaloneScoringSystem.STANDARD
        ).first()
        
        if not standard_system:
            self.stdout.write(self.style.WARNING('Standard scoring system not found, skipping criteria creation.'))
            return
        
        # Check if criteria already exist for this system
        if StandaloneScoringCriterion.objects.filter(scoring_system=standard_system).exists():
            if verbose:
                self.stdout.write('Criteria already exist for the standard system, skipping.')
            return
        
        # Create default criteria
        criteria = [
            {
                'name': 'Technique',
                'description': 'Technical execution and correctness',
                'weight': 1.0,
                'order': 1,
            },
            {
                'name': 'Power',
                'description': 'Strength and force of techniques',
                'weight': 0.8,
                'order': 2,
            },
            {
                'name': 'Balance',
                'description': 'Stability and body control',
                'weight': 0.7,
                'order': 3,
            },
            {
                'name': 'Overall Impression',
                'description': 'General assessment of the performance',
                'weight': 1.2,
                'order': 4,
            },
            {
                'name': 'Fluidity',
                'description': 'Smooth transitions between techniques',
                'weight': 0.9,
                'order': 5,
            },
            {
                'name': 'Spirit',
                'description': 'Energy, focus, and presence',
                'weight': 0.7,
                'order': 6,
            },
        ]
        
        count = 0
        for criterion_data in criteria:
            StandaloneScoringCriterion.objects.create(
                scoring_system=standard_system,
                category_id=None,  # Global criteria
                min_score=standard_system.min_score,
                max_score=standard_system.max_score,
                step=standard_system.score_step,
                is_active=True,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                **criterion_data,
            )
            count += 1
            
            if verbose:
                self.stdout.write(f'  Created criterion: {criterion_data["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {count} default scoring criteria'))
