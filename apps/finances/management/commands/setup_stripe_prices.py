"""
Management command to create Stripe Product + Prices for subscription billing.

Usage:
    python manage.py setup_stripe_prices

Creates:
    - 1 Stripe Product: "MartialComp Premium"
    - 2 Stripe Prices: mature (999 cents/unit/year), emergent (499 cents/unit/year)

Output: Price IDs to configure in .env as STRIPE_PRICE_MATURE_YEARLY / STRIPE_PRICE_EMERGENT_YEARLY
"""
from django.core.management.base import BaseCommand

from apps.finances.services.stripe_service import StripeService, StripeServiceError

import stripe


class Command(BaseCommand):
    help = "Create Stripe Product and Prices for MartialComp Premium subscription"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without calling Stripe API',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE("=== MartialComp Stripe Price Setup ==="))

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no API calls will be made"))
            self.stdout.write("Would create:")
            self.stdout.write("  Product: MartialComp Premium")
            self.stdout.write("  Price 1: mature - 999 cents EUR / unit / year")
            self.stdout.write("  Price 2: emergent - 499 cents EUR / unit / year")
            return

        try:
            StripeService._configure_stripe()
        except StripeServiceError as e:
            self.stderr.write(self.style.ERROR(f"Stripe config error: {e}"))
            return

        # 1. Create or find Product
        product = self._get_or_create_product()
        if not product:
            return

        self.stdout.write(self.style.SUCCESS(
            f"Product: {product.id} ({product.name})"
        ))

        # 2. Create Prices
        prices = {
            'mature': {'amount': 999, 'nickname': 'Premium Mature (9.99 EUR/member/year)'},
            'emergent': {'amount': 499, 'nickname': 'Premium Emergent (4.99 EUR/member/year)'},
        }

        created = {}
        for tier, config in prices.items():
            price = self._create_price(product.id, config['amount'], config['nickname'])
            if price:
                created[tier] = price.id
                self.stdout.write(self.style.SUCCESS(
                    f"  Price ({tier}): {price.id} - {config['nickname']}"
                ))

        # 3. Print .env config
        if created:
            self.stdout.write("")
            self.stdout.write(self.style.NOTICE("Add these to your .env file:"))
            self.stdout.write(self.style.NOTICE("=" * 50))
            if 'mature' in created:
                self.stdout.write(f"STRIPE_PRICE_MATURE_YEARLY={created['mature']}")
            if 'emergent' in created:
                self.stdout.write(f"STRIPE_PRICE_EMERGENT_YEARLY={created['emergent']}")
            self.stdout.write(self.style.NOTICE("=" * 50))

    def _get_or_create_product(self):
        """Find existing or create new Stripe Product."""
        try:
            # Search for existing product by name
            products = stripe.Product.search(
                query="name:'MartialComp Premium'",
                limit=1,
            )
            if products.data:
                self.stdout.write("Found existing product")
                return products.data[0]

            # Create new
            product = stripe.Product.create(
                name="MartialComp Premium",
                description="MartialComp Premium subscription - unlimited members",
                metadata={'app': 'martialcomp', 'tier': 'premium'},
            )
            self.stdout.write("Created new product")
            return product

        except stripe.error.StripeError as e:
            self.stderr.write(self.style.ERROR(f"Stripe API error: {e}"))
            return None

    def _create_price(self, product_id, amount_cents, nickname):
        """Create a recurring per-unit annual Stripe Price."""
        try:
            price = stripe.Price.create(
                product=product_id,
                unit_amount=amount_cents,
                currency='eur',
                recurring={
                    'interval': 'year',
                    'interval_count': 1,
                    'usage_type': 'licensed',  # per-seat
                },
                nickname=nickname,
                metadata={'app': 'martialcomp'},
            )
            return price
        except stripe.error.StripeError as e:
            self.stderr.write(self.style.ERROR(f"Error creating price: {e}"))
            return None
