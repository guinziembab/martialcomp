#!/usr/bin/env python3
"""
Script simplifié pour insérer les catégories d'arts martiaux
directement dans la base de données SQLite.
"""

import sqlite3
import os
from datetime import datetime

# Structure des catégories basée sur martial_arts_shop_categories.md
categories_data = [
    # 1. TENUES & KIMONOS
    {
        'name': 'Tenues & Kimonos',
        'description': 'Tenues traditionnelles et modernes pour tous les arts martiaux',
        'order': 1,
        'children': [
            {'name': 'Kimonos Karaté', 'description': 'Kimonos spécialisés pour la pratique du karaté'},
            {'name': 'Kimonos Judo', 'description': 'Judogis traditionnels et de compétition'},
            {'name': 'Kimonos Jiu-Jitsu', 'description': 'Kimonos adaptés au Jiu-Jitsu brésilien et traditionnel'},
            {'name': 'Tenues Taekwondo', 'description': 'Doboks pour la pratique du Taekwondo'},
            {'name': 'Tenues Kung-Fu', 'description': 'Tenues traditionnelles chinoises'},
            {'name': 'Tenues Arts Martiaux Mixtes', 'description': 'Équipements pour MMA et sports de combat'},
        ]
    },
    # 2. GRADES & CEINTURES
    {
        'name': 'Grades & Ceintures',
        'description': 'Ceintures et systèmes de grades pour tous les arts martiaux',
        'order': 2,
        'children': [
            {'name': 'Ceintures de Karaté', 'description': 'Ceintures colorées selon la tradition'},
            {'name': 'Ceintures de Judo', 'description': 'Ceintures officielles de Judo'},
            {'name': 'Ceintures de Taekwondo', 'description': 'Ceintures selon les standards WTF/ITF'},
            {'name': 'Ceintures de Jiu-Jitsu', 'description': 'Ceintures brésiliennes authentiques'},
            {'name': 'Accessoires de Grade', 'description': 'Barrettes, broderies et personnalisations'},
        ]
    },
    # 3. PROTECTIONS & SÉCURITÉ
    {
        'name': 'Protections & Sécurité',
        'description': 'Équipements de protection pour l\'entraînement et la compétition',
        'order': 3,
        'children': [
            {'name': 'Protège-Tibias', 'description': 'Protection des jambes pour les combats'},
            {'name': 'Gants de Combat', 'description': 'Gants pour boxe, MMA et arts martiaux'},
            {'name': 'Casques de Protection', 'description': 'Casques pour sparring et compétition'},
            {'name': 'Protections Corporelles', 'description': 'Plastrons, coquilles et protections diverses'},
            {'name': 'Protège-Dents', 'description': 'Protection dentaire personnalisée'},
        ]
    },
    # 4. MATÉRIEL D'ENTRAÎNEMENT
    {
        'name': 'Matériel d\'Entraînement',
        'description': 'Équipements pour l\'entraînement technique et physique',
        'order': 4,
        'children': [
            {'name': 'Sacs de Frappe', 'description': 'Sacs lourds et légers pour l\'entraînement'},
            {'name': 'Pattes d\'Ours', 'description': 'Paos et mitaines d\'entraînement'},
            {'name': 'Makiwaras', 'description': 'Planches de frappe traditionnelles'},
            {'name': 'Mannequins d\'Entraînement', 'description': 'Dummy et partenaires d\'entraînement'},
            {'name': 'Accessoires de Forme', 'description': 'Nunchakus, bâtons et armes traditionnelles'},
        ]
    },
    # 5. ÉQUIPEMENT DOJO/CLUB
    {
        'name': 'Équipement Dojo/Club',
        'description': 'Matériel pour l\'équipement des dojos et clubs',
        'order': 5,
        'children': [
            {'name': 'Tatamis', 'description': 'Tapis de sol et revêtements'},
            {'name': 'Miroirs de Dojo', 'description': 'Miroirs de sécurité pour entraînement'},
            {'name': 'Matériel de Rangement', 'description': 'Vestiaires, casiers et organisation'},
            {'name': 'Signalétique', 'description': 'Panneaux, règlements et décoration'},
        ]
    },
    # 6. LIVRES & MÉDIAS
    {
        'name': 'Livres & Médias',
        'description': 'Documentation technique et pédagogique',
        'order': 6,
        'children': [
            {'name': 'Livres Techniques', 'description': 'Manuels et guides d\'entraînement'},
            {'name': 'DVDs d\'Entraînement', 'description': 'Supports vidéo pédagogiques'},
            {'name': 'Histoire des Arts Martiaux', 'description': 'Ouvrages historiques et philosophiques'},
        ]
    },
    # 7. TROPHÉES & RÉCOMPENSES
    {
        'name': 'Trophées & Récompenses',
        'description': 'Récompenses et prix pour compétitions',
        'order': 7,
        'children': [
            {'name': 'Trophées', 'description': 'Coupes et trophées personnalisables'},
            {'name': 'Médailles', 'description': 'Médailles de compétition'},
            {'name': 'Diplômes & Certificats', 'description': 'Reconnaissance officielle'},
        ]
    },
    # 8. ACCESSOIRES & LIFESTYLE
    {
        'name': 'Accessoires & Lifestyle',
        'description': 'Accessoires du quotidien pour pratiquants',
        'order': 8,
        'children': [
            {'name': 'Sacs de Sport', 'description': 'Transport d\'équipement'},
            {'name': 'Vêtements Casual', 'description': 'T-shirts, sweats et casual wear'},
            {'name': 'Accessoires Déco', 'description': 'Objets décoratifs et cadeaux'},
        ]
    },
    # 9. SANTÉ & RÉCUPÉRATION
    {
        'name': 'Santé & Récupération',
        'description': 'Produits pour la récupération et la santé',
        'order': 9,
        'children': [
            {'name': 'Soins Corporels', 'description': 'Baumes, huiles et soins'},
            {'name': 'Compléments Nutritionnels', 'description': 'Nutrition sportive'},
            {'name': 'Matériel de Récupération', 'description': 'Rouleaux, balles de massage'},
        ]
    },
    # 10. PERSONNALISATION & SERVICES
    {
        'name': 'Personnalisation & Services',
        'description': 'Services de personnalisation et broderie',
        'order': 10,
        'children': [
            {'name': 'Broderie', 'description': 'Personnalisation textile'},
            {'name': 'Impression', 'description': 'Impression sur textile et objets'},
            {'name': 'Gravure', 'description': 'Gravure sur métaux et matériaux durs'},
        ]
    },
]

