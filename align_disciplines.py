#!/usr/bin/env python3
"""
Script d'alignement des disciplines Qwan Ki Do et Long Phai
"""

import psycopg2
import json
import sys
from datetime import datetime

# Configuration de production
PROD_DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'martialcomp_db',
    'user': 'martialcomp_user',
    'password': 'AQWZSX123ok,'
}

def get_qwan_ki_do_competition_types():
    """Récupère les types de compétition de Qwan Ki Do en production"""
    try:
        conn = psycopg2.connect(**PROD_DB_CONFIG)
        cur = conn.cursor()
        
        query = """
        SELECT 
            ct.id,
            ct.name,
            ct.description,
            ct.team_based,
            ct.min_team_size,
            ct.max_team_size,
            ct.weight_category,
            ct.scoring_system,
            ct."order"
        FROM competitions_competitiontype ct
        JOIN competitions_discipline d ON ct.discipline_id = d.id
        WHERE d.name = 'Qwan Ki Do'
        ORDER BY ct."order", ct.name
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        competition_types = []
        for row in rows:
            competition_types.append({
                'id': row[0],
                'name': row[1],
                'description': row[2],
                'team_based': row[3],
                'min_team_size': row[4],
                'max_team_size': row[5],
                'weight_category': row[6],
                'scoring_system': row[7],
                'order': row[8]
            })
        
        conn.close()
        return competition_types
        
    except Exception as e:
        print(f"Erreur lors de la récupération des types de Qwan Ki Do: {e}")
        return []

def get_long_phai_discipline_id():
    """Récupère l'ID de la discipline Long Phai"""
    try:
        conn = psycopg2.connect(**PROD_DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM competitions_discipline WHERE name = 'Long Phai' LIMIT 1")
        result = cur.fetchone()
        
        conn.close()
        return result[0] if result else None
        
    except Exception as e:
        print(f"Erreur lors de la récupération de Long Phai: {e}")
        return None

def align_long_phai_competition_types():
    """Aligne les types de compétition de Long Phai sur Qwan Ki Do"""
    
    print("=== ALIGNEMENT DES TYPES DE COMPÉTITION ===")
    print(f"Début: {datetime.now()}")
    
    # Récupérer les types de Qwan Ki Do
    print("1. Récupération des types de Qwan Ki Do...")
    qwan_types = get_qwan_ki_do_competition_types()
    print(f"   {len(qwan_types)} types trouvés pour Qwan Ki Do")
    
    if not qwan_types:
        print("Aucun type trouvé pour Qwan Ki Do. Arrêt.")
        return
    
    # Récupérer l'ID de Long Phai
    print("2. Récupération de l'ID de Long Phai...")
    long_phai_id = get_long_phai_discipline_id()
    if not long_phai_id:
        print("Discipline Long Phai non trouvée. Arrêt.")
        return
    print(f"   Long Phai ID: {long_phai_id}")
    
    # Connexion à la production
    try:
        conn = psycopg2.connect(**PROD_DB_CONFIG)
        cur = conn.cursor()
        
        # Supprimer les types existants de Long Phai
        print("3. Suppression des types existants de Long Phai...")
        cur.execute("DELETE FROM competitions_competitiontype WHERE discipline_id = %s", (long_phai_id,))
        deleted_count = cur.rowcount
        print(f"   {deleted_count} types supprimés")
        
        # Statistiques
        created_count = 0
        error_count = 0
        
        print("4. Création des nouveaux types pour Long Phai...")
        
        for type_data in qwan_types:
            try:
                # Adapter le nom pour Long Phai
                adapted_name = type_data['name']
                if 'Quyen' in adapted_name:
                    adapted_name = adapted_name.replace('Quyen', 'Formes')
                if 'Combat' in adapted_name:
                    adapted_name = adapted_name.replace('Combat', 'Sparring')
                
                # Créer le type pour Long Phai
                cur.execute("""
                    INSERT INTO competitions_competitiontype (
                        name, description, discipline_id, team_based,
                        min_team_size, max_team_size, weight_category,
                        scoring_system, "order", created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                """, (
                    adapted_name,
                    type_data['description'].replace('Qwan Ki Do', 'Long Phai'),
                    long_phai_id,
                    type_data['team_based'],
                    type_data['min_team_size'],
                    type_data['max_team_size'],
                    type_data['weight_category'],
                    type_data['scoring_system'],
                    type_data['order']
                ))
                created_count += 1
                print(f"   + Créé: {adapted_name}")
                
            except Exception as e:
                error_count += 1
                print(f"   ✗ Erreur pour {type_data['name']}: {e}")
        
        # Commit des changements
        conn.commit()
        conn.close()
        
        print("\n=== RÉSULTATS ===")
        print(f"Types supprimés: {deleted_count}")
        print(f"Types créés: {created_count}")
        print(f"Erreurs: {error_count}")
        print(f"Total traité: {len(qwan_types)}")
        print(f"Fin: {datetime.now()}")
        
    except Exception as e:
        print(f"Erreur lors de l'alignement: {e}")

def create_common_grades_system():
    """Crée un système de grades commun pour les deux disciplines"""
    
    print("\n=== CRÉATION DU SYSTÈME DE GRADES COMMUN ===")
    print(f"Début: {datetime.now()}")
    
    # Système de grades commun (basé sur les arts martiaux vietnamiens)
    common_grades = [
        {"level": 1, "name": "Blanc", "color": "Blanc", "color_code": "#FFFFFF", "is_dan_grade": False, "min_age": 6, "order": 1},
        {"level": 2, "name": "Jaune", "color": "Jaune", "color_code": "#FFFF00", "is_dan_grade": False, "min_age": 7, "order": 2},
        {"level": 3, "name": "Orange", "color": "Orange", "color_code": "#FFA500", "is_dan_grade": False, "min_age": 8, "order": 3},
        {"level": 4, "name": "Vert", "color": "Vert", "color_code": "#008000", "is_dan_grade": False, "min_age": 9, "order": 4},
        {"level": 5, "name": "Bleu", "color": "Bleu", "color_code": "#0000FF", "is_dan_grade": False, "min_age": 10, "order": 5},
        {"level": 6, "name": "Marron", "color": "Marron", "color_code": "#8B4513", "is_dan_grade": False, "min_age": 12, "order": 6},
        {"level": 7, "name": "Noir 1er Dan", "color": "Noir", "color_code": "#000000", "is_dan_grade": True, "min_age": 16, "order": 7},
        {"level": 8, "name": "Noir 2ème Dan", "color": "Noir", "color_code": "#000000", "is_dan_grade": True, "min_age": 18, "order": 8},
        {"level": 9, "name": "Noir 3ème Dan", "color": "Noir", "color_code": "#000000", "is_dan_grade": True, "min_age": 21, "order": 9},
        {"level": 10, "name": "Noir 4ème Dan", "color": "Noir", "color_code": "#000000", "is_dan_grade": True, "min_age": 25, "order": 10},
    ]
    
    try:
        conn = psycopg2.connect(**PROD_DB_CONFIG)
        cur = conn.cursor()
        
        # Récupérer les IDs des disciplines
        cur.execute("SELECT id, name FROM competitions_discipline WHERE name IN ('Qwan Ki Do', 'Long Phai')")
        disciplines = {row[1]: row[0] for row in cur.fetchall()}
        
        if 'Qwan Ki Do' not in disciplines or 'Long Phai' not in disciplines:
            print("Disciplines Qwan Ki Do ou Long Phai non trouvées")
            return
        
        # Statistiques
        created_count = 0
        error_count = 0
        
        print("Création des grades pour les deux disciplines...")
        
        for discipline_name, discipline_id in disciplines.items():
            print(f"\nCréation des grades pour {discipline_name} (ID: {discipline_id})...")
            
            for grade_data in common_grades:
                try:
                    cur.execute("""
                        INSERT INTO grades_grade (
                            name, discipline_id, color, color_code, level,
                            min_age, is_dan_grade, order_field, is_active,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                        )
                    """, (
                        grade_data['name'],
                        discipline_id,
                        grade_data['color'],
                        grade_data['color_code'],
                        grade_data['level'],
                        grade_data['min_age'],
                        grade_data['is_dan_grade'],
                        grade_data['order'],
                        True
                    ))
                    created_count += 1
                    print(f"   + Créé: {grade_data['name']} (Niveau {grade_data['level']})")
                    
                except Exception as e:
                    error_count += 1
                    print(f"   ✗ Erreur pour {grade_data['name']} ({discipline_name}): {e}")
        
        # Commit des changements
        conn.commit()
        conn.close()
        
        print(f"\n=== RÉSULTATS GRADES ===")
        print(f"Grades créés: {created_count}")
        print(f"Erreurs: {error_count}")
        print(f"Fin: {datetime.now()}")
        
    except Exception as e:
        print(f"Erreur lors de la création des grades: {e}")

if __name__ == "__main__":
    # Aligner les types de compétition
    align_long_phai_competition_types()
    
    # Créer le système de grades commun
    create_common_grades_system()