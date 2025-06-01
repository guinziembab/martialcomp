#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour ajouter directement la colonne teaching_place_name à la base de données
"""
import os
import sys
import subprocess

# Tenter d'importer psycopg2
try:
    import psycopg2
    print("Module psycopg2 trouvé.")
except ImportError:
    print("Module psycopg2 non trouvé. Installation...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2"])
    import psycopg2
    print("Module psycopg2 installé.")

# Paramètres de la base de données PostgreSQL
db_params = {
    'dbname': 'martialcomp',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

# Fonction pour ajouter la colonne à PostgreSQL
def add_column_to_postgres():
    try:
        print("Tentative de connexion à PostgreSQL...")
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connexion réussie à PostgreSQL")
        
        # Vérifier si la colonne teaching_place_name existe déjà
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'competitions_coachprofile' 
            AND column_name = 'teaching_place_name';
        """)
        
        if cursor.fetchone():
            print("La colonne teaching_place_name existe déjà.")
        else:
            # Ajouter la colonne
            print("Ajout de la colonne teaching_place_name...")
            cursor.execute("""
                ALTER TABLE competitions_coachprofile 
                ADD COLUMN teaching_place_name VARCHAR(200) DEFAULT '';
            """)
            print("✓ Colonne teaching_place_name ajoutée avec succès à PostgreSQL!")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur PostgreSQL: {e}")
        return False

# Fonction pour ajouter la colonne à SQLite
def add_column_to_sqlite():
    try:
        import sqlite3
        
        # Vérifier si la base de données SQLite existe
        if os.path.exists('db.sqlite3'):
            print("Base de données SQLite trouvée.")
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            
            # Vérifier si la colonne existe déjà
            cursor.execute("PRAGMA table_info(competitions_coachprofile)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'teaching_place_name' in columns:
                print("La colonne teaching_place_name existe déjà dans SQLite.")
            else:
                print("Ajout de la colonne teaching_place_name à SQLite...")
                cursor.execute("""
                    ALTER TABLE competitions_coachprofile 
                    ADD COLUMN teaching_place_name TEXT DEFAULT '';
                """)
                print("✓ Colonne teaching_place_name ajoutée avec succès à SQLite!")
            
            conn.commit()
            conn.close()
            return True
        else:
            print("Base de données SQLite non trouvée.")
            return False
    except Exception as e:
        print(f"Erreur SQLite: {e}")
        return False

# Fonction pour créer la migration Django
def create_django_migration():
    try:
        # Créer la migration
        print("\nCréation de la migration pour teaching_place_name...")
        migration_dir = "competitions/migrations"
        os.makedirs(migration_dir, exist_ok=True)
        
        # Trouver le prochain numéro de migration
        existing_migrations = [f for f in os.listdir(migration_dir) if f.startswith("00") and f.endswith(".py")]
        existing_numbers = [int(f.split("_")[0]) for f in existing_migrations if f.split("_")[0].isdigit()]
        next_number = max(existing_numbers) + 1 if existing_numbers else 1
        
        migration_file = f"{migration_dir}/{next_number:04d}_add_teaching_place_name.py"
        
        migration_content = f"""# Generated manually for teaching_place_name
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '{(next_number-1):04d}_coachprofile_teaching_place'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachprofile',
            name='teaching_place_name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Nom de votre club, dojo ou lieu d\\'enseignement principal',
                max_length=200,
                verbose_name='Lieu ou club d\\'enseignement'
            ),
        ),
    ]
"""
        
        # Vérifier si le fichier existe déjà
        if os.path.exists(migration_file):
            print(f"La migration {migration_file} existe déjà.")
        else:
            with open(migration_file, "w", encoding="utf-8") as f:
                f.write(migration_content)
            print(f"✓ Migration créée: {migration_file}")
        
        return True
    except Exception as e:
        print(f"Erreur lors de la création de la migration: {e}")
        return False

# Fonction pour mettre à jour le modèle si nécessaire
def update_forms_if_needed():
    # Vérifier le formulaire
    forms_file = "competitions/forms/onboarding.py"
    
    if os.path.exists(forms_file):
        with open(forms_file, "r", encoding="utf-8") as f:
            forms_content = f.read()
        
        # Vérifier si teaching_place_name est déjà dans le formulaire
        if "'teaching_place_name'" in forms_content or '"teaching_place_name"' in forms_content:
            print("Le champ teaching_place_name est déjà présent dans le formulaire.")
            return True
        else:
            print("Mise à jour du formulaire pour inclure teaching_place_name...")
            
            # Créer une sauvegarde
            with open(f"{forms_file}.col.bak", "w", encoding="utf-8") as f:
                f.write(forms_content)
            
            # Remplacer primary_teaching_place par teaching_place_name
            updated_forms = forms_content.replace(
                "'primary_teaching_place'", 
                "'teaching_place_name'"
            ).replace(
                '"primary_teaching_place"', 
                '"teaching_place_name"'
            )
            
            # Écrire le contenu mis à jour
            with open(forms_file, "w", encoding="utf-8") as f:
                f.write(updated_forms)
            
            print("✓ Formulaire mis à jour pour utiliser teaching_place_name")
            return True
    else:
        print(f"Fichier {forms_file} non trouvé.")
        return False

# Exécuter les fonctions principales
print("==== Ajout de la colonne teaching_place_name à la base de données ====\n")

# Tenter de mettre à jour PostgreSQL et SQLite
pg_success = add_column_to_postgres()
sqlite_success = add_column_to_sqlite()

# Mettre à jour le formulaire si nécessaire
forms_updated = update_forms_if_needed()

# Créer la migration Django
migration_created = create_django_migration()

print("\n==== Résumé des opérations ====")
print(f"PostgreSQL: {'✓ Réussi' if pg_success else '❌ Échec'}")
print(f"SQLite: {'✓ Réussi' if sqlite_success else '❌ Échec'}")
print(f"Formulaire: {'✓ Mis à jour' if forms_updated else '❌ Non mis à jour'}")
print(f"Migration Django: {'✓ Créée' if migration_created else '❌ Non créée'}")

print("\nVeuillez exécuter la commande suivante pour appliquer les migrations:")
print("python manage.py migrate")
print("\nPuis redémarrez votre serveur Django.")