def slugify(text):
    """Créer un slug à partir d'un texte"""
    import re
    # Remplacer les caractères spéciaux
    text = text.lower()
    text = re.sub(r'[àáâãäå]', 'a', text)
    text = re.sub(r'[èéêë]', 'e', text)
    text = re.sub(r'[ìíîï]', 'i', text)
    text = re.sub(r'[òóôõö]', 'o', text)
    text = re.sub(r'[ùúûü]', 'u', text)
    text = re.sub(r'[ýÿ]', 'y', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text

def populate_categories():
    """Insérer les catégories dans la base de données"""
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} non trouvée")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si les catégories existent déjà
        cursor.execute("SELECT COUNT(*) FROM shop_category")
        existing_count = cursor.fetchone()[0]
        
        if existing_count > 0:
            print(f"✓ {existing_count} catégories déjà existantes")
            response = input("Voulez-vous les supprimer et recommencer? (y/N): ")
            if response.lower() == 'y':
                cursor.execute("DELETE FROM shop_category_disciplines")
                cursor.execute("DELETE FROM shop_category")
                print("✓ Catégories supprimées")
            else:
                print("✓ Conservation des catégories existantes")
                conn.close()
                return True
        
        # Insérer les catégories principales
        for cat_data in categories_data:
            slug = slugify(cat_data['name'])
            cursor.execute("""
                INSERT INTO shop_category 
                (name, slug, description, parent_id, order_index, is_active, created_at, updated_at)
                VALUES (?, ?, ?, NULL, ?, 1, ?, ?)
            """, (
                cat_data['name'],
                slug,
                cat_data['description'],
                cat_data['order'],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            parent_id = cursor.lastrowid
            print(f"✓ Catégorie créée: {cat_data['name']} (ID: {parent_id})")
            
            # Insérer les sous-catégories
            for i, child in enumerate(cat_data['children'], 1):
                child_slug = slugify(child['name'])
                cursor.execute("""
                    INSERT INTO shop_category 
                    (name, slug, description, parent_id, order_index, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                """, (
                    child['name'],
                    child_slug,
                    child['description'],
                    parent_id,
                    i,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                child_id = cursor.lastrowid
                print(f"  ✓ Sous-catégorie: {child['name']} (ID: {child_id})")
        
        conn.commit()
        conn.close()
        
        # Afficher le résumé
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM shop_category WHERE parent_id IS NULL")
        main_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shop_category WHERE parent_id IS NOT NULL")
        sub_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shop_category")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        print("\n" + "="*50)
        print("🎯 CATÉGORIES D'ARTS MARTIAUX CRÉÉES AVEC SUCCÈS!")
        print("="*50)
        print(f"📊 Catégories principales: {main_count}")
        print(f"📋 Sous-catégories: {sub_count}")
        print(f"🔢 Total: {total_count} catégories")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'insertion: {e}")
        return False

if __name__ == '__main__':
    print("🥋 MISE EN PLACE DES CATÉGORIES D'ARTS MARTIAUX")
    print("=" * 50)
    success = populate_categories()
    
    if success:
        print("\n✅ Les catégories ont été créées avec succès!")
        print("📱 Vous pouvez maintenant utiliser le formulaire de création de produits")
        print("🌐 URL: http://127.0.0.1:8000/shop/dashboard/club/product/create/")
    else:
        print("\n❌ Échec de la création des catégories")