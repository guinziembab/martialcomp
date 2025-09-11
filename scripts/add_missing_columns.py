"""
Script pour ajouter les colonnes manquantes directement dans la base de données
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection, transaction

def add_missing_columns():
    print("=== Ajout des colonnes manquantes ===\n")
    
    with connection.cursor() as cursor:
        # Ajouter is_migrated à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS is_migrated BOOLEAN DEFAULT FALSE;
            """)
            print("✓ Colonne is_migrated ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour is_migrated: {e}")
        
        # Ajouter tenant à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES multitenant_tenant(id) ON DELETE SET NULL;
            """)
            print("✓ Colonne tenant_id ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour tenant_id: {e}")
        
        # Ajouter migration_date à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS migration_date TIMESTAMP;
            """)
            print("✓ Colonne migration_date ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour migration_date: {e}")
        
        # Ajouter country à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS country VARCHAR(2) DEFAULT 'FR';
            """)
            print("✓ Colonne country ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour country: {e}")
        
        # Ajouter timezone à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Europe/Paris';
            """)
            print("✓ Colonne timezone ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour timezone: {e}")
        
        # Ajouter currency à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'EUR';
            """)
            print("✓ Colonne currency ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour currency: {e}")
        
        # Ajouter email à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS email VARCHAR(254);
            """)
            print("✓ Colonne email ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour email: {e}")
        
        # Ajouter phone à Club
        try:
            cursor.execute("""
                ALTER TABLE competitions_club 
                ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
            """)
            print("✓ Colonne phone ajoutée à competitions_club")
        except Exception as e:
            print(f"⚠️ Erreur pour phone: {e}")
        
        print("\n✓ Toutes les colonnes ont été traitées")

if __name__ == "__main__":
    add_missing_columns()