#!/usr/bin/env python3
"""
Script pour convertir les champs brand et supplier de ForeignKey vers CharField.
Ce script migre les données existantes et modifie la structure de la base.
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction, connection
from shop.models import Product

def convert_brand_supplier_fields():
    """
    Convertit les champs brand et supplier de ForeignKey vers CharField.
    """
    print("🔄 Conversion des champs marque et fournisseur vers du texte libre...")
    
    try:
        with transaction.atomic():
            # Utiliser du SQL direct pour modifier la structure
            with connection.cursor() as cursor:
                print("1. Vérification de la structure actuelle...")
                
                # Vérifier si les colonnes existent déjà en tant que texte
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'shop_product' 
                    AND column_name IN ('brand', 'supplier', 'brand_id', 'supplier_id')
                """)
                columns = cursor.fetchall()
                print(f"Colonnes trouvées: {columns}")
                
                # Déterminer quelles colonnes existent
                has_brand_id = any(col[0] == 'brand_id' for col in columns)
                has_supplier_id = any(col[0] == 'supplier_id' for col in columns)
                has_brand_text = any(col[0] == 'brand' and 'char' in col[1].lower() for col in columns)
                has_supplier_text = any(col[0] == 'supplier' and 'char' in col[1].lower() for col in columns)
                
                print(f"brand_id existe: {has_brand_id}")
                print(f"supplier_id existe: {has_supplier_id}")
                print(f"brand (text) existe: {has_brand_text}")
                print(f"supplier (text) existe: {has_supplier_text}")
                
                # Ajouter les nouvelles colonnes texte si elles n'existent pas
                if not has_brand_text:
                    print("2. Ajout de la colonne brand (texte)...")
                    cursor.execute("""
                        ALTER TABLE shop_product 
                        ADD COLUMN brand VARCHAR(100) DEFAULT ''
                    """)
                
                if not has_supplier_text:
                    print("3. Ajout de la colonne supplier (texte)...")
                    cursor.execute("""
                        ALTER TABLE shop_product 
                        ADD COLUMN supplier VARCHAR(100) DEFAULT ''
                    """)
                
                # Migration des données existantes si les FK existent
                if has_brand_id:
                    print("4. Migration des données brand...")
                    cursor.execute("""
                        UPDATE shop_product 
                        SET brand = COALESCE(shop_brand.name, '') 
                        FROM shop_brand 
                        WHERE shop_product.brand_id = shop_brand.id
                    """)
                    
                    print("5. Suppression de la contrainte FK brand_id...")
                    # Supprimer la contrainte FK et la colonne
                    cursor.execute("""
                        ALTER TABLE shop_product 
                        DROP CONSTRAINT IF EXISTS shop_product_brand_id_fkey
                    """)
                    cursor.execute("""
                        ALTER TABLE shop_product 
                        DROP COLUMN IF EXISTS brand_id
                    """)
                
                if has_supplier_id:
                    print("6. Migration des données supplier...")
                    cursor.execute("""
                        UPDATE shop_product 
                        SET supplier = COALESCE(shop_supplier.name, '') 
                        FROM shop_supplier 
                        WHERE shop_product.supplier_id = shop_supplier.id
                    """)
                    
                    print("7. Suppression de la contrainte FK supplier_id...")
                    # Supprimer la contrainte FK et la colonne
                    cursor.execute("""
                        ALTER TABLE shop_product 
                        DROP CONSTRAINT IF EXISTS shop_product_supplier_id_fkey
                    """)
                    cursor.execute("""
                        ALTER TABLE shop_product 
                        DROP COLUMN IF EXISTS supplier_id
                    """)
                
                print("8. Mise à jour des contraintes...")
                # S'assurer que les colonnes ne sont pas NULL
                cursor.execute("""
                    ALTER TABLE shop_product 
                    ALTER COLUMN brand SET NOT NULL
                """)
                cursor.execute("""
                    ALTER TABLE shop_product 
                    ALTER COLUMN supplier SET NOT NULL
                """)
                
        print("✅ Conversion terminée avec succès!")
        
        # Vérifier les résultats
        print("\n📊 Vérification des données migrées:")
        products_with_brand = Product.objects.exclude(brand='').count()
        products_with_supplier = Product.objects.exclude(supplier='').count()
        total_products = Product.objects.count()
        
        print(f"Total produits: {total_products}")
        print(f"Produits avec marque: {products_with_brand}")
        print(f"Produits avec fournisseur: {products_with_supplier}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {e}")
        print("Détails de l'erreur:")
        import traceback
        traceback.print_exc()

