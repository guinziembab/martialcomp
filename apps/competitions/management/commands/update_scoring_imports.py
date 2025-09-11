import os
import re
from pathlib import Path
from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Updates import statements in Python files to use the scoring compatibility layer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry run mode without making any actual changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Provide detailed output during processing'
        )
        parser.add_argument(
            '--directory',
            type=str,
            default='competitions/views',
            help='Directory to process (relative to project root)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        directory = options['directory']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode. No changes will be made.'))
        
        # Get the project root directory
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        target_dir = project_root / directory
        
        if not target_dir.exists():
            self.stdout.write(self.style.ERROR(f'Directory {target_dir} does not exist.'))
            return
        
        self.stdout.write(f'Processing files in {target_dir}...')
        
        # Count statistics
        files_processed = 0
        files_modified = 0
        
        # Process all Python files recursively
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if not file.endswith('.py'):
                    continue
                
                file_path = os.path.join(root, file)
                was_modified = self.process_file(file_path, dry_run, verbose)
                
                files_processed += 1
                if was_modified:
                    files_modified += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Processed {files_processed} files, modified {files_modified} files.'
        ))
    
    def process_file(self, file_path, dry_run, verbose):
        """Process a single Python file, updating import statements."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for imports from the old scoring models
        import_patterns = [
            r'from apps.competitions.models.scoring import (.+)',
            r'from apps.competitions.models.technical_scoring import (.+)',
            r'from apps.competitions.models.scoring_criteria import (.+)',
            r'from apps.competitions.models.scoring_results import (.+)',
        ]
        
        # Fix any incorrect user imports
        user_patterns = [
            r'from apps.competitions.models.user import (.+)',
        ]
        
        was_modified = False
        
        for pattern in import_patterns:
            # Match the pattern
            matches = re.findall(pattern, content)
            
            if matches:
                for match in matches:
                    original_import = f'from competitions.models.{"scoring" if "scoring import" in pattern else "technical_scoring" if "technical_scoring import" in pattern else "scoring_criteria" if "scoring_criteria import" in pattern else "scoring_results"} import {match}'
                    new_import = f'from apps.competitions.models.scoring_compatibility import {match}'
                    
                    if original_import in content:
                        if verbose:
                            self.stdout.write(f'  Replacing in {os.path.basename(file_path)}: {original_import} -> {new_import}')
                        
                        # Replace the import
                        content = content.replace(original_import, new_import)
                        was_modified = True
        
        # Fix incorrect user imports
        for pattern in user_patterns:
            # Match the pattern
            matches = re.findall(pattern, content)
            
            if matches:
                for match in matches:
                    original_import = f'from apps.competitions.models.user import {match}'
                    new_import = f'from apps.competitions.models.users import {match}'
                    
                    if original_import in content:
                        if verbose:
                            self.stdout.write(f'  Fixing user import in {os.path.basename(file_path)}: {original_import} -> {new_import}')
                        
                        # Replace the import
                        content = content.replace(original_import, new_import)
                        was_modified = True
        
        # Special case: Check for direct model accesses
        # This is more complex and might require manual review
        model_names = [
            'ScoringSystem', 'ScoringCriterion', 'ScoringConfiguration',
            'CategoryScoringConfig', 'Performance', 'Score',
            'TechnicalPerformance', 'TechnicalScore',
            'JudgeSubmission', 'JudgeSubmissionStatus',
            'CompetitionRanking',
        ]
        
        # Check for model usages without compatible imports
        for model_name in model_names:
            if re.search(rf'\b{model_name}\b', content) and f'import {model_name}' not in content:
                # This might be accessing the model directly from models
                if verbose:
                    self.stdout.write(self.style.WARNING(
                        f'  {os.path.basename(file_path)} might be using {model_name} without explicit import, '
                        f'manual review recommended.'
                    ))
        
        # Write the modified content back to the file
        if was_modified and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return was_modified
