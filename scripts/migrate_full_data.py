#!/usr/bin/env python3
"""
Migration complète des données SQLite vers PostgreSQL
"""
import sqlite3
import psycopg2
import json
from datetime import datetime

def migrate_table_data(table_name, sqlite_conn, pg_conn, exclude_cols=None):
    """Migrer une table complète avec gestion des types"""
    exclude_cols = exclude_cols or []
    
    print(f"🔄 Migration table: {table_name}")
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Obtenir la structure de la table
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = sqlite_cursor.fetchall()
        
        if not columns_info:
            print(f"  ⚠️  Table {table_name} n'existe pas dans SQLite")
            return True
        
        # Construire la liste des colonnes
        columns = []
        boolean_cols = []
        for col_info in columns_info:
            col_name = col_info[1]
            col_type = col_info[2].upper()
            
            if col_name not in exclude_cols:
                columns.append(col_name)
                if 'BOOL' in col_type or col_name.startswith('is_') or col_name.startswith('has_'):
                    boolean_cols.append(col_name)
        
        if not columns:
            print(f"  ⚠️  Aucune colonne à migrer pour {table_name}")
            return True
        
        # Lire les données SQLite
        columns_str = ', '.join(columns)
        sqlite_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        print(f"  📊 {len(rows)} lignes trouvées")
        
        if len(rows) == 0:
            return True
        
        # Insérer dans PostgreSQL
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """
        
        migrated_count = 0
        for row in rows:
            try:
                # Convertir les booléens
                converted_row = []
                for i, value in enumerate(row):
                    col_name = columns[i]
                    if col_name in boolean_cols and value is not None:
                        converted_row.append(bool(value))
                    else:
                        converted_row.append(value)
                
                pg_cursor.execute(insert_query, converted_row)
                pg_conn.commit()
                migrated_count += 1
                
            except Exception as e:
                pg_conn.rollback()
                print(f"    ⚠️  Ligne ignorée: {e}")
        
        print(f"  ✅ {migrated_count}/{len(rows)} lignes migrées")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur table {table_name}: {e}")
        return False

def get_table_list(sqlite_conn):
    """Obtenir la liste des tables à migrer (hors tables système)"""
    cursor = sqlite_conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        AND name NOT LIKE 'django_%'
        AND name != 'auth_user'
        ORDER BY name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def migrate_all_data():
    """Migration complète des données"""
    print("🚀 Migration complète SQLite → PostgreSQL")
    
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
        
        # Obtenir la liste des tables
        tables = get_table_list(sqlite_conn)
        print(f"📋 {len(tables)} tables à migrer:")
        for table in tables:
            print(f"  - {table}")
        
        # Migrer chaque table
        success_count = 0
        for table in tables:
            if migrate_table_data(table, sqlite_conn, pg_conn):
                success_count += 1
            print()  # Ligne vide pour lisibilité
        
        print(f"🎯 Résultat: {success_count}/{len(tables)} tables migrées")
        
        # Vérifications spécifiques
        check_important_data(pg_conn)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        return False
    finally:
        sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

def check_important_data(pg_conn):
    """Vérifier les données importantes migrées"""
    print("🔍 Vérification des données importantes:")
    
    checks = [
        ("Disciplines", "competitions_discipline"),
        ("Grades", "grades_grade"),
        ("Organisations", "organizations_organization"),
        ("Clubs", "competitions_club"),
        ("Compétitions", "competitions_competition"),
        ("Sites", "django_site"),
    ]
    
    cursor = pg_conn.cursor()
    
    for name, table in checks:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  📊 {name}: {count} entrées")
            
            if table == "competitions_discipline" and count > 0:
                cursor.execute(f"SELECT name FROM {table} LIMIT 5")
                disciplines = [row[0] for row in cursor.fetchall()]
                print(f"    🥋 Exemples: {', '.join(disciplines)}")
                
        except Exception as e:
            print(f"  ⚠️  {name}: Table non trouvée ou erreur")

def main():
    """Point d'entrée principal"""
    import os
    if not os.path.exists('db.sqlite3'):
        print("❌ Fichier db.sqlite3 non trouvé")
        return False
    
    success = migrate_all_data()
    
    if success:
        print("\n🎉 Migration complète terminée!")
        print("💡 Toutes vos données sont maintenant disponibles dans PostgreSQL")
    else:
        print("\n❌ Migration incomplète")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)