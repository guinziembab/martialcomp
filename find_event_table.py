#!/usr/bin/env python
"""
Script pour trouver la table Event dans la base de données
"""

import sqlite3
import os

def find_event_table():
    """Chercher la table Event ou des tables similaires"""
    
    db_path = 'db.sqlite3'
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données {db_path} non trouvée")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Lister toutes les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        # Chercher des variations de la table Event
        possible_event_tables = []
        for table in table_names:
            if 'event' in table.lower():
                possible_event_tables.append(table)
        
        print(f"🎯 Tables contenant 'event' : {possible_event_tables}")
        
        # Chercher des tables avec des noms proches
        similar_tables = []
        for table in table_names:
            if any(word in table.lower() for word in ['competition', 'match', 'tournament', 'planning']):
                similar_tables.append(table)
        
        print(f"🎯 Tables similaires : {similar_tables}")
        
        # Vérifier la table django_migrations pour voir quelles migrations Event ont été appliquées
        cursor.execute("""
            SELECT name FROM django_migrations 
            WHERE app = 'competitions' AND name LIKE '%event%'
        """)
        event_migrations = cursor.fetchall()
        print(f"🎯 Migrations Event appliquées : {[m[0] for m in event_migrations]}")
        
        # Vérifier si la table Event existe dans django_content_type
        cursor.execute("""
            SELECT model FROM django_content_type 
            WHERE app_label = 'competitions' AND model LIKE '%event%'
        """)
        event_models = cursor.fetchall()
        print(f"🎯 Modèles Event dans django_content_type : {[m[0] for m in event_models]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche : {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🔍 Recherche de la table Event...")
    find_event_table()