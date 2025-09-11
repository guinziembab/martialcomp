"""Script pour ajouter le champ is_migrated au modèle Club."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection


def check_and_add_is_migrated():
    print("=== Vérification du champ is_migrated ===\n")
    
    with connection.cursor() as cursor:
        # Vérifier si le champ existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='competitions_club' 
            AND column_name='is_migrated';
        """)
        
        exists = cursor.fetchone()
        
        if exists:
            print("✓ Le champ is_migrated existe déjà")
        else:
            print("✗ Le champ is_migrated n'existe pas")
            print("\nPour l'ajouter, suivez ces étapes :")
            print("\n1. Ouvrez competitions/models/club.py")
            print("2. Ajoutez ce champ à la classe Club :")
            print("   is_migrated = models.BooleanField(default=False, verbose_name='Migré vers multi-tenant')")
            print("\n3. Créez une migration :")
            print("   python manage.py makemigrations competitions")
            print("\n4. Appliquez la migration :")
            print("   python manage.py migrate competitions")
            
            # Vérifier le modèle actuel
            print("\n\nStructure actuelle de la table competitions_club :")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'competitions_club'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            for col in columns:
                print(f"   - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")


if __name__ == "__main__":
    check_and_add_is_migrated()