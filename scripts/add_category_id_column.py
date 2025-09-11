#!/usr/bin/env python3
"""
Solution ultra-rapide pour ajouter uniquement la colonne category_id manquante
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
sys.path.append('C:\\martial_hub_django\\martialcomp')
os.chdir('C:\\martial_hub_django\\martialcomp')
django.setup()

from django.db import connection

def add_category_id_column():
    """Ajouter uniquement la colonne category_id manquante"""
    
    print("=== Ajout de la colonne category_id ===")
    
    try:
        with connection.cursor() as cursor:
            # Vérifier si la colonne existe déjà
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'competitions_technicalperformanceresult'
                AND column_name = 'category_id'
                AND table_schema = 'public'
            """)
            
            if cursor.fetchone():
                print("✅ Colonne category_id existe déjà")
                return True
            
            # Ajouter la colonne category_id
            print("Ajout de category_id...")
            cursor.execute("""
                ALTER TABLE competitions_technicalperformanceresult 
                ADD COLUMN category_id BIGINT DEFAULT NULL
            """)
            
            # Vérifier l'ajout
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'competitions_technicalperformanceresult'
                AND column_name = 'category_id'
            """)
            
            if cursor.fetchone():
                print("✅ Colonne category_id ajoutée avec succès")
                
                # Test d'accès
                cursor.execute("SELECT category_id FROM competitions_technicalperformanceresult LIMIT 1")
                print("✅ Colonne accessible")
                
                return True
            else:
                print("❌ Colonne non trouvée après ajout")
                return False
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_deletion_query():
    """Tester une requête similaire à celle qui échoue"""
    
    print("\n=== Test de requête avec category_id ===")
    
    try:
        with connection.cursor() as cursor:
            # Simuler une requête qui utilise category_id (comme dans l'erreur)
            cursor.execute("""
                SELECT t.id, t.category_id 
                FROM competitions_technicalperformanceresult t
                WHERE t.category_id IS NULL OR t.category_id IS NOT NULL
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            print(f"✅ Requête réussie: {len(results)} résultats")
            
            # Test de jointure (comme suggéré dans l'erreur)
            # Vérifier d'abord si competitions_competitioncategory existe
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name = 'competitions_competitioncategory'
                AND table_schema = 'public'
            """)
            
            if cursor.fetchone():
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM competitions_technicalperformanceresult t
                    LEFT JOIN competitions_competitioncategory c ON t.category_id = c.id
                    LIMIT 1
                """)
                print("✅ Jointure avec competitions_competitioncategory réussie")
            else:
                print("ℹ️  Table competitions_competitioncategory n'existe pas encore")
            
            return True
            
    except Exception as e:
        print(f"❌ Erreur de test: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("=== Correction Rapide category_id ===")
    
    # Ajouter la colonne
    if not add_category_id_column():
        print("\n❌ Échec de l'ajout de category_id")
        return False
    
    # Tester
    if not test_deletion_query():
        print("\n⚠️  Test de requête échoué")
    
    print("\n🎉 Colonne category_id ajoutée!")
    print("\n📋 Test final:")
    print("Essayez de supprimer un compte - l'erreur category_id devrait être résolue")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)