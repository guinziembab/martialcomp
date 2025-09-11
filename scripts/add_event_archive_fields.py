#!/usr/bin/env python
import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def add_archive_fields():
    """Ajouter les champs d'archivage au modèle Event"""
    
    with connection.cursor() as cursor:
        try:
            # Vérifier si les champs existent déjà
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'competitions_event' 
                AND column_name IN ('is_archived', 'archived_at')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            # Ajouter le champ is_archived s'il n'existe pas
            if 'is_archived' not in existing_columns:
                print("Ajout du champ is_archived...")
                cursor.execute("""
                    ALTER TABLE competitions_event 
                    ADD COLUMN is_archived BOOLEAN DEFAULT FALSE NOT NULL
                """)
                print("✅ Champ is_archived ajouté avec succès")
            else:
                print("ℹ️ Le champ is_archived existe déjà")
            
            # Ajouter le champ archived_at s'il n'existe pas
            if 'archived_at' not in existing_columns:
                print("Ajout du champ archived_at...")
                cursor.execute("""
                    ALTER TABLE competitions_event 
                    ADD COLUMN archived_at TIMESTAMP NULL
                """)
                print("✅ Champ archived_at ajouté avec succès")
            else:
                print("ℹ️ Le champ archived_at existe déjà")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout des champs d'archivage : {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🔧 Ajout des champs d'archivage pour les événements...")
    
    if add_archive_fields():
        print("✅ Tous les champs d'archivage ont été ajoutés avec succès !")
    else:
        print("❌ Erreur lors de l'ajout des champs d'archivage")
        sys.exit(1)