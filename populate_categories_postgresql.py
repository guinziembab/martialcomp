#!/usr/bin/env python3
"""
Script Django pour populer les catégories d'arts martiaux dans PostgreSQL
Basé sur le document martial_arts_shop_categories.md
"""

import os
import sys
import django
from django.db import transaction
from django.utils.text import slugify

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from shop.models.category import Category
from competitions.models.discipline import Discipline

# Structure des catégories basée sur martial_arts_shop_categories.md
categories_structure = [
    # 1. TENUES & KIMONOS
    {
        'name': 'Tenues & Kimonos',
        'description': 'Tenues traditionnelles et modernes pour tous les arts martiaux',
        'order': 1,
        'children': [
            {
                'name': 'Kimonos Karaté',
                'description': 'Kimonos spécialisés pour la pratique du karaté - Coton léger pour débutants, coton lourd 12-16oz pour compétition',
                'disciplines': ['Karaté'],
            },
            {
                'name': 'Kimonos Judo',
                'description': 'Judogis traditionnels et de compétition - Grammages 350g à 750g selon le niveau',
                'disciplines': ['Judo'],
            },
            {
                'name': 'Kimonos Jiu-Jitsu',
                'description': 'Kimonos adaptés au Jiu-Jitsu brésilien et traditionnel - Tissage spécial résistant',
                'disciplines': ['Jiu-Jitsu Brésilien'],
            },
            {
                'name': 'Tenues Taekwondo',
                'description': 'Doboks pour la pratique du Taekwondo - Modèles ITF et WTF',
                'disciplines': ['Taekwondo'],
            },
            {
                'name': 'Tenues Kung-Fu',
                'description': 'Tenues traditionnelles chinoises - Soie, coton et matériaux modernes',
                'disciplines': ['Kung-Fu', 'Wushu'],
            },
            {
                'name': 'Tenues Arts Martiaux Mixtes',
                'description': 'Équipements pour MMA et sports de combat - Shorts, rashguards, gants',
                'disciplines': ['MMA', 'Grappling'],
            },
        ]
    },
    # 2. GRADES & CEINTURES
    {
        'name': 'Grades & Ceintures',
        'description': 'Ceintures et systèmes de grades pour tous les arts martiaux',
        'order': 2,
        'children': [
            {
                'name': 'Ceintures de Karaté',
                'description': 'Ceintures colorées selon la tradition - Blanc, jaune, orange, vert, bleu, marron, noir',
                'disciplines': ['Karaté'],
            },
            {
                'name': 'Ceintures de Judo',
                'description': 'Ceintures officielles de Judo - Système Dan et Kyu traditionnel',
                'disciplines': ['Judo'],
            },
            {
                'name': 'Ceintures de Taekwondo',
                'description': 'Ceintures selon les standards WTF/ITF - Système de couleurs spécifique',
                'disciplines': ['Taekwondo'],
            },
            {
                'name': 'Ceintures de Jiu-Jitsu',
                'description': 'Ceintures brésiliennes authentiques - Blanc, bleu, violet, marron, noir',
                'disciplines': ['Jiu-Jitsu Brésilien'],
            },
            {
                'name': 'Accessoires de Grade',
                'description': 'Barrettes, broderies et personnalisations - Écussons, galons, marquages',
                'disciplines': [],
            },
        ]
    },
    # 3. PROTECTIONS & SÉCURITÉ
    {
        'name': 'Protections & Sécurité',
        'description': 'Équipements de protection pour l\'entraînement et la compétition',
        'order': 3,
        'children': [
            {
                'name': 'Protège-Tibias',
                'description': 'Protection des jambes pour les combats - Mousse, cuir et matériaux composites',
                'disciplines': ['Karaté', 'Taekwondo', 'Kickboxing', 'MMA'],
            },
            {
                'name': 'Gants de Combat',
                'description': 'Gants pour boxe, MMA et arts martiaux - Diverses densités et matériaux',
                'disciplines': ['Boxe', 'MMA', 'Karaté', 'Taekwondo'],
            },
            {
                'name': 'Casques de Protection',
                'description': 'Casques pour sparring et compétition - Protection tête et visage',
                'disciplines': ['Boxe', 'MMA', 'Karaté', 'Taekwondo'],
            },
            {
                'name': 'Protections Corporelles',
                'description': 'Plastrons, coquilles et protections diverses - Protection complète du corps',
                'disciplines': ['Karaté', 'Taekwondo', 'MMA'],
            },
            {
                'name': 'Protège-Dents',
                'description': 'Protection dentaire personnalisée - Simple et double densité',
                'disciplines': ['MMA', 'Boxe', 'Rugby'],
            },
        ]
    },
    # 4. MATÉRIEL D'ENTRAÎNEMENT
    {
        'name': 'Matériel d\'Entraînement',
        'description': 'Équipements pour l\'entraînement technique et physique',
        'order': 4,
        'children': [
            {
                'name': 'Sacs de Frappe',
                'description': 'Sacs lourds et légers pour l\'entraînement - Suspendus et sur pied',
                'disciplines': ['Boxe', 'MMA', 'Karaté', 'Muay Thai'],
            },
            {
                'name': 'Pattes d\'Ours',
                'description': 'Paos et mitaines d\'entraînement - Travail de précision et technique',
                'disciplines': ['Boxe', 'MMA', 'Karaté', 'Taekwondo'],
            },
            {
                'name': 'Makiwaras',
                'description': 'Planches de frappe traditionnelles - Entraînement du conditionnement',
                'disciplines': ['Karaté', 'Kung-Fu'],
            },
            {
                'name': 'Mannequins d\'Entraînement',
                'description': 'Dummy et partenaires d\'entraînement - Bois, mousse et matériaux modernes',
                'disciplines': ['Wing Chun', 'Jiu-Jitsu', 'MMA'],
            },
            {
                'name': 'Accessoires de Forme',
                'description': 'Nunchakus, bâtons et armes traditionnelles - Entraînement aux kata et formes',
                'disciplines': ['Karaté', 'Kung-Fu', 'Kobudo'],
            },
        ]
    },
    # 5. ÉQUIPEMENT DOJO/CLUB
    {
        'name': 'Équipement Dojo/Club',
        'description': 'Matériel pour l\'équipement des dojos et clubs',
        'order': 5,
        'children': [
            {
                'name': 'Tatamis',
                'description': 'Tapis de sol et revêtements - Puzzle, rouleau et tatamis traditionnels',
                'disciplines': [],
            },
            {
                'name': 'Miroirs de Dojo',
                'description': 'Miroirs de sécurité pour entraînement - Incassables et résistants aux chocs',
                'disciplines': [],
            },
            {
                'name': 'Matériel de Rangement',
                'description': 'Vestiaires, casiers et organisation - Stockage équipements et effets personnels',
                'disciplines': [],
            },
            {
                'name': 'Signalétique',
                'description': 'Panneaux, règlements et décoration - Affichage réglementaire et décoratif',
                'disciplines': [],
            },
        ]
    },
    # 6. LIVRES & MÉDIAS
    {
        'name': 'Livres & Médias',
        'description': 'Documentation technique et pédagogique',
        'order': 6,
        'children': [
            {
                'name': 'Livres Techniques',
                'description': 'Manuels et guides d\'entraînement - Techniques, philosophie, histoire',
                'disciplines': [],
            },
            {
                'name': 'DVDs d\'Entraînement',
                'description': 'Supports vidéo pédagogiques - Cours et démonstrations techniques',
                'disciplines': [],
            },
            {
                'name': 'Histoire des Arts Martiaux',
                'description': 'Ouvrages historiques et philosophiques - Origines et évolution des arts martiaux',
                'disciplines': [],
            },
        ]
    },
    # 7. TROPHÉES & RÉCOMPENSES
    {
        'name': 'Trophées & Récompenses',
        'description': 'Récompenses et prix pour compétitions',
        'order': 7,
        'children': [
            {
                'name': 'Trophées',
                'description': 'Coupes et trophées personnalisables - Métal, résine et matériaux nobles',
                'disciplines': [],
            },
            {
                'name': 'Médailles',
                'description': 'Médailles de compétition - Or, argent, bronze avec personnalisation',
                'disciplines': [],
            },
            {
                'name': 'Diplômes & Certificats',
                'description': 'Reconnaissance officielle - Parchemins et certificats de grade',
                'disciplines': [],
            },
        ]
    },
    # 8. ACCESSOIRES & LIFESTYLE
    {
        'name': 'Accessoires & Lifestyle',
        'description': 'Accessoires du quotidien pour pratiquants',
        'order': 8,
        'children': [
            {
                'name': 'Sacs de Sport',
                'description': 'Transport d\'équipement - Sacs à dos, sacs de voyage et housses',
                'disciplines': [],
            },
            {
                'name': 'Vêtements Casual',
                'description': 'T-shirts, sweats et casual wear - Vêtements aux couleurs des disciplines',
                'disciplines': [],
            },
            {
                'name': 'Accessoires Déco',
                'description': 'Objets décoratifs et cadeaux - Statuettes, calligraphies, objets d\'art',
                'disciplines': [],
            },
        ]
    },
    # 9. SANTÉ & RÉCUPÉRATION
    {
        'name': 'Santé & Récupération',
        'description': 'Produits pour la récupération et la santé',
        'order': 9,
        'children': [
            {
                'name': 'Soins Corporels',
                'description': 'Baumes, huiles et soins - Préparation et récupération musculaire',
                'disciplines': [],
            },
            {
                'name': 'Compléments Nutritionnels',
                'description': 'Nutrition sportive - Protéines, vitamines et suppléments',
                'disciplines': [],
            },
            {
                'name': 'Matériel de Récupération',
                'description': 'Rouleaux, balles de massage - Équipements de physiothérapie',
                'disciplines': [],
            },
        ]
    },
    # 10. PERSONNALISATION & SERVICES
    {
        'name': 'Personnalisation & Services',
        'description': 'Services de personnalisation et broderie',
        'order': 10,
        'children': [
            {
                'name': 'Broderie',
                'description': 'Personnalisation textile - Noms, logos, écussons sur kimonos',
                'disciplines': [],
            },
            {
                'name': 'Impression',
                'description': 'Impression sur textile et objets - Sérigraphie, transfert, numérique',
                'disciplines': [],
            },
            {
                'name': 'Gravure',
                'description': 'Gravure sur métaux et matériaux durs - Trophées, plaques, bijoux',
                'disciplines': [],
            },
        ]
    },
]

