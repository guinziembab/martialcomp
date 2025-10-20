#!/usr/bin/env python3
"""
Script de synchronisation des types de compétition de développement vers production
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

def get_competition_types_from_dev():
    """Récupère tous les types de compétition de développement"""
    try:
        conn = psycopg2.connect(**DEV_DB_CONFIG)
        cur = conn.cursor()
        
        query = """
        SELECT 
            ct.id,
            ct.name,
            ct.description,
            d.name as discipline_name,
            ct.team_based,
            ct.min_team_size,
            ct.max_team_size,
            ct.weight_category,
            ct.scoring_system,
            ct."order"
        FROM competitions_competitiontype ct
        JOIN competitions_discipline d ON ct.discipline_id = d.id
        ORDER BY d.name, ct."order", ct.name
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        competition_types = []
        for row in rows:
            competition_types.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'discipline_name': row[3],
                'team_based': row[4],
                'min_team_size': row[5],
                'max_team_size': row[6],
                'weight_category': row[7],
                'scoring_system': row[8],
                'order': row[9]
            })
        
        conn.close()
        return competition_types
        
    except Exception as e:
        print(f"Erreur lors de la récupération des types de développement: {e}")
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

def sync_competition_types():
    """Synchronise les types de compétition vers la production"""
    
    print("=== SYNCHRONISATION DES TYPES DE COMPÉTITION ===")
    print(f"Début: {datetime.now()}")
    
    # Récupérer les types de développement
    print("1. Récupération des types de développement...")
    dev_types = get_competition_types_from_dev()
    print(f"   {len(dev_types)} types trouvés en développement")
    
    if not dev_types:
        print("Aucun type trouvé en développement. Arrêt.")
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
        
        print("3. Synchronisation des types...")
        
        for type_data in dev_types:
            try:
                discipline_name = type_data['discipline_name']
                
                # Vérifier si la discipline existe en production
                if discipline_name not in prod_disciplines:
                    print(f"   ⚠️  Discipline '{discipline_name}' non trouvée en production - SKIP")
                    skipped_count += 1
                    continue
                
                discipline_id = prod_disciplines[discipline_name]
                
                # Vérifier si le type existe déjà
                cur.execute("""
                    SELECT id FROM competitions_competitiontype 
                    WHERE name = %s AND discipline_id = %s
                """, (type_data['name'], discipline_id))
                
                existing = cur.fetchone()
                
                if existing:
                    # Mettre à jour
                    cur.execute("""
                        UPDATE competitions_competitiontype SET
                            description = %s,
                            team_based = %s,
                            min_team_size = %s,
                            max_team_size = %s,
                            weight_category = %s,
                            scoring_system = %s,
                            "order" = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """, (
                        type_data['description'],
                        type_data['team_based'],
                        type_data['min_team_size'],
                        type_data['max_team_size'],
                        type_data['weight_category'],
                        type_data['scoring_system'],
                        type_data['order'],
                        existing[0]
                    ))
                    updated_count += 1
                    print(f"   ✓ Mis à jour: {type_data['name']} ({discipline_name})")
                else:
                    # Créer
                    cur.execute("""
                        INSERT INTO competitions_competitiontype (
                            name, description, discipline_id, team_based,
                            min_team_size, max_team_size, weight_category,
                            scoring_system, "order", created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                        )
                    """, (
                        type_data['name'],
                        type_data['description'],
                        discipline_id,
                        type_data['team_based'],
                        type_data['min_team_size'],
                        type_data['max_team_size'],
                        type_data['weight_category'],
                        type_data['scoring_system'],
                        type_data['order']
                    ))
                    created_count += 1
                    print(f"   + Créé: {type_data['name']} ({discipline_name})")
                
            except Exception as e:
                error_count += 1
                print(f"   ✗ Erreur pour {type_data['name']}: {e}")
        
        # Commit des changements
        conn.commit()
        conn.close()
        
        print("\n=== RÉSULTATS ===")
        print(f"Types créés: {created_count}")
        print(f"Types mis à jour: {updated_count}")
        print(f"Types ignorés: {skipped_count}")
        print(f"Erreurs: {error_count}")
        print(f"Total traité: {len(dev_types)}")
        print(f"Fin: {datetime.now()}")
        
    except Exception as e:
        print(f"Erreur lors de la synchronisation: {e}")

if __name__ == "__main__":
    sync_competition_types()