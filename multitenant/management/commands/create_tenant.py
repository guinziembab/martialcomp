"""
Management command to create a new tenant
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from ...models import Tenant, Domain
from ...utils import create_schema_for_tenant


class Command(BaseCommand):
    help = 'Create a new tenant with its database schema'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='Name of the organization')
        parser.add_argument('subdomain', type=str, help='Subdomain for the tenant')
        parser.add_argument(
            '--continent',
            type=str,
            choices=[choice[0] for choice in Tenant.CONTINENT_CHOICES],
            default='europe_west',
            help='Continent for pricing'
        )
        parser.add_argument(
            '--plan',
            type=str,
            choices=[choice[0] for choice in Tenant.SUBSCRIPTION_PLAN_CHOICES],
            default='trial',
            help='Subscription plan'
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Custom domain (optional)'
        )

    def handle(self, *args, **options):
        name = options['name']
        subdomain = options['subdomain']
        continent = options['continent']
        plan = options['plan']
        custom_domain = options.get('domain')

        # Generate schema name from subdomain
        schema_name = f'tenant_{subdomain.lower().replace("-", "_")}'
        primary_domain = f'{subdomain}.martialcomp.com'

        try:
            with transaction.atomic():
                # Create the tenant
                tenant = Tenant.objects.create(
                    name=name,
                    schema_name=schema_name,
                    domain=primary_domain,
                    continent=continent,
                    subscription_plan=plan,
                    is_active=True
                )

                # Create the primary domain
                Domain.objects.create(
                    tenant=tenant,
                    domain=primary_domain,
                    is_primary=True
                )

                # Add custom domain if provided
                if custom_domain:
                    Domain.objects.create(
                        tenant=tenant,
                        domain=custom_domain,
                        is_primary=False
                    )

                # Create the schema
                create_schema_for_tenant(tenant)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created tenant "{name}" with schema "{schema_name}"'
                    )
                )
                self.stdout.write(
                    f'Primary domain: {primary_domain}'
                )
                if custom_domain:
                    self.stdout.write(
                        f'Custom domain: {custom_domain}'
                    )

        except Exception as e:
            raise CommandError(f'Error creating tenant: {str(e)}')