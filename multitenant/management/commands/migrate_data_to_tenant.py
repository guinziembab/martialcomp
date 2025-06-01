"""
Management command to migrate existing data to a specific tenant
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.apps import apps
from django.db.models import Q
import json

from ...models import Tenant
from ...utils import SchemaContext


class Command(BaseCommand):
    help = 'Migrate existing data from public schema to a specific tenant schema'

    def add_arguments(self, parser):
        parser.add_argument(
            'tenant_id',
            type=str,
            help='Tenant ID or slug to migrate data to'
        )
        parser.add_argument(
            '--models',
            nargs='+',
            type=str,
            help='Specific models to migrate (app_label.ModelName)'
        )
        parser.add_argument(
            '--filter',
            type=str,
            help='JSON filter to apply when selecting data to migrate'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it'
        )
        parser.add_argument(
            '--delete-source',
            action='store_true',
            help='Delete source data after successful migration'
        )

    def handle(self, *args, **options):
        tenant_identifier = options['tenant_id']
        specific_models = options.get('models', [])
        filter_json = options.get('filter')
        dry_run = options.get('dry_run', False)
        delete_source = options.get('delete_source', False)

        # Find the tenant
        try:
            tenant = Tenant.objects.get(
                Q(id=tenant_identifier) | Q(slug=tenant_identifier)
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant not found: {tenant_identifier}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No data will be migrated')
            )

        self.stdout.write(f'Migrating data to tenant: {tenant.name}')
        self.stdout.write(f'Target schema: {tenant.schema_name}')

        # Parse filter if provided
        data_filter = {}
        if filter_json:
            try:
                data_filter = json.loads(filter_json)
            except json.JSONDecodeError as e:
                raise CommandError(f'Invalid JSON filter: {e}')

        # Models that should NOT be migrated (remain in public schema)
        excluded_models = [
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

        # Get models to migrate
        models_to_migrate = []
        
        if specific_models:
            # Validate specified models
            for model_path in specific_models:
                try:
                    app_label, model_name = model_path.split('.')
                    model = apps.get_model(app_label, model_name)
                    if model_path not in excluded_models:
                        models_to_migrate.append(model)
                except (ValueError, LookupError):
                    raise CommandError(f'Invalid model: {model_path}')
        else:
            # Get all models except excluded ones
            for app_config in apps.get_app_configs():
                for model in app_config.get_models():
                    model_path = f'{app_config.label}.{model.__name__}'
                    if model_path not in excluded_models:
                        models_to_migrate.append(model)

        # Start migration
        total_objects = 0
        migrated_objects = 0
        failed_models = []

        for model in models_to_migrate:
            model_name = f'{model._meta.app_label}.{model.__name__}'
            self.stdout.write(f'\nMigrating {model_name}...')

            try:
                # Apply filter if applicable
                queryset = model.objects.all()
                if data_filter and model_name in data_filter:
                    queryset = queryset.filter(**data_filter[model_name])

                object_count = queryset.count()
                total_objects += object_count

                if dry_run:
                    self.stdout.write(
                        f'  Would migrate {object_count} objects'
                    )
                    continue

                # Perform actual migration
                with transaction.atomic():
                    # Switch to tenant schema
                    with SchemaContext(tenant.schema_name):
                        migrated_count = 0
                        
                        # Migrate in batches to avoid memory issues
                        batch_size = 1000
                        for offset in range(0, object_count, batch_size):
                            batch = list(queryset[offset:offset + batch_size])
                            
                            # Clear primary keys to create new objects
                            for obj in batch:
                                obj.pk = None
                                
                                # Handle foreign keys to auth.User
                                if hasattr(obj, 'user_id'):
                                    # Ensure user exists in tenant schema
                                    # This is a simplification - you may need more complex logic
                                    pass
                            
                            # Bulk create in tenant schema
                            model.objects.bulk_create(batch)
                            migrated_count += len(batch)
                            
                            self.stdout.write(
                                f'  Migrated {migrated_count}/{object_count} objects'
                            )

                    # Delete source data if requested
                    if delete_source and not dry_run:
                        with SchemaContext('public'):
                            delete_count = queryset.delete()[0]
                            self.stdout.write(
                                self.style.WARNING(
                                    f'  Deleted {delete_count} source objects'
                                )
                            )

                    migrated_objects += migrated_count

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  Error: {str(e)}')
                )
                failed_models.append(model_name)
                continue

        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write('Migration Summary:')
        self.stdout.write(f'Total objects found: {total_objects}')
        self.stdout.write(f'Objects migrated: {migrated_objects}')
        
        if failed_models:
            self.stdout.write(
                self.style.ERROR(f'Failed models: {", ".join(failed_models)}')
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no data was actually migrated')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Migration completed successfully!')
            )

        # Next steps
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Test the tenant to ensure data was migrated correctly')
        self.stdout.write('2. Update any external references to use tenant-specific URLs')
        self.stdout.write('3. Configure web server for subdomain routing')
        
        if not delete_source:
            self.stdout.write(
                '4. Once verified, consider running with --delete-source to clean up'
            )