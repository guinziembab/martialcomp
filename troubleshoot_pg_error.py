#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script de diagnostic pour le problème de colonne manquante dans PostgreSQL
"""
import psycopg2
import sys
import json

print("Script de diagnostic pour le problème de colonne manquante")

# Paramètres de connexion à la base de données
DB_NAME = "martialcomp"
DB_USER = "postgres"
DB_PASSWORD = "postgres"  # Remplacer par votre mot de passe si différent
DB_HOST = "localhost"
DB_PORT = "5432"

# Se connecter à la base de données
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
    
    # 1. Vérifier la structure de la table practitioner
    print("\n=== Structure de competitions_practitioner ===")
    
    cur.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'competitions_practitioner' 
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    print(f"Nombre de colonnes: {len(columns)}")
    
    for col in columns:
        print(f"- {col[0]} ({col[1]}), Nullable: {col[2]}")
    
    # 2. Vérifier si primary_discipline_id existe
    print("\n=== Vérification de primary_discipline_id ===")
    
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'competitions_practitioner' 
        AND column_name = 'primary_discipline_id';
    """)
    
    has_column = cur.fetchone() is not None
    print(f"primary_discipline_id existe: {has_column}")
    
    # 3. Vérifier les contraintes et index
    print("\n=== Contraintes et index sur competitions_practitioner ===")
    
    cur.execute("""
        SELECT conname, contype, pg_get_constraintdef(c.oid) 
        FROM pg_constraint c 
        JOIN pg_namespace n ON n.oid = c.connamespace 
        WHERE n.nspname = 'public' AND conrelid = 'competitions_practitioner'::regclass;
    """)
    
    constraints = cur.fetchall()
    print(f"Nombre de contraintes: {len(constraints)}")
    
    for con in constraints:
        print(f"- {con[0]} (Type: {con[1]}): {con[2]}")
    
    cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename = 'competitions_practitioner';
    """)
    
    indexes = cur.fetchall()
    print(f"Nombre d'index: {len(indexes)}")
    
    for idx in indexes:
        print(f"- {idx[0]}: {idx[1]}")
    
    # 4. Vérifier les migrations
    print("\n=== Migrations Django ===")
    
    cur.execute("""
        SELECT app, name, applied 
        FROM django_migrations 
        WHERE app = 'competitions' 
        ORDER BY id DESC 
        LIMIT 10;
    """)
    
    migrations = cur.fetchall()
    print(f"Dernières migrations competitions: {len(migrations)}")
    
    for mig in migrations:
        print(f"- {mig[0]}.{mig[1]}, appliquée le {mig[2]}")
    
    # 5. Solution suggérée
    print("\n=== Solution suggérée ===")
    
    if not has_column:
        print("La colonne primary_discipline_id n'existe pas.")
        print("Solution: Exécuter le script fix_postgres_coach.py pour ajouter la colonne manquante.")
    else:
        print("La colonne primary_discipline_id existe mais n'est peut-être pas reconnue par Django.")
        print("Solution: Vérifier les migrations Django et potentiellement faire un reset des migrations.")
    
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