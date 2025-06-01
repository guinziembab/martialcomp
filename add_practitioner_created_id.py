#!/usr/bin/env python3
"""
Script pour ajouter la colonne practitioner_created_id manquante
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

def analyze_current_structure():
    """Analyser la structure actuelle de competitions_organizationqrcodescan"""
    
    print("=== Analyse de la structure actuelle ===")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'competitions_organizationqrcodescan'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        current_columns = cursor.fetchall()
        
        print(f"Colonnes actuelles ({len(current_columns)}):")
        column_names = []
        for col in current_columns:
            nullable = "NULL" if col[2] == "YES" else "NOT NULL"
            default = f" DEFAULT {col[3]}" if col[3] else ""
            print(f"  - {col[0]} ({col[1]}) {nullable}{default}")
            column_names.append(col[0])
        
        return column_names

def identify_missing_qr_columns(current_columns):
    """Identifier toutes les colonnes manquantes probables"""
    
    print("\n=== Identification des colonnes manquantes ===")
    
    # Colonnes probables basées sur l'erreur et les patterns Django
    expected_columns = [
        ('practitioner_created_id', 'BIGINT', 'NULL'),  # ← Colonne manquante dans l'erreur
        ('practitioner_updated_id', 'BIGINT', 'NULL'),
        ('organization_id', 'BIGINT', 'NULL'),
        ('club_id', 'BIGINT', 'NULL'),
        ('federation_id', 'BIGINT', 'NULL'),
        ('event_id', 'BIGINT', 'NULL'),
        ('competition_id', 'BIGINT', 'NULL'),
        ('session_id', 'VARCHAR(255)', 'NULL'),
        ('device_info', 'TEXT', 'NULL'),
        ('metadata', 'JSONB', 'NULL'),
        ('created_by_id', 'INTEGER', 'NULL'),
        ('updated_by_id', 'INTEGER', 'NULL'),
        ('updated_at', 'TIMESTAMP WITH TIME ZONE', 'NULL')
    ]
    
    missing_columns = []
    
    for col_name, col_type, nullable in expected_columns:
        if col_name not in current_columns:
            missing_columns.append((col_name, col_type, nullable))
            print(f"❌ Manquante: {col_name} ({col_type}) {nullable}")
        else:
            print(f"✅ Présente: {col_name}")
    
    return missing_columns

def add_missing_qr_columns(missing_columns):
    """Ajouter toutes les colonnes manquantes"""
    
    print(f"\n=== Ajout de {len(missing_columns)} colonnes manquantes ===")
    
    if not missing_columns:
        print("✅ Aucune colonne à ajouter")
        return True
    
    with connection.cursor() as cursor:
        success_count = 0
        
        for col_name, col_type, nullable in missing_columns:
            print(f"\nAjout de {col_name}...")
            
            try:
                # Déterminer la valeur par défaut
                default_value = ""
                if col_name == 'practitioner_created_id':
                    default_value = " DEFAULT NULL"
                elif col_name == 'practitioner_updated_id':
                    default_value = " DEFAULT NULL"
                elif 'id' in col_name and col_name.endswith('_id'):
                    default_value = " DEFAULT NULL"
                elif col_name == 'metadata':
                    default_value = " DEFAULT '{}'"
                elif col_name == 'device_info':
                    default_value = " DEFAULT ''"
                elif col_name == 'session_id':
                    default_value = " DEFAULT NULL"
                elif col_name in ['updated_at']:
                    default_value = " DEFAULT NOW()"
                
                sql = f"""
                    ALTER TABLE competitions_organizationqrcodescan 
                    ADD COLUMN {col_name} {col_type}{default_value}
                """
                
                cursor.execute(sql)
                print(f"  ✅ {col_name} ajoutée")
                success_count += 1
                
            except Exception as e:
                print(f"  ❌ Erreur pour {col_name}: {e}")
        
        print(f"\n📊 Résultat: {success_count}/{len(missing_columns)} colonnes ajoutées")
        return success_count == len(missing_columns)

def test_practitioner_created_id():
    """Tester spécifiquement la colonne practitioner_created_id"""
    
    print("\n=== Test de practitioner_created_id ===")
    
    try:
        with connection.cursor() as cursor:
            # Test de la colonne
            cursor.execute("""
                SELECT practitioner_created_id 
                FROM competitions_organizationqrcodescan 
                LIMIT 1
            """)
            print("✅ Colonne practitioner_created_id accessible")
            
            # Test de l'UPDATE qui échoue (comme dans l'erreur originale)
            cursor.execute("""
                UPDATE competitions_organizationqrcodescan 
                SET practitioner_created_id = NULL 
                WHERE practitioner_created_id = 999999
            """)
            print("✅ UPDATE practitioner_created_id fonctionne")
            
            # Vérifier la structure finale
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'competitions_organizationqrcodescan'
                AND column_name = 'practitioner_created_id'
            """)
            
            if cursor.fetchone():
                print("✅ practitioner_created_id confirmée dans la structure")
                return True
            else:
                print("❌ practitioner_created_id non trouvée")
                return False
            
    except Exception as e:
        print(f"❌ Erreur de test: {e}")
        return False

def verify_final_structure():
    """Vérifier la structure finale de la table"""
    
    print("\n=== Structure finale ===")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = 'competitions_organizationqrcodescan'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        final_columns = cursor.fetchall()
        
        print(f"Structure finale ({len(final_columns)} colonnes):")
        for col_name, col_type in final_columns:
            print(f"  - {col_name} ({col_type})")
        
        # Vérifier spécifiquement practitioner_created_id
        has_column = any(col[0] == 'practitioner_created_id' for col in final_columns)
        
        if has_column:
            print("✅ practitioner_created_id présente - l'erreur devrait être résolue")
            return True
        else:
            print("❌ practitioner_created_id toujours manquante")
            return False

def main():
    """Fonction principale"""
    
    print("=== Correction de practitioner_created_id manquante ===")
    
    # 1. Analyser la structure actuelle
    current_columns = analyze_current_structure()
    
    # 2. Identifier les colonnes manquantes
    missing_columns = identify_missing_qr_columns(current_columns)
    
    # 3. Ajouter les colonnes manquantes
    if not add_missing_qr_columns(missing_columns):
        print("\n❌ Échec de l'ajout des colonnes")
        return False
    
    # 4. Tester practitioner_created_id spécifiquement
    if not test_practitioner_created_id():
        print("\n❌ Test de practitioner_created_id échoué")
        return False
    
    # 5. Vérifier la structure finale
    if not verify_final_structure():
        print("\n❌ Structure finale incorrecte")
        return False
    
    print("\n🎉 practitioner_created_id ajoutée avec succès!")
    print("\n📋 Test final:")
    print("1. Essayez de supprimer un compte")
    print("2. L'erreur 'practitioner_created_id n'existe pas' devrait être résolue")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)