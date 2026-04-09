"""
Assigns all existing products (with organization=NULL) to a given user's organization.

Usage:
    python manage.py assign_products_to_organization KP_admin
    python manage.py assign_products_to_organization KP_admin --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Assign all orphan products (organization=NULL) to a user's organization."

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username whose organization to use')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    def handle(self, *args, **options):
        username = options['username']
        dry_run = options['dry_run']

        # 1. Find the user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found.")

        # 2. Get their organization
        organization = None
        try:
            profile = user.profile
            organization = profile.organization
        except Exception:
            pass

        if not organization:
            # Fallback: check via practitioner
            if hasattr(user, 'practitioners'):
                practitioner = user.practitioners.first()
                if practitioner and practitioner.organization:
                    organization = practitioner.organization

        if not organization:
            # Fallback: check via club ownership
            from apps.competitions.models import Club
            club = Club.objects.filter(owner=user).first()
            if club and club.organization:
                organization = club.organization

        if not organization:
            raise CommandError(
                f"User '{username}' has no associated organization. "
                f"Please assign an organization to this user first."
            )

        self.stdout.write(f"Organization found: {organization.name} (id={organization.id})")

        # 3. Find orphan products
        from apps.shop.models import Product
        orphan_products = Product.objects.filter(organization__isnull=True)
        count = orphan_products.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No orphan products found. Nothing to do."))
            return

        self.stdout.write(f"Found {count} products with organization=NULL:")
        for p in orphan_products:
            self.stdout.write(f"  - [{p.id}] {p.name}")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would assign {count} products to '{organization.name}'. "
                f"Run without --dry-run to apply."
            ))
            return

        # 4. Assign them
        updated = orphan_products.update(organization=organization)
        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Assigned {updated} products to organization '{organization.name}'."
        ))
