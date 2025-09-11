#!/usr/bin/env python3
"""
Migration spécifique des grades avec gestion du mot réservé 'order'
"""
import sqlite3
import psycopg2
import json

def migrate_grades_table():
    """Migrer spécifiquement la table des grades"""
    print("🥋 Migration spécifique des grades")
    
    # Connexions
    sqlite_conn = sqlite3.connect('db.sqlite3')
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        pg_conn = psycopg2.connect(
            host='localhost',
            database='martialcomp_dev',
            user='postgres',
            password='password'
        )
        
        print("✅ Connexions établies")
        
        # Lire les grades de SQLite avec guillemets pour 'order'
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute('''
            SELECT id, name, name_fr, name_en, name_es, name_it, name_de, name_pt, 
                   name_no, name_ja, name_zh, name_hi, name_ar, name_sw, name_am, 
                   name_zu, name_yo, name_ko, color, color_fr, color_en, color_es, 
                   color_it, color_de, color_pt, color_no, color_ja, color_zh, 
                   color_hi, color_ar, color_sw, color_am, color_zu, color_yo, 
                   color_ko, discipline_id, category_id, "order", rank_value, 
                   created_at, updated_at
            FROM grades_grade
        ''')
        
        grades = sqlite_cursor.fetchall()
        print(f"📊 {len(grades)} grades trouvés dans SQLite")
        
        if len(grades) == 0:
            print("ℹ️  Aucun grade à migrer")
            return True
        
        # Afficher quelques exemples
        print("🔍 Exemples de grades trouvés:")
        for i, grade in enumerate(grades[:5]):
            print(f"  - {grade['name']} (couleur: {grade['color']}, ordre: {grade['order']})")
        
        # Migrer vers PostgreSQL
        pg_cursor = pg_conn.cursor()
        migrated_count = 0
        
        for grade in grades:
            try:
                # Utiliser des guillemets pour la colonne 'order'
                pg_cursor.execute('''
                    INSERT INTO grades_grade 
                    (id, name, name_fr, name_en, name_es, name_it, name_de, name_pt, 
                     name_no, name_ja, name_zh, name_hi, name_ar, name_sw, name_am, 
                     name_zu, name_yo, name_ko, color, color_fr, color_en, color_es, 
                     color_it, color_de, color_pt, color_no, color_ja, color_zh, 
                     color_hi, color_ar, color_sw, color_am, color_zu, color_yo, 
                     color_ko, discipline_id, category_id, "order", rank_value, 
                     created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                ''', (
                    grade['id'], grade['name'], grade['name_fr'], grade['name_en'], 
                    grade['name_es'], grade['name_it'], grade['name_de'], grade['name_pt'], 
                    grade['name_no'], grade['name_ja'], grade['name_zh'], grade['name_hi'], 
                    grade['name_ar'], grade['name_sw'], grade['name_am'], grade['name_zu'], 
                    grade['name_yo'], grade['name_ko'], grade['color'], grade['color_fr'], 
                    grade['color_en'], grade['color_es'], grade['color_it'], grade['color_de'], 
                    grade['color_pt'], grade['color_no'], grade['color_ja'], grade['color_zh'], 
                    grade['color_hi'], grade['color_ar'], grade['color_sw'], grade['color_am'], 
                    grade['color_zu'], grade['color_yo'], grade['color_ko'], grade['discipline_id'], 
                    grade['category_id'], grade['order'], grade['rank_value'], 
                    grade['created_at'], grade['updated_at']
                ))
                
                pg_conn.commit()
                print(f"  ✅ Grade {grade['name']} migré")
                migrated_count += 1
                
            except Exception as e:
                pg_conn.rollback()
                print(f"  ⚠️  Grade {grade['name']} ignoré: {e}")
        
        # Mettre à jour la séquence
        try:
            pg_cursor.execute("SELECT setval('grades_grade_id_seq', (SELECT MAX(id) FROM grades_grade));")
            pg_conn.commit()
        except Exception as e:
            print(f"⚠️  Erreur mise à jour séquence: {e}")
        
        print(f"📊 {migrated_count}/{len(grades)} grades migrés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur migration grades: {e}")
        return False
    finally:
        sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

