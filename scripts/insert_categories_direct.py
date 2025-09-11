#!/usr/bin/env python3
"""
Script pour insérer directement les catégories d'arts martiaux en SQL
"""

import sqlite3
import re
from datetime import datetime

def slugify(text):
    """Créer un slug à partir d'un texte"""
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

# Structure des catégories d'arts martiaux
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

def insert_categories():
    """Insérer les catégories dans la base de données SQLite"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Vider les tables
        cursor.execute("DELETE FROM shop_category_disciplines")
        cursor.execute("DELETE FROM shop_category")
        
        now = datetime.now().isoformat()
        total_created = 0
        
        # Insérer les catégories principales et leurs enfants
        for cat_data in categories_data:
            # Insérer la catégorie principale
            main_slug = slugify(cat_data['name'])
            cursor.execute("""
                INSERT INTO shop_category 
                (name, slug, description, parent_id, order_index, is_active, meta_title, meta_description, created_at, updated_at)
                VALUES (?, ?, ?, NULL, ?, 1, ?, ?, ?, ?)
            """, (
                cat_data['name'],
                main_slug,
                cat_data['description'],
                cat_data['order'],
                cat_data['name'],  # meta_title
                cat_data['description'][:160],  # meta_description tronquée
                now,
                now
            ))
            
            parent_id = cursor.lastrowid
            print(f"✅ {cat_data['name']} (ID: {parent_id})")
            total_created += 1
            
            # Insérer les sous-catégories
            for i, child in enumerate(cat_data['children'], 1):
                child_slug = slugify(child['name'])
                cursor.execute("""
                    INSERT INTO shop_category 
                    (name, slug, description, parent_id, order_index, is_active, meta_title, meta_description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
                """, (
                    child['name'],
                    child_slug,
                    child['description'],
                    parent_id,
                    i,
                    child['name'],  # meta_title
                    child['description'][:160],  # meta_description tronquée
                    now,
                    now
                ))
                
                child_id = cursor.lastrowid
                print(f"  ↳ {child['name']} (ID: {child_id})")
                total_created += 1
        
        conn.commit()
        
        # Statistiques
        cursor.execute("SELECT COUNT(*) FROM shop_category WHERE parent_id IS NULL")
        main_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shop_category WHERE parent_id IS NOT NULL")
        sub_count = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("🎯 CATÉGORIES D'ARTS MARTIAUX CRÉÉES AVEC SUCCÈS!")
        print("="*60)
        print(f"📊 Catégories principales: {main_count}")
        print(f"📋 Sous-catégories: {sub_count}")
        print(f"🔢 Total créé: {total_created}")
        print("\n🔗 URLs pour tester:")
        print("  📱 Admin: http://127.0.0.1:8000/admin/shop/category/")
        print("  🛍️  Boutique: http://127.0.0.1:8000/shop/dashboard/club/product/create/")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    print("🥋 INSERTION DIRECTE DES CATÉGORIES D'ARTS MARTIAUX")
    print("=" * 60)
    
    success = insert_categories()
    
    if success:
        print("\n✅ TERMINÉ! Les catégories sont maintenant disponibles.")
    else:
        print("\n❌ ÉCHEC de l'insertion des catégories.")