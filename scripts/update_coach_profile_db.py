#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour mettre à jour la table coach_profile avec les champs du modèle actuel
"""
import psycopg2
import sys

print("Script pour mettre à jour la table CoachProfile dans la base de données")

# Paramètres de connexion à la base de données
DB_NAME = "martialcomp"
DB_USER = "postgres"
DB_PASSWORD = "postgres"  # Remplacer par votre mot de passe si différent
DB_HOST = "localhost"
DB_PORT = "5432"

try:
    print(f"Tentative de connexion à PostgreSQL ({DB_HOST}:{DB_PORT})...")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    print("Connexion à la base de données réussie")
    
    # Lister tous les champs du modèle dans la base de données
    print("\n=== Colonnes actuelles dans competitions_coachprofile ===")
    
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'competitions_coachprofile'
        ORDER BY ordinal_position;
    """)
    
    existing_columns = {col[0]: (col[1], col[2]) for col in cur.fetchall()}
    
    for col_name, (data_type, nullable) in existing_columns.items():
        print(f"- {col_name} ({data_type}), Nullable: {nullable}")
    
    # Vérifier et ajouter les colonnes manquantes
    required_columns = {
        'profile_type': ('varchar(20)', 'DEFAULT \'traditional\'', 'NOT NULL'),
        'years_teaching': ('integer', 'DEFAULT 0', 'NOT NULL'),
        'primary_teaching_place_id': ('bigint', 'REFERENCES competitions_club(id) ON DELETE SET NULL', 'NULL'),
        'available_for_seminars': ('boolean', 'DEFAULT true', 'NOT NULL'),
        'available_for_private_lessons': ('boolean', 'DEFAULT true', 'NOT NULL'),
        'available_for_online_coaching': ('boolean', 'DEFAULT false', 'NOT NULL'),
        'hourly_rate_range': ('varchar(50)', '', 'NULL'),
        'bio': ('text', '', 'NULL'),
        'years_of_experience': ('integer', 'DEFAULT 0', 'NOT NULL'),
        'certification_info': ('text', '', 'NULL'),
        'photo': ('varchar(100)', '', 'NULL'),
    }
    
    print("\n=== Ajout des colonnes manquantes ===")
    
    for col_name, (data_type, default, nullability) in required_columns.items():
        if col_name not in existing_columns:
            # Construire la requête SQL pour ajouter la colonne
            add_column_sql = f"ALTER TABLE competitions_coachprofile ADD COLUMN {col_name} {data_type}"
            
            # Ajouter DEFAULT si spécifié
            if default:
                add_column_sql += f" {default}"
            
            # Ajouter NOT NULL si spécifié et pas de DEFAULT
            if nullability == 'NOT NULL' and not default:
                # Pour les colonnes NOT NULL sans valeur par défaut, on doit d'abord ajouter la colonne puis la contrainte
                add_column_sql = f"ALTER TABLE competitions_coachprofile ADD COLUMN {col_name} {data_type}"
            
            # Exécuter la requête
            try:
                print(f"Ajout de {col_name}...")
                cur.execute(add_column_sql)
                
                # Ajouter NOT NULL séparément si nécessaire
                if nullability == 'NOT NULL' and not default:
                    cur.execute(f"ALTER TABLE competitions_coachprofile ALTER COLUMN {col_name} SET NOT NULL")
                
                print(f"✓ Colonne {col_name} ajoutée")
            except psycopg2.Error as e:
                print(f"Erreur lors de l'ajout de {col_name}: {e}")
        else:
            print(f"- {col_name} existe déjà")
    
    # Vérifier si des colonnes ont été ajoutées
    print("\n=== Vérification de la structure mise à jour ===")
    
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'competitions_coachprofile'
        ORDER BY ordinal_position;
    """)
    
    updated_columns = {col[0]: (col[1], col[2]) for col in cur.fetchall()}
    
    print(f"Nombre de colonnes avant: {len(existing_columns)}")
    print(f"Nombre de colonnes après: {len(updated_columns)}")
    
    # Afficher les colonnes ajoutées
    added_columns = set(updated_columns.keys()) - set(existing_columns.keys())
    if added_columns:
        print("Colonnes ajoutées:")
        for col in added_columns:
            print(f"- {col} ({updated_columns[col][0]}), Nullable: {updated_columns[col][1]}")
    
    print("\n✓ Mise à jour de la table competitions_coachprofile terminée!")
    
except psycopg2.Error as e:
    print(f"Erreur de base de données : {e}")
    sys.exit(1)
except Exception as e:
    print(f"Erreur : {e}")
    sys.exit(1)
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()