def migrate_grade_categories():
    """Migrer les catégories de grades"""
    print("\n🏷️  Migration des catégories de grades")
    
    sqlite_conn = sqlite3.connect('db.sqlite3')
    sqlite_conn.row_factory = sqlite3.Row
    
    try:
        pg_conn = psycopg2.connect(
            host='localhost',
            database='martialcomp_dev',
            user='postgres',
            password='password'
        )
        
        # Lire les catégories avec guillemets pour 'order'
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute('''
            SELECT id, name, name_fr, name_en, name_es, name_it, name_de, name_pt, 
                   name_no, name_ja, name_zh, name_hi, name_ar, name_sw, name_am, 
                   name_zu, name_yo, name_ko, description, description_fr, 
                   description_en, description_es, description_it, description_de, 
                   description_pt, description_no, description_ja, description_zh, 
                   description_hi, description_ar, description_sw, description_am, 
                   description_zu, description_yo, description_ko, discipline_id, 
                   "order", created_at, updated_at
            FROM grades_gradecategory
        ''')
        
        categories = sqlite_cursor.fetchall()
        print(f"📊 {len(categories)} catégories trouvées")
        
        if len(categories) == 0:
            return True
        
        pg_cursor = pg_conn.cursor()
        migrated_count = 0
        
        for cat in categories:
            try:
                pg_cursor.execute('''
                    INSERT INTO grades_gradecategory 
                    (id, name, name_fr, name_en, name_es, name_it, name_de, name_pt, 
                     name_no, name_ja, name_zh, name_hi, name_ar, name_sw, name_am, 
                     name_zu, name_yo, name_ko, description, description_fr, 
                     description_en, description_es, description_it, description_de, 
                     description_pt, description_no, description_ja, description_zh, 
                     description_hi, description_ar, description_sw, description_am, 
                     description_zu, description_yo, description_ko, discipline_id, 
                     "order", created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                ''', (
                    cat['id'], cat['name'], cat['name_fr'], cat['name_en'], cat['name_es'], 
                    cat['name_it'], cat['name_de'], cat['name_pt'], cat['name_no'], 
                    cat['name_ja'], cat['name_zh'], cat['name_hi'], cat['name_ar'], 
                    cat['name_sw'], cat['name_am'], cat['name_zu'], cat['name_yo'], 
                    cat['name_ko'], cat['description'], cat['description_fr'], 
                    cat['description_en'], cat['description_es'], cat['description_it'], 
                    cat['description_de'], cat['description_pt'], cat['description_no'], 
                    cat['description_ja'], cat['description_zh'], cat['description_hi'], 
                    cat['description_ar'], cat['description_sw'], cat['description_am'], 
                    cat['description_zu'], cat['description_yo'], cat['description_ko'], 
                    cat['discipline_id'], cat['order'], cat['created_at'], cat['updated_at']
                ))
                
                pg_conn.commit()
                print(f"  ✅ Catégorie {cat['name']} migrée")
                migrated_count += 1
                
            except Exception as e:
                pg_conn.rollback()
                print(f"  ⚠️  Catégorie {cat['name']} ignorée: {e}")
        
        print(f"📊 {migrated_count}/{len(categories)} catégories migrées")
        return True
        
    except Exception as e:
        print(f"❌ Erreur catégories: {e}")
        return False
    finally:
        sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

def verify_grades_migration():
    """Vérifier que les grades ont été migrés"""
    print("\n🔍 Vérification des grades migrés")
    
    try:
        pg_conn = psycopg2.connect(
            host='localhost',
            database='martialcomp_dev',
            user='postgres',
            password='password'
        )
        
        cursor = pg_conn.cursor()
        
        # Compter les grades
        cursor.execute("SELECT COUNT(*) FROM grades_grade")
        grades_count = cursor.fetchone()[0]
        
        # Compter les catégories
        cursor.execute("SELECT COUNT(*) FROM grades_gradecategory")
        categories_count = cursor.fetchone()[0]
        
        print(f"📊 Résultat final:")
        print(f"  - {grades_count} grades")
        print(f"  - {categories_count} catégories de grades")
        
        # Exemples de grades par discipline
        cursor.execute('''
            SELECT g.name, g.color, d.name as discipline 
            FROM grades_grade g 
            JOIN competitions_discipline d ON g.discipline_id = d.id 
            ORDER BY g.discipline_id, g."order" 
            LIMIT 10
        ''')
        
        examples = cursor.fetchall()
        if examples:
            print(f"🥋 Exemples de grades:")
            for grade_name, color, discipline in examples:
                print(f"  - {discipline}: {grade_name} ({color})")
        
        pg_conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def main():
    """Migration complète des grades"""
    print("🚀 Migration spécifique des grades SQLite → PostgreSQL")
    
    import os
    if not os.path.exists('db.sqlite3'):
        print("❌ db.sqlite3 non trouvé")
        return False
    
    # Migrer les catégories d'abord (foreign key)
    if not migrate_grade_categories():
        print("❌ Échec migration catégories")
        return False
    
    # Puis les grades
    if not migrate_grades_table():
        print("❌ Échec migration grades")
        return False
    
    # Vérifier
    verify_grades_migration()
    
    print("\n🎉 Migration des grades terminée!")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)