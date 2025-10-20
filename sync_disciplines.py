#!/usr/bin/env python3
"""
Script de synchronisation des disciplines de développement vers production
"""

import psycopg2
import json
import sys
from datetime import datetime

# Configuration de développement
DEV_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'martialcomp_dev',
    'user': 'postgres',
    'password': 'postgres'
}

# Configuration de production
PROD_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'martialcomp_db',
    'user': 'martialcomp_user',
    'password': 'AQWZSX123ok,'
}

def get_disciplines_from_dev():
    """Récupère toutes les disciplines de développement"""
    try:
        conn = psycopg2.connect(**DEV_DB_CONFIG)
        cur = conn.cursor()
        
        query = """
        SELECT 
            id,
            name,
            description,
            created_at,
            updated_at
        FROM competitions_discipline
        ORDER BY name
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        disciplines = []
        for row in rows:
            disciplines.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3],
                'updated_at': row[4]
            })
        
        conn.close()
        return disciplines
        
    except Exception as e:
        print(f"Erreur lors de la récupération des disciplines de développement: {e}")
        return []

def get_disciplines_from_prod():
    """Récupère les disciplines de production"""
    try:
        conn = psycopg2.connect(**PROD_DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT id, name FROM competitions_discipline")
        rows = cur.fetchall()
        
        disciplines = {row[1]: row[0] for row in rows}
        conn.close()
        return disciplines
        
    except Exception as e:
        print(f"Erreur lors de la récupération des disciplines de production: {e}")
        return {}

def sync_disciplines():
    """Synchronise les disciplines vers la production"""
    
    print("=== SYNCHRONISATION DES DISCIPLINES ===")
    print(f"Début: {datetime.now()}")
    
    # Récupérer les disciplines de développement
    print("1. Récupération des disciplines de développement...")
    dev_disciplines = get_disciplines_from_dev()
    print(f"   {len(dev_disciplines)} disciplines trouvées en développement")
    
    if not dev_disciplines:
        print("Aucune discipline trouvée en développement. Arrêt.")
        return
    
    # Récupérer les disciplines de production
    print("2. Récupération des disciplines de production...")
    prod_disciplines = get_disciplines_from_prod()
    print(f"   {len(prod_disciplines)} disciplines trouvées en production")
    
    # Connexion à la production
    try:
        conn = psycopg2.connect(**PROD_DB_CONFIG)
        cur = conn.cursor()
        
        # Statistiques
        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        print("3. Synchronisation des disciplines...")
        
        for discipline_data in dev_disciplines:
            try:
                discipline_name = discipline_data['name']
                
                # Vérifier si la discipline existe déjà en production
                if discipline_name in prod_disciplines:
                    print(f"   - Existant: {discipline_name}")
                    skipped_count += 1
                    continue
                
                # Créer la discipline
                cur.execute("""
                    INSERT INTO competitions_discipline (
                        name, description, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s
                    )
                """, (
                    discipline_data['name'],
                    discipline_data['description'],
                    discipline_data['created_at'],
                    discipline_data['updated_at']
                ))
                created_count += 1
                print(f"   + Créé: {discipline_name}")
                
            except Exception as e:
                error_count += 1
                print(f"   ✗ Erreur pour {discipline_data['name']}: {e}")
        
        # Commit des changements
        conn.commit()
        conn.close()
        
        print("\n=== RÉSULTATS ===")
        print(f"Disciplines créées: {created_count}")
        print(f"Disciplines mises à jour: {updated_count}")
        print(f"Disciplines ignorées: {skipped_count}")
        print(f"Erreurs: {error_count}")
        print(f"Total traité: {len(dev_disciplines)}")
        print(f"Fin: {datetime.now()}")
        
    except Exception as e:
        print(f"Erreur lors de la synchronisation: {e}")

if __name__ == "__main__":
    sync_disciplines()