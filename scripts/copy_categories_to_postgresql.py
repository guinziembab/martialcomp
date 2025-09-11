#!/usr/bin/env python3
"""
Script pour copier les catégories de SQLite vers PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# Configuration PostgreSQL (ajustez selon vos paramètres)
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'martialcomp',
    'user': 'postgres',
    'password': 'password'  # Ajustez selon votre configuration
}

def get_sqlite_categories():
    """Récupérer les catégories depuis SQLite"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row  # Pour obtenir des dictionnaires
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, slug, description, parent_id, is_active, 
                   meta_title, meta_description, image, "order", 
                   created_at, updated_at
            FROM shop_category 
            ORDER BY "order", id
        """)
        
        categories = [dict(row) for row in cursor.fetchall()]
        return categories
        
    finally:
        conn.close()

def create_postgresql_tables():
    """Créer les tables PostgreSQL si elles n'existent pas"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Créer la table shop_category
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop_category (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(120) NOT NULL UNIQUE,
                description TEXT,
                parent_id INTEGER REFERENCES shop_category(id),
                is_active BOOLEAN DEFAULT true,
                meta_title VARCHAR(150),
                meta_description TEXT,
                image VARCHAR(100),
                "order" INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Créer la table shop_category_disciplines
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop_category_disciplines (
                id SERIAL PRIMARY KEY,
                category_id INTEGER NOT NULL REFERENCES shop_category(id),
                discipline_id INTEGER NOT NULL,
                UNIQUE(category_id, discipline_id)
            );
        """)
        
        conn.commit()
        print("✅ Tables PostgreSQL créées")
        
    except Exception as e:
        print(f"❌ Erreur création tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def insert_categories_postgresql(categories):
    """Insérer les catégories dans PostgreSQL"""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    cursor = conn.cursor()
    
    try:
        # Vider les tables existantes
        cursor.execute("DELETE FROM shop_category_disciplines")
        cursor.execute("DELETE FROM shop_category")
        
        # Mapping des anciens IDs vers les nouveaux
        id_mapping = {}
        
        # Insérer d'abord les catégories parentes (parent_id = NULL)
        parents = [cat for cat in categories if cat['parent_id'] is None]
        for cat in parents:
            cursor.execute("""
                INSERT INTO shop_category 
                (name, slug, description, parent_id, is_active, meta_title, meta_description, image, "order", created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                cat['name'],
                cat['slug'],
                cat['description'],
                None,
                cat['is_active'],
                cat['meta_title'],
                cat['meta_description'],
                cat['image'],
                cat['order'],
                cat['created_at'],
                cat['updated_at']
            ))
            
            new_id = cursor.fetchone()[0]
            id_mapping[cat['id']] = new_id
            print(f"✅ Parent: {cat['name']} (ID: {cat['id']} -> {new_id})")
        
        # Insérer ensuite les sous-catégories
        children = [cat for cat in categories if cat['parent_id'] is not None]
        for cat in children:
            new_parent_id = id_mapping.get(cat['parent_id'])
            if new_parent_id is None:
                print(f"⚠️  Parent non trouvé pour {cat['name']}")
                continue
                
            cursor.execute("""
                INSERT INTO shop_category 
                (name, slug, description, parent_id, is_active, meta_title, meta_description, image, "order", created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                cat['name'],
                cat['slug'],
                cat['description'],
                new_parent_id,
                cat['is_active'],
                cat['meta_title'],
                cat['meta_description'],
                cat['image'],
                cat['order'],
                cat['created_at'],
                cat['updated_at']
            ))
            
            new_id = cursor.fetchone()[0]
            id_mapping[cat['id']] = new_id
            print(f"  ↳ {cat['name']} (ID: {cat['id']} -> {new_id})")
        
        conn.commit()
        
        # Statistiques
        cursor.execute("SELECT COUNT(*) FROM shop_category WHERE parent_id IS NULL")
        main_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shop_category WHERE parent_id IS NOT NULL")
        sub_count = cursor.fetchone()[0]
        
        print(f"\n📊 Catégories principales: {main_count}")
        print(f"📋 Sous-catégories: {sub_count}")
        print(f"🔢 Total: {main_count + sub_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur insertion: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def copy_categories():
    """Fonction principale de copie"""
    print("🔄 COPIE DES CATÉGORIES SQLite -> PostgreSQL")
    print("=" * 50)
    
    # Vérifier la connexion PostgreSQL
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        conn.close()
        print("✅ Connexion PostgreSQL réussie")
    except Exception as e:
        print(f"❌ Erreur connexion PostgreSQL: {e}")
        print("Veuillez vérifier que PostgreSQL est démarré et configuré")
        return False
    
    # Récupérer les catégories depuis SQLite
    print("📖 Lecture des catégories depuis SQLite...")
    categories = get_sqlite_categories()
    print(f"✅ {len(categories)} catégories trouvées")
    
    # Créer les tables PostgreSQL
    if not create_postgresql_tables():
        return False
    
    # Insérer les catégories
    print("📝 Insertion dans PostgreSQL...")
    if insert_categories_postgresql(categories):
        print("\n✅ COPIE TERMINÉE AVEC SUCCÈS!")
        print("🔗 Les catégories sont maintenant disponibles dans PostgreSQL")
        return True
    else:
        print("\n❌ ÉCHEC de la copie")
        return False

if __name__ == '__main__':
    success = copy_categories()
    
    if success:
        print("\n🎯 INSTRUCTIONS:")
        print("1. Redémarrez votre serveur Django avec les paramètres PostgreSQL")
        print("2. Vérifiez l'admin: http://127.0.0.1:8000/admin/shop/category/")
        print("3. Testez la boutique: http://127.0.0.1:8000/shop/dashboard/club/product/create/")
    else:
        print("\n💡 ALTERNATIVES:")
        print("1. Utilisez SQLite temporairement avec --settings=config.settings_minimal")
        print("2. Configurez PostgreSQL et relancez ce script")
        print("3. Utilisez la commande Django: python manage.py create_martial_arts_categories")