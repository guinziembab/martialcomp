"""
Management command to clone data from one tenant to another
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.apps import apps
from django.db.models import Q

from ...models import Tenant
from ...utils import SchemaContext


class Command(BaseCommand):
    help = 'Clone data from one tenant to another'

    def add_arguments(self, parser):
        parser.add_argument(
            'source_tenant',
            type=str,
            help='Source tenant ID or slug'
        )
        parser.add_argument(
            'target_tenant',
            type=str,
            help='Target tenant ID or slug'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='Specific models to clone (app_label.ModelName)'
        )
        parser.add_argument(
            '--exclude-models',
            nargs='+',
            type=str,
            help='Models to exclude from cloning'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cloned without actually doing it'
        )
        parser.add_argument(
            '--clear-target',
            action='store_true',
            help='Clear existing data in target tenant before cloning'
        )

    def handle(self, *args, **options):
        source_identifier = options['source_tenant']
        target_identifier = options['target_tenant']
        specific_models = options.get('models', [])
        excluded_models = options.get('exclude_models', [])
        dry_run = options.get('dry_run', False)
        clear_target = options.get('clear_target', False)

        # Find tenants
        try:
            source_tenant = Tenant.objects.get(
                Q(id=source_identifier) | Q(slug=source_identifier)
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Source tenant not found: {source_identifier}')

        try:
            target_tenant = Tenant.objects.get(
                Q(id=target_identifier) | Q(slug=target_identifier)
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Target tenant not found: {target_identifier}')

        if source_tenant.id == target_tenant.id:
            raise CommandError('Source and target tenants cannot be the same')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No data will be cloned')
            )

        self.stdout.write(f'Cloning data from: {source_tenant.name}')
        self.stdout.write(f'Cloning data to: {target_tenant.name}')
        self.stdout.write(f'Source schema: {source_tenant.schema_name}')
        self.stdout.write(f'Target schema: {target_tenant.schema_name}')

        # Models that should NOT be cloned
        default_excluded = [
            'auth.User',
            'auth.Group',
            'auth.Permission',
            'contenttypes.ContentType',
            'sessions.Session',
            'admin.LogEntry',
            'multitenant.Tenant',
            'multitenant.Domain',
            'multitenant.TenantFeature',
        ]
        
        # Add user-specified exclusions
        all_excluded = set(default_excluded + excluded_models)

        # Get models to clone
        models_to_clone = []
        
        if specific_models:
            # Validate specified models
            for model_path in specific_models:
                if model_path in all_excluded:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping excluded model: {model_path}')
                    )
                    continue
                
                try:
                    app_label, model_name = model_path.split('.')
                    model = apps.get_model(app_label, model_name)
                    models_to_clone.append(model)
                except (ValueError, LookupError):
                    raise CommandError(f'Invalid model: {model_path}')
        else:
            # Get all models except excluded ones
            for app_config in apps.get_app_configs():
                for model in app_config.get_models():
                    model_path = f'{app_config.label}.{model.__name__}'
                    if model_path not in all_excluded:
                        models_to_clone.append(model)

        # Start cloning
        total_objects = 0
        cloned_objects = 0
        failed_models = []

        with transaction.atomic():
            for model in models_to_clone:
                model_name = f'{model._meta.app_label}.{model.__name__}'
                self.stdout.write(f'\nCloning {model_name}...')

                try:
                    # Count objects in source
                    with SchemaContext(source_tenant.schema_name):
                        source_count = model.objects.count()
                        
                    total_objects += source_count

                    if dry_run:
                        self.stdout.write(
                            f'  Would clone {source_count} objects'
                        )
                        
                        # Check target
                        with SchemaContext(target_tenant.schema_name):
                            target_count = model.objects.count()
                            if target_count > 0 and clear_target:
                                self.stdout.write(
                                    f'  Would clear {target_count} existing objects'
                                )
                        continue

                    # Clear target if requested
                    if clear_target:
                        with SchemaContext(target_tenant.schema_name):
                            deleted_count = model.objects.all().delete()[0]
                            if deleted_count > 0:
                                self.stdout.write(
                                    f'  Cleared {deleted_count} existing objects'
                                )

                    # Clone data
                    cloned_count = 0
                    batch_size = 1000
                    
                    with SchemaContext(source_tenant.schema_name):
                        queryset = model.objects.all()
                        
                        for offset in range(0, source_count, batch_size):
                            batch = list(queryset[offset:offset + batch_size])
                            
                            # Clear primary keys
                            original_pks = []
                            for obj in batch:
                                original_pks.append(obj.pk)
                                obj.pk = None
                            
                            # Clone to target
                            with SchemaContext(target_tenant.schema_name):
                                model.objects.bulk_create(batch)
                                cloned_count += len(batch)
                            
                            # Restore PKs for reference
                            for obj, pk in zip(batch, original_pks):
                                obj.pk = pk
                            
                            self.stdout.write(
                                f'  Cloned {cloned_count}/{source_count} objects'
                            )

                    cloned_objects += cloned_count

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  Error: {str(e)}')
                    )
                    failed_models.append(model_name)
                    
                    # Rollback for this model
                    if not dry_run:
                        transaction.set_rollback(True)
                    continue

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('Clone Summary:')
        self.stdout.write(f'Total objects in source: {total_objects}')
        self.stdout.write(f'Objects cloned: {cloned_objects}')
        
        if failed_models:
            self.stdout.write(
                self.style.ERROR(f'Failed models: {", ".join(failed_models)}')
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no data was actually cloned')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Cloning completed successfully!')
            )

        # Recommendations
        self.stdout.write('\nRecommendations:')
        self.stdout.write('1. Test the target tenant to ensure data was cloned correctly')
        self.stdout.write('2. Review any tenant-specific configurations that may need adjustment')
        self.stdout.write('3. Update any external integrations for the new tenant')
        self.stdout.write('4. Consider running tenant isolation tests')