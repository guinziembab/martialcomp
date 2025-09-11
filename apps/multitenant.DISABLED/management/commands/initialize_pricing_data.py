from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.multitenant.models import SubscriptionTier, PayPerUseFeature, PromotionCode

class Command(BaseCommand):
    help = 'Initialise les données de tarification avec les niveaux d\'abonnement et les fonctionnalités Ã  l\'usage'

    def handle(self, *args, **options):
        # Créer les niveaux d'abonnement
        basic_tier = SubscriptionTier.objects.create(
            name="Basic",
            description="Fonctionnalités essentielles pour les petits clubs et organisations",
            price_monthly=29.99,
            price_annually=299.99,
            max_users=5,
            max_competitions=10,
            max_storage_gb=10,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": False,
                "advanced_analytics": False,
                "custom_branding": False,
                "api_access": False,
                "realtime_scoring": False,
                "bulk_import": False,
                "advanced_finance": False,
                "certification_management": False
            }
        )
        
        standard_tier = SubscriptionTier.objects.create(
            name="Standard",
            description="Fonctionnalités avancées pour les organisations en croissance",
            price_monthly=59.99,
            price_annually=599.99,
            max_users=20,
            max_competitions=50,
            max_storage_gb=50,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": True,
                "advanced_analytics": False,
                "custom_branding": True,
                "api_access": False,
                "realtime_scoring": True,
                "bulk_import": True,
                "advanced_finance": False,
                "certification_management": True
            }
        )
        
        pro_tier = SubscriptionTier.objects.create(
            name="Pro",
            description="Solution complète pour les organisations professionnelles",
            price_monthly=99.99,
            price_annually=999.99,
            max_users=50,
            max_competitions=100,
            max_storage_gb=100,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": True,
                "advanced_analytics": True,
                "custom_branding": True,
                "api_access": True,
                "realtime_scoring": True,
                "bulk_import": True,
                "advanced_finance": True,
                "certification_management": True
            }
        )
        
        # Créer les fonctionnalités Ã  l'usage
        PayPerUseFeature.objects.create(
            name="additional_participants",
            description="Participants supplémentaires au-delÃ  de la limite du plan",
            price_per_unit=2.50,
            unit_label="par participant"
        )
        
        PayPerUseFeature.objects.create(
            name="additional_storage",
            description="Stockage supplémentaire au-delÃ  de la limite du plan",
            price_per_unit=5.00,
            unit_label="par Go"
        )
        
        PayPerUseFeature.objects.create(
            name="premium_support",
            description="Sessions de support premium avec un spécialiste dédié",
            price_per_unit=50.00,
            unit_label="par session"
        )
        
        # Créer quelques codes promotionnels
        from apps.multitenant.models.pricing import PromotionCode
        
        PromotionCode.objects.create(
            code="WELCOME20",
            description="20% de réduction pour les nouveaux utilisateurs",
            discount_type="percentage",
            discount_value=20.00,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=90),
            max_uses=100,
            current_uses=0
        )
        
        PromotionCode.objects.create(
            code="MARTIAL2025",
            description="50â‚¬ de réduction sur l'abonnement annuel",
            discount_type="fixed",
            discount_value=50.00,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=60),
            max_uses=50,
            current_uses=0
        )
        
        PromotionCode.objects.create(
            code="TRYITFREE",
            description="3 mois gratuits avec l'abonnement annuel",
            discount_type="free_months",
            discount_value=3.00,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timezone.timedelta(days=30),
            max_uses=25,
            current_uses=0
        )
        
        self.stdout.write(self.style.SUCCESS('Données de tarification initialisées avec succès'))

