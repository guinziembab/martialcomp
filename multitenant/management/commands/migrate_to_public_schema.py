"""
Management command to migrate existing data to the public schema
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.apps import apps
from django.db.models import Model

# Models that should remain in public schema
PUBLIC_SCHEMA_MODELS = [
    'multitenant.Tenant',
    'multitenant.Domain',
    'multitenant.TenantFeature',
    # Add other models that should be shared across tenants
    'auth.User',  # If using a shared user model
    'auth.Group',
    'auth.Permission',
    'contenttypes.ContentType',
    'sessions.Session',
    'admin.LogEntry',
]


class Command(BaseCommand):
    help = 'Migrate existing data to the public schema in preparation for multi-tenant setup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='Skip creating a backup before migration'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        no_backup = options.get('no_backup', False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN: No changes will be made')
            )

        # Create backup if not skipped
        if not no_backup and not dry_run:
            self.stdout.write('Creating backup...')
            try:
                from django.core.management import call_command
                call_command('dumpdata', output='backup_before_multitenant.json')
                self.stdout.write(
                    self.style.SUCCESS('Backup created: backup_before_multitenant.json')
                )
            except Exception as e:
                raise CommandError(f'Error creating backup: {str(e)}')

        # Ensure we're in the public schema
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public")

        # List all models that will be checked
        self.stdout.write('\nChecking models:')
        
        models_to_check = []
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                model_label = f'{app_config.label}.{model.__name__}'
                
                if model_label in PUBLIC_SCHEMA_MODELS:
                    self.stdout.write(
                        f'  {model_label}: Will remain in public schema'
                    )
                else:
                    models_to_check.append((model_label, model))
                    if dry_run:
                        self.stdout.write(
                            f'  {model_label}: Would be prepared for tenant isolation'
                        )
                    else:
                        self.stdout.write(
                            f'  {model_label}: Will be prepared for tenant isolation'
                        )

        if not dry_run:
            # Ensure all tables exist in public schema
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                self.stdout.write(
                    f'\nFound {len(existing_tables)} existing tables in public schema'
                )

            # Run migrations to ensure schema is up to date
            self.stdout.write('\nEnsuring all migrations are applied...')
            try:
                from django.core.management import call_command
                call_command('migrate')
                self.stdout.write(
                    self.style.SUCCESS('All migrations applied successfully')
                )
            except Exception as e:
                raise CommandError(f'Error applying migrations: {str(e)}')

        self.stdout.write(
            self.style.SUCCESS(
                '\nData is ready for multi-tenant migration'
            )
        )
        
        # Next steps information
        self.stdout.write('\nNext steps:')
        self.stdout.write('1. Create your first tenant: python manage.py create_tenant')
        self.stdout.write('2. Run tenant-specific migrations: python manage.py migrate_tenants')
        self.stdout.write('3. Configure your web server to handle subdomains')
        self.stdout.write('4. Test tenant isolation thoroughly')