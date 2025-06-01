"""
Commande Django pour créer les catégories d'arts martiaux
Usage: python manage.py create_martial_arts_categories [--reset]
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from shop.models.category import Category


class Command(BaseCommand):
    help = 'Créer les catégories d\'arts martiaux pour la boutique'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Supprimer toutes les catégories existantes avant création',
        )

    def handle(self, *args, **options):
        self.stdout.write("🥋 CRÉATION DES CATÉGORIES D'ARTS MARTIAUX")
        self.stdout.write("=" * 50)

        # Structure des catégories basée sur martial_arts_shop_categories.md
        categories_data = [
            # 1. TENUES & KIMONOS
            {
                'name': 'Tenues & Kimonos',
                'description': 'Tenues traditionnelles et modernes pour tous les arts martiaux',
                'order': 1,
                'children': [
                    {'name': 'Kimonos Karaté', 'description': 'Kimonos spécialisés pour la pratique du karaté - Coton léger pour débutants, coton lourd 12-16oz pour compétition'},
                    {'name': 'Kimonos Judo', 'description': 'Judogis traditionnels et de compétition - Grammages 350g à 750g selon le niveau'},
                    {'name': 'Kimonos Jiu-Jitsu', 'description': 'Kimonos adaptés au Jiu-Jitsu brésilien et traditionnel - Tissage spécial résistant'},
                    {'name': 'Tenues Taekwondo', 'description': 'Doboks pour la pratique du Taekwondo - Modèles ITF et WTF'},
                    {'name': 'Tenues Kung-Fu', 'description': 'Tenues traditionnelles chinoises - Soie, coton et matériaux modernes'},
                    {'name': 'Tenues Arts Martiaux Mixtes', 'description': 'Équipements pour MMA et sports de combat - Shorts, rashguards, gants'},
                ]
            },
            # 2. GRADES & CEINTURES
            {
                'name': 'Grades & Ceintures',
                'description': 'Ceintures et systèmes de grades pour tous les arts martiaux',
                'order': 2,
                'children': [
                    {'name': 'Ceintures de Karaté', 'description': 'Ceintures colorées selon la tradition - Blanc, jaune, orange, vert, bleu, marron, noir'},
                    {'name': 'Ceintures de Judo', 'description': 'Ceintures officielles de Judo - Système Dan et Kyu traditionnel'},
                    {'name': 'Ceintures de Taekwondo', 'description': 'Ceintures selon les standards WTF/ITF - Système de couleurs spécifique'},
                    {'name': 'Ceintures de Jiu-Jitsu', 'description': 'Ceintures brésiliennes authentiques - Blanc, bleu, violet, marron, noir'},
                    {'name': 'Accessoires de Grade', 'description': 'Barrettes, broderies et personnalisations - Écussons, galons, marquages'},
                ]
            },
            # 3. PROTECTIONS & SÉCURITÉ
            {
                'name': 'Protections & Sécurité',
                'description': 'Équipements de protection pour l\'entraînement et la compétition',
                'order': 3,
                'children': [
                    {'name': 'Protège-Tibias', 'description': 'Protection des jambes pour les combats - Mousse, cuir et matériaux composites'},
                    {'name': 'Gants de Combat', 'description': 'Gants pour boxe, MMA et arts martiaux - Diverses densités et matériaux'},
                    {'name': 'Casques de Protection', 'description': 'Casques pour sparring et compétition - Protection tête et visage'},
                    {'name': 'Protections Corporelles', 'description': 'Plastrons, coquilles et protections diverses - Protection complète du corps'},
                    {'name': 'Protège-Dents', 'description': 'Protection dentaire personnalisée - Simple et double densité'},
                ]
            },
            # 4. MATÉRIEL D'ENTRAÎNEMENT
            {
                'name': 'Matériel d\'Entraînement',
                'description': 'Équipements pour l\'entraînement technique et physique',
                'order': 4,
                'children': [
                    {'name': 'Sacs de Frappe', 'description': 'Sacs lourds et légers pour l\'entraînement - Suspendus et sur pied'},
                    {'name': 'Pattes d\'Ours', 'description': 'Paos et mitaines d\'entraînement - Travail de précision et technique'},
                    {'name': 'Makiwaras', 'description': 'Planches de frappe traditionnelles - Entraînement du conditionnement'},
                    {'name': 'Mannequins d\'Entraînement', 'description': 'Dummy et partenaires d\'entraînement - Bois, mousse et matériaux modernes'},
                    {'name': 'Accessoires de Forme', 'description': 'Nunchakus, bâtons et armes traditionnelles - Entraînement aux kata et formes'},
                ]
            },
            # 5. ÉQUIPEMENT DOJO/CLUB
            {
                'name': 'Équipement Dojo/Club',
                'description': 'Matériel pour l\'équipement des dojos et clubs',
                'order': 5,
                'children': [
                    {'name': 'Tatamis', 'description': 'Tapis de sol et revêtements - Puzzle, rouleau et tatamis traditionnels'},
                    {'name': 'Miroirs de Dojo', 'description': 'Miroirs de sécurité pour entraînement - Incassables et résistants aux chocs'},
                    {'name': 'Matériel de Rangement', 'description': 'Vestiaires, casiers et organisation - Stockage équipements et effets personnels'},
                    {'name': 'Signalétique', 'description': 'Panneaux, règlements et décoration - Affichage réglementaire et décoratif'},
                ]
            },
            # 6. LIVRES & MÉDIAS
            {
                'name': 'Livres & Médias',
                'description': 'Documentation technique et pédagogique',
                'order': 6,
                'children': [
                    {'name': 'Livres Techniques', 'description': 'Manuels et guides d\'entraînement - Techniques, philosophie, histoire'},
                    {'name': 'DVDs d\'Entraînement', 'description': 'Supports vidéo pédagogiques - Cours et démonstrations techniques'},
                    {'name': 'Histoire des Arts Martiaux', 'description': 'Ouvrages historiques et philosophiques - Origines et évolution des arts martiaux'},
                ]
            },
            # 7. TROPHÉES & RÉCOMPENSES
            {
                'name': 'Trophées & Récompenses',
                'description': 'Récompenses et prix pour compétitions',
                'order': 7,
                'children': [
                    {'name': 'Trophées', 'description': 'Coupes et trophées personnalisables - Métal, résine et matériaux nobles'},
                    {'name': 'Médailles', 'description': 'Médailles de compétition - Or, argent, bronze avec personnalisation'},
                    {'name': 'Diplômes & Certificats', 'description': 'Reconnaissance officielle - Parchemins et certificats de grade'},
                ]
            },
            # 8. ACCESSOIRES & LIFESTYLE
            {
                'name': 'Accessoires & Lifestyle',
                'description': 'Accessoires du quotidien pour pratiquants',
                'order': 8,
                'children': [
                    {'name': 'Sacs de Sport', 'description': 'Transport d\'équipement - Sacs à dos, sacs de voyage et housses'},
                    {'name': 'Vêtements Casual', 'description': 'T-shirts, sweats et casual wear - Vêtements aux couleurs des disciplines'},
                    {'name': 'Accessoires Déco', 'description': 'Objets décoratifs et cadeaux - Statuettes, calligraphies, objets d\'art'},
                ]
            },
            # 9. SANTÉ & RÉCUPÉRATION
            {
                'name': 'Santé & Récupération',
                'description': 'Produits pour la récupération et la santé',
                'order': 9,
                'children': [
                    {'name': 'Soins Corporels', 'description': 'Baumes, huiles et soins - Préparation et récupération musculaire'},
                    {'name': 'Compléments Nutritionnels', 'description': 'Nutrition sportive - Protéines, vitamines et suppléments'},
                    {'name': 'Matériel de Récupération', 'description': 'Rouleaux, balles de massage - Équipements de physiothérapie'},
                ]
            },
            # 10. PERSONNALISATION & SERVICES
            {
                'name': 'Personnalisation & Services',
                'description': 'Services de personnalisation et broderie',
                'order': 10,
                'children': [
                    {'name': 'Broderie', 'description': 'Personnalisation textile - Noms, logos, écussons sur kimonos'},
                    {'name': 'Impression', 'description': 'Impression sur textile et objets - Sérigraphie, transfert, numérique'},
                    {'name': 'Gravure', 'description': 'Gravure sur métaux et matériaux durs - Trophées, plaques, bijoux'},
                ]
            },
        ]

        with transaction.atomic():
            # Réinitialiser si demandé
            if options['reset']:
                deleted_count = Category.objects.count()
                Category.objects.all().delete()
                self.stdout.write(f"🗑️  {deleted_count} catégories existantes supprimées")

            # Vérifier les catégories existantes
            existing_count = Category.objects.count()
            if existing_count > 0:
                self.stdout.write(f"⚠️  {existing_count} catégories déjà présentes")
                self.stdout.write("Utilisez --reset pour supprimer et recréer")
                return

            total_created = 0

            # Créer les catégories
            for cat_data in categories_data:
                # Créer la catégorie principale
                main_category = Category.objects.create(
                    name=cat_data['name'],
                    slug=slugify(cat_data['name']),
                    description=cat_data['description'],
                    order=cat_data['order'],
                    is_active=True
                )
                
                self.stdout.write(f"✅ {main_category.name} (ID: {main_category.id})")
                total_created += 1

                # Créer les sous-catégories
                for i, child in enumerate(cat_data['children'], 1):
                    child_category = Category.objects.create(
                        name=child['name'],
                        slug=slugify(child['name']),
                        description=child['description'],
                        parent=main_category,
                        order=i,
                        is_active=True
                    )
                    
                    self.stdout.write(f"  ↳ {child_category.name} (ID: {child_category.id})")
                    total_created += 1

            self.stdout.write("\n" + "="*60)
            self.stdout.write("🎯 CATÉGORIES D'ARTS MARTIAUX CRÉÉES AVEC SUCCÈS!")
            self.stdout.write("="*60)
            
            # Statistiques finales
            main_count = Category.objects.filter(parent=None).count()
            sub_count = Category.objects.filter(parent__isnull=False).count()
            
            self.stdout.write(f"📊 Catégories principales: {main_count}")
            self.stdout.write(f"📋 Sous-catégories: {sub_count}")
            self.stdout.write(f"🔢 Total créé: {total_created}")
            
            self.stdout.write("\n🔗 URLs disponibles:")
            self.stdout.write("  📱 Admin: http://127.0.0.1:8000/admin/shop/category/")
            self.stdout.write("  🛍️  Boutique: http://127.0.0.1:8000/shop/dashboard/club/product/create/")
            self.stdout.write("="*60)