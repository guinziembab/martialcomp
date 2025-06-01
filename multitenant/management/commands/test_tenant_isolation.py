"""
Management command to test tenant isolation
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, models
from django.contrib.auth import get_user_model
from ...models import Tenant
from ...utils import SchemaContext

User = get_user_model()


class Command(BaseCommand):
    help = 'Test tenant isolation by creating test data in different schemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant1',
            type=str,
            required=True,
            help='Slug or domain of the first tenant'
        )
        parser.add_argument(
            '--tenant2', 
            type=str,
            required=True,
            help='Slug or domain of the second tenant'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up test data after validation'
        )

    def handle(self, *args, **options):
        tenant1_identifier = options['tenant1']
        tenant2_identifier = options['tenant2']
        cleanup = options.get('cleanup', False)

        # Find tenants
        try:
            tenant1 = Tenant.objects.get(
                models.Q(slug=tenant1_identifier) | 
                models.Q(domain=tenant1_identifier)
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant not found: {tenant1_identifier}')

        try:
            tenant2 = Tenant.objects.get(
                models.Q(slug=tenant2_identifier) | 
                models.Q(domain=tenant2_identifier)
            )
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant not found: {tenant2_identifier}')

        self.stdout.write(f'Testing isolation between tenants:')
        self.stdout.write(f'  Tenant 1: {tenant1.name} (schema: {tenant1.schema_name})')
        self.stdout.write(f'  Tenant 2: {tenant2.name} (schema: {tenant2.schema_name})')

        # Create test data in tenant1
        test_username = 'test_isolation_user'
        
        with SchemaContext(tenant1.schema_name):
            self.stdout.write(f'\nCreating test user in {tenant1.name}...')
            user1 = User.objects.create_user(
                username=test_username,
                email='test@tenant1.com',
                password='testpass123'
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created user {user1.username} in {tenant1.name}'
                )
            )

        # Try to find the same user in tenant2 (should not exist)
        with SchemaContext(tenant2.schema_name):
            self.stdout.write(f'\nChecking for user in {tenant2.name}...')
            user_exists = User.objects.filter(username=test_username).exists()
            
            if user_exists:
                self.stdout.write(
                    self.style.ERROR(
                        f'ISOLATION FAILURE: User found in {tenant2.name}!'
                    )
                )
                raise CommandError('Tenant isolation test failed')
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Good: User not found in {tenant2.name}'
                    )
                )

        # Verify the user still exists in tenant1
        with SchemaContext(tenant1.schema_name):
            user_exists = User.objects.filter(username=test_username).exists()
            if user_exists:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Good: User still exists in {tenant1.name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'ERROR: User disappeared from {tenant1.name}!'
                    )
                )
                raise CommandError('Tenant isolation test failed')

        # Cleanup if requested
        if cleanup:
            self.stdout.write('\nCleaning up test data...')
            with SchemaContext(tenant1.schema_name):
                User.objects.filter(username=test_username).delete()
                self.stdout.write(
                    self.style.SUCCESS('Test data cleaned up')
                )

        self.stdout.write(
            self.style.SUCCESS(
                '\nTenant isolation test passed successfully!'
            )
        )
        
        # Additional tests summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Summary:')
        self.stdout.write('✓ Data created in one tenant is not visible in another')
        self.stdout.write('✓ Each tenant maintains separate data')
        self.stdout.write('✓ Schema isolation is working correctly')
        self.stdout.write('='*50)