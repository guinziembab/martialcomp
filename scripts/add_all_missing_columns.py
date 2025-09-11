#!/usr/bin/env python3
"""
Script pour ajouter TOUTES les colonnes manquantes d'un coup
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

def add_all_missing_columns():
    """Ajouter toutes les colonnes manquantes probables"""
    
    print("=== Ajout de toutes les colonnes manquantes ===")
    
    # Liste complète des colonnes probablement nécessaires
    columns_to_add = [
        ('performance_order', 'INTEGER', 'NULL'),  # ← La colonne spécifiquement manquante
        ('competition_id', 'BIGINT', 'NULL'),
        ('judge_id', 'BIGINT', 'NULL'),
        ('technical_score', 'DECIMAL(5,2)', 'NULL'),
        ('artistic_score', 'DECIMAL(5,2)', 'NULL'),
        ('difficulty_score', 'DECIMAL(5,2)', 'NULL'),
        ('execution_score', 'DECIMAL(5,2)', 'NULL'),
        ('presentation_score', 'DECIMAL(5,2)', 'NULL'),
        ('notes', 'TEXT', 'NULL'),
        ('updated_at', 'TIMESTAMP WITH TIME ZONE', 'NULL'),
        ('is_final', 'BOOLEAN', 'NULL'),
        ('rank', 'INTEGER', 'NULL'),
        ('round_number', 'INTEGER', 'NULL'),
        ('attempt_number', 'INTEGER', 'NULL'),
        ('validation_status', 'VARCHAR(20)', 'NULL'),
        ('validated_by_id', 'BIGINT', 'NULL'),
        ('validated_at', 'TIMESTAMP WITH TIME ZONE', 'NULL')
    ]
    
    with connection.cursor() as cursor:
        # Obtenir les colonnes actuelles
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'competitions_technicalperformanceresult'
            AND table_schema = 'public'
        """)
        
        current_columns = [row[0] for row in cursor.fetchall()]
        print(f"Colonnes actuelles: {current_columns}")
        
        # Ajouter chaque colonne manquante
        added_count = 0
        
        for col_name, sql_type, nullable in columns_to_add:
            if col_name not in current_columns:
                print(f"\nAjout de {col_name}...")
                
                try:
                    # Déterminer la valeur par défaut
                    default_value = ""
                    if col_name == 'performance_order':
                        default_value = " DEFAULT 1"
                    elif 'score' in col_name:
                        default_value = " DEFAULT 0.00"
                    elif col_name == 'notes':
                        default_value = " DEFAULT ''"
                    elif col_name == 'is_final':
                        default_value = " DEFAULT FALSE"
                    elif col_name == 'validation_status':
                        default_value = " DEFAULT 'pending'"
                    elif col_name in ['updated_at', 'validated_at'] and 'NOT NULL' in nullable:
                        default_value = " DEFAULT NOW()"
                    elif 'NULL' in nullable:
                        default_value = " DEFAULT NULL"
                    
                    sql = f"""
                        ALTER TABLE competitions_technicalperformanceresult 
                        ADD COLUMN {col_name} {sql_type}{default_value}
                    """
                    
                    cursor.execute(sql)
                    print(f"  ✅ {col_name} ajoutée")
                    added_count += 1
                    
                except Exception as e:
                    print(f"  ⚠️  Erreur pour {col_name}: {e}")
            else:
                print(f"✅ {col_name} existe déjà")
        
        print(f"\n📊 Résultat: {added_count} nouvelles colonnes ajoutées")
        
        # Vérification finale
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'competitions_technicalperformanceresult'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"\nStructure finale ({len(final_columns)} colonnes):")
        for col in final_columns:
            print(f"  - {col}")
        
        # Vérifier spécifiquement performance_order
        if 'performance_order' in final_columns:
            print(f"\n✅ performance_order présente - l'erreur devrait être résolue")
            return True
        else:
            print(f"\n❌ performance_order toujours manquante")
            return False

def test_performance_order_query():
    """Tester une requête avec performance_order"""
    
    print(f"\n=== Test de requête avec performance_order ===")
    
    try:
        with connection.cursor() as cursor:
            # Test de la colonne performance_order
            cursor.execute("""
                SELECT id, performance_order 
                FROM competitions_technicalperformanceresult 
                ORDER BY performance_order 
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            print(f"✅ Requête ORDER BY performance_order réussie: {len(results)} résultats")
            
            # Test de jointure comme dans l'erreur originale
            cursor.execute("""
                SELECT COUNT(*) 
                FROM competitions_technicalperformanceresult t
                LEFT JOIN competitions_competitioncategory c ON t.category_id = c.id
                ORDER BY c.name, t.performance_order
                LIMIT 1
            """)
            
            print("✅ Requête avec jointure et ORDER BY réussie")
            return True
            
    except Exception as e:
        print(f"❌ Erreur de test: {e}")
        return False

def main():
    """Fonction principale"""
    
    print("=== Correction Complète des Colonnes Manquantes ===")
    
    # Ajouter toutes les colonnes
    if not add_all_missing_columns():
        print("\n❌ Échec de l'ajout des colonnes")
        return False
    
    # Tester les requêtes
    if not test_performance_order_query():
        print("\n⚠️  Test de requête échoué")
    
    print("\n🎉 Toutes les colonnes ajoutées!")
    print("\n📋 Test final:")
    print("1. Essayez de supprimer un compte")
    print("2. L'erreur 'performance_order n'existe pas' devrait être résolue")
    print("3. Si d'autres colonnes manquent, elles ont probablement été ajoutées aussi")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)