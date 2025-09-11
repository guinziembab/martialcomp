from django.core.management.base import BaseCommand
from apps.finances.models.pricing import PricingRegion, VolumeDiscount
from decimal import Decimal

class Command(BaseCommand):
    help = 'Initialise le système de tarification avec les données de la directive'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("ðŸŽ¯ INITIALISATION DU SYSTÃˆME DE TARIFICATION"))
        self.stdout.write("=" * 60)
        
        # Créer les régions tarifaires
        self.setup_pricing_regions()
        
        # Créer les réductions volume
        self.setup_volume_discounts()
        
        self.stdout.write(self.style.SUCCESS("âœ… Système de tarification initialisé avec succès!"))

    def setup_pricing_regions(self):
        """Configure les régions tarifaires selon la directive"""
        self.stdout.write("\nðŸŒ Configuration des régions tarifaires...")
        
        regions_data = [
            ('africa', 'Afrique', Decimal('2.99')),
            ('southeast_asia', 'Asie du Sud-Est', Decimal('3.99')),
            ('south_central_america', 'Amérique du Sud/Centrale', Decimal('4.99')),
            ('eastern_europe', 'Europe de l\'Est', Decimal('5.99')),
            ('western_europe_north_america_oceania', 'Europe de l\'Ouest/Amérique du Nord/Océanie', Decimal('6.99')),
            ('middle_east', 'Moyen-Orient', Decimal('5.99')),
        ]
        
        for region_code, region_name, price in regions_data:
            region, created = PricingRegion.objects.get_or_create(
                name=region_code,
                defaults={
                    'base_price_per_member': price,
                    'currency': 'EUR'
                }
            )
            
            if created:
                self.stdout.write(f"   âœ… Créé: {region_name} - {price}â‚¬")
            else:
                self.stdout.write(f"   â„¹ï¸  Existant: {region_name} - {price}â‚¬")

    def setup_volume_discounts(self):
        """Configure les réductions volume selon la directive"""
        self.stdout.write("\nðŸ“Š Configuration des réductions volume...")
        
        discounts_data = [
            (1, 99, Decimal('0'), 'Prix standard'),
            (100, 249, Decimal('15'), 'Réduction 15%'),
            (250, 499, Decimal('25'), 'Réduction 25%'),
            (500, 999, Decimal('35'), 'Réduction 35%'),
            (1000, 0, Decimal('45'), 'Réduction 45% (1000+ membres)'),
        ]
        
        for start, end, discount, description in discounts_data:
            discount_obj, created = VolumeDiscount.objects.get_or_create(
                member_range_start=start,
                member_range_end=end,
                defaults={
                    'discount_percentage': discount,
                    'description': description
                }
            )
            
            if created:
                self.stdout.write(f"   âœ… Créé: {start}-{end if end > 0 else '+'} membres: -{discount}%")
            else:
                self.stdout.write(f"   â„¹ï¸  Existant: {start}-{end if end > 0 else '+'} membres: -{discount}%")

    def show_pricing_examples(self):
        """Affiche des exemples de tarification"""
        self.stdout.write("\nðŸ’¡ Exemples de tarification:")
        self.stdout.write("-" * 40)
        
        # Exemple Europe de l'Ouest
        region = PricingRegion.objects.get(name='western_europe_north_america_oceania')
        
        examples = [
            (50, "Petit club"),
            (150, "Club moyen"),
            (300, "Grand club"),
            (800, "Très grand club"),
            (1200, "Mégaclub"),
        ]
        
        for members, description in examples:
            discount = VolumeDiscount.get_discount_for_members(members)
            base_price = region.base_price_per_member
            final_price = base_price * (1 - discount / 100)
            total = final_price * members
            
            self.stdout.write(f"   {description} ({members} membres):")
            self.stdout.write(f"     Prix de base: {base_price}â‚¬")
            self.stdout.write(f"     Réduction: -{discount}%")
            self.stdout.write(f"     Prix final: {final_price:.2f}â‚¬/membre")
            self.stdout.write(f"     Total annuel: {total:.2f}â‚¬")
            self.stdout.write("") 