def create_categories():
    """Créer les catégories d'arts martiaux dans PostgreSQL"""
    
    with transaction.atomic():
        # Vérifier si des catégories existent déjà
        existing_count = Category.objects.count()
        if existing_count > 0:
            print(f"✓ {existing_count} catégories existantes détectées")
            response = input("Supprimer et recréer toutes les catégories? (y/N): ").strip().lower()
            if response == 'y':
                Category.objects.all().delete()
                print("✓ Catégories supprimées")
            else:
                print("✓ Conservation des catégories existantes")
                return
        
        # Récupérer les disciplines disponibles
        disciplines_map = {d.name: d for d in Discipline.objects.all()}
        
        print(f"📊 Disciplines disponibles: {len(disciplines_map)}")
        for discipline_name in disciplines_map.keys():
            print(f"  - {discipline_name}")
        
        total_created = 0
        
        # Créer les catégories principales et leurs sous-catégories
        for category_data in categories_structure:
            # Créer la catégorie principale
            main_category = Category.objects.create(
                name=category_data['name'],
                slug=slugify(category_data['name']),
                description=category_data['description'],
                order=category_data['order'],
                is_active=True
            )
            
            print(f"✓ Catégorie principale créée: {main_category.name} (ID: {main_category.id})")
            total_created += 1
            
            # Créer les sous-catégories
            for i, child_data in enumerate(category_data['children'], 1):
                child_category = Category.objects.create(
                    name=child_data['name'],
                    slug=slugify(child_data['name']),
                    description=child_data['description'],
                    parent=main_category,
                    order=i,
                    is_active=True
                )
                
                # Associer les disciplines si spécifiées
                if 'disciplines' in child_data and child_data['disciplines']:
                    for discipline_name in child_data['disciplines']:
                        if discipline_name in disciplines_map:
                            child_category.disciplines.add(disciplines_map[discipline_name])
                            print(f"    📎 Discipline associée: {discipline_name}")
                        else:
                            print(f"    ⚠️  Discipline non trouvée: {discipline_name}")
                
                print(f"  ✓ Sous-catégorie créée: {child_category.name} (ID: {child_category.id})")
                total_created += 1
        
        print("\n" + "="*70)
        print("🎯 CATÉGORIES D'ARTS MARTIAUX CRÉÉES AVEC SUCCÈS DANS POSTGRESQL!")
        print("="*70)
        
        # Statistiques finales
        main_categories = Category.objects.filter(parent=None).count()
        sub_categories = Category.objects.filter(parent__isnull=False).count()
        total_categories = Category.objects.count()
        
        print(f"📊 Catégories principales: {main_categories}")
        print(f"📋 Sous-catégories: {sub_categories}")
        print(f"🔢 Total: {total_categories} catégories")
        print(f"🏗️  Nouvellement créées: {total_created}")
        
        print("\n🔗 URLs disponibles:")
        print("  📱 Admin Django: http://127.0.0.1:8000/admin/shop/category/")
        print("  🛍️  Création produit: http://127.0.0.1:8000/shop/dashboard/club/product/create/")
        print("="*70)