def create_categories():
    """
    Crée les catégories d'équipement d'arts martiaux.
    """
    print("\n🥋 Création des catégories d'équipement d'arts martiaux...")
    
    try:
        from shop.models.category import Category
        from competitions.models import Discipline
        
        # Catégories principales d'équipement d'arts martiaux
        categories_data = [
            # 1. Équipement de protection
            {
                'name': 'Équipement de protection',
                'description': 'Protections pour la sécurité des pratiquants',
                'children': [
                    {'name': 'Casques et protections tête', 'description': 'Casques de boxe, protège-oreilles, grilles'},
                    {'name': 'Protections corps', 'description': 'Plastrons, gilets de protection, coquilles'},
                    {'name': 'Protections jambes', 'description': 'Protège-tibias, genouillères, chevillières'},
                    {'name': 'Protections bras et mains', 'description': 'Protège-avant-bras, gants, mitaines'},
                    {'name': 'Protections pieds', 'description': 'Protège-pieds, chaussons de combat'},
                ]
            },
            
            # 2. Vêtements et uniformes
            {
                'name': 'Vêtements et uniformes',
                'description': 'Tenues traditionnelles et modernes pour la pratique',
                'children': [
                    {'name': 'Kimonos et Gi', 'description': 'Kimonos karaté, judo, jiu-jitsu, aïkido'},
                    {'name': 'Dobok Taekwondo', 'description': 'Tenues spécifiques au taekwondo'},
                    {'name': 'Tenues de boxe', 'description': 'Shorts, débardeurs, robes de boxe'},
                    {'name': 'Tenues d\'entraînement', 'description': 'Joggings, t-shirts techniques, rashguards'},
                    {'name': 'Accessoires vestimentaires', 'description': 'Ceintures, bandeaux, chaussettes'},
                ]
            },
            
            # 3. Gants de combat
            {
                'name': 'Gants de combat',
                'description': 'Gants spécialisés selon les disciplines',
                'children': [
                    {'name': 'Gants de boxe', 'description': 'Gants anglaise, française, thaï'},
                    {'name': 'Gants MMA', 'description': 'Gants combat libre, grappling'},
                    {'name': 'Gants karaté', 'description': 'Gants semi-contact, contact léger'},
                    {'name': 'Mitaines d\'entraînement', 'description': 'Gants légers pour sparring'},
                    {'name': 'Gants spécialisés', 'description': 'Wing chun, krav maga, self-défense'},
                ]
            },
            
            # 4. Matériel d'entraînement
            {
                'name': 'Matériel d\'entraînement',
                'description': 'Équipements pour améliorer la technique et la condition physique',
                'children': [
                    {'name': 'Sacs de frappe', 'description': 'Sacs lourds, speed bags, sacs de sol'},
                    {'name': 'Paos et boucliers', 'description': 'Pattes d\'ours, boucliers de frappe, focus mitts'},
                    {'name': 'Mannequins d\'entraînement', 'description': 'Dummy de wing chun, mannequins grappling'},
                    {'name': 'Équipements de cardio', 'description': 'Cordes à sauter, échelles d\'agilité'},
                    {'name': 'Matériel de musculation', 'description': 'Poids, élastiques, kettlebells spécialisés'},
                ]
            },
            
            # 5. Chaussures et équipements pieds
            {
                'name': 'Chaussures et équipements pieds',
                'description': 'Chaussures et accessoires pour les pieds',
                'children': [
                    {'name': 'Chaussures de boxe', 'description': 'Chaussures montantes et basses'},
                    {'name': 'Chaussures de taekwondo', 'description': 'Chaussures spécifiques TKD'},
                    {'name': 'Chaussures arts martiaux', 'description': 'Chaussures kung fu, karaté'},
                    {'name': 'Chaussons et protections', 'description': 'Chaussons souples, protège-pieds'},
                ]
            },
        ]
        
        created_count = 0
        
        for category_data in categories_data:
            # Créer ou récupérer la catégorie parent
            parent_category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'description': category_data['description'],
                    'is_active': True,
                    'order': created_count
                }
            )
            
            if created:
                created_count += 1
                print(f"✅ Catégorie parent créée: {parent_category.name}")
            else:
                print(f"ℹ️  Catégorie parent existe déjà: {parent_category.name}")
            
            # Créer les sous-catégories
            if 'children' in category_data:
                for i, child_data in enumerate(category_data['children']):
                    child_category, created = Category.objects.get_or_create(
                        name=child_data['name'],
                        parent=parent_category,
                        defaults={
                            'description': child_data['description'],
                            'is_active': True,
                            'order': i
                        }
                    )
                    
                    if created:
                        created_count += 1
                        print(f"  ✅ Sous-catégorie créée: {child_category.name}")
                    else:
                        print(f"  ℹ️  Sous-catégorie existe déjà: {child_category.name}")
        
        print(f"\n🎉 Terminé ! {created_count} nouvelles catégories créées.")
        print(f"📊 Total catégories: {Category.objects.count()}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des catégories: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        convert_brand_supplier_fields()
        create_categories()
        print("\n✅ Script terminé avec succès !")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)