def display_category_tree():
    """Afficher l'arbre des catégories"""
    print("\n🌳 STRUCTURE DES CATÉGORIES:")
    print("="*50)
    
    main_categories = Category.objects.filter(parent=None).order_by('order')
    for main_cat in main_categories:
        children_count = main_cat.children.count()
        print(f"📂 {main_cat.name} ({children_count} sous-catégories)")
        
        for sub_cat in main_cat.children.all().order_by('order'):
            disciplines = list(sub_cat.disciplines.all())
            if disciplines:
                disciplines_str = ', '.join([d.name for d in disciplines])
                print(f"  📄 {sub_cat.name} - [{disciplines_str}]")
            else:
                print(f"  📄 {sub_cat.name} - [Toutes disciplines]")

def verify_database_connection():
    """Vérifier la connexion à la base de données"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Connexion PostgreSQL réussie")
        return True
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        return False

if __name__ == '__main__':
    print("🥋 MISE EN PLACE DES CATÉGORIES D'ARTS MARTIAUX - POSTGRESQL")
    print("=" * 70)
    
    # Vérifier la connexion
    if not verify_database_connection():
        print("❌ Impossible de se connecter à PostgreSQL")
        sys.exit(1)
    
    try:
        create_categories()
        display_category_tree()
        
        print("\n✅ IMPLÉMENTATION TERMINÉE AVEC SUCCÈS!")
        print("Les catégories sont maintenant disponibles dans l'admin Django et le formulaire de création de produits.")
        
    except Exception as e:
        print(f"\n❌ ERREUR lors de la création des catégories: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)