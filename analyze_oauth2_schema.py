#!/usr/bin/env python3
"""
Script pour analyser la structure des tables oauth2_provider et corriger les colonnes manquantes
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_postgres')
sys.path.append('C:\\martial_hub_django\\martialcomp')
os.chdir('C:\\martial_hub_django\\martialcomp')
django.setup()

from django.db import connection

def analyze_table_structure():
    """Analyser la structure actuelle des tables oauth2_provider"""
    
    print("=== Analyse de la structure des tables oauth2_provider ===")
    
    tables_to_check = [
        'oauth2_provider_accesstoken',
        'oauth2_provider_application', 
        'oauth2_provider_refreshtoken',
        'oauth2_provider_grant'
    ]
    
    with connection.cursor() as cursor:
        for table in tables_to_check:
            print(f"\n--- Table: {table} ---")
            try:
                cursor.execute(f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                print(f"Colonnes actuelles ({len(columns)}):")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"  - {col[0]} ({col[1]}) {nullable}{default}")
                    
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
    
    return True

def get_expected_oauth2_schema():
    """Retourner la structure attendue pour oauth2_provider based on latest migrations"""
    
    return {
        'oauth2_provider_accesstoken': [
            ('id', 'bigint', 'NOT NULL'),
            ('token', 'character varying(255)', 'NOT NULL'),
            ('expires', 'timestamp with time zone', 'NOT NULL'),
            ('scope', 'text', 'NOT NULL'),
            ('application_id', 'bigint', 'NULL'),
            ('user_id', 'integer', 'NULL'),
            ('created', 'timestamp with time zone', 'NOT NULL'),
            ('updated', 'timestamp with time zone', 'NOT NULL'),
            ('source_refresh_token_id', 'bigint', 'NULL'),
            ('id_token_id', 'bigint', 'NULL'),
            ('token_checksum', 'character varying(64)', 'NOT NULL'),  # Colonne manquante !
        ],
        'oauth2_provider_refreshtoken': [
            ('id', 'bigint', 'NOT NULL'),
            ('token', 'character varying(255)', 'NOT NULL'),
            ('access_token_id', 'bigint', 'NOT NULL'),
            ('application_id', 'bigint', 'NOT NULL'), 
            ('user_id', 'integer', 'NOT NULL'),
            ('created', 'timestamp with time zone', 'NOT NULL'),
            ('updated', 'timestamp with time zone', 'NOT NULL'),
            ('revoked', 'timestamp with time zone', 'NULL'),
            ('token_family_id', 'uuid', 'NULL'),  # Possiblement manquante
        ],
        'oauth2_provider_application': [
            ('id', 'bigint', 'NOT NULL'),
            ('client_id', 'character varying(100)', 'NOT NULL'),
            ('user_id', 'integer', 'NULL'),
            ('client_secret', 'character varying(255)', 'NOT NULL'),
            ('name', 'character varying(255)', 'NOT NULL'),
            ('client_type', 'character varying(32)', 'NOT NULL'),
            ('authorization_grant_type', 'character varying(32)', 'NOT NULL'),
            ('skip_authorization', 'boolean', 'NOT NULL'),
            ('created', 'timestamp with time zone', 'NOT NULL'),
            ('updated', 'timestamp with time zone', 'NOT NULL'),
            ('algorithm', 'character varying(5)', 'NOT NULL'),
            ('allowed_origins', 'text', 'NOT NULL'),
            ('post_logout_redirect_uris', 'text', 'NOT NULL'),
            ('redirect_uris', 'text', 'NOT NULL'),
            ('hash_client_secret', 'boolean', 'NOT NULL'),
        ]
    }

def find_missing_columns():
    """Comparer la structure actuelle avec la structure attendue"""
    
    print("\n=== Recherche des colonnes manquantes ===")
    
    expected = get_expected_oauth2_schema()
    missing_columns = {}
    
    with connection.cursor() as cursor:
        for table_name, expected_columns in expected.items():
            print(f"\n--- Vérification de {table_name} ---")
            
            # Obtenir les colonnes actuelles
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns 
                WHERE table_name = '{table_name}' 
                AND table_schema = 'public'
            """)
            
            current_columns = {row[0] for row in cursor.fetchall()}
            expected_column_names = {col[0] for col in expected_columns}
            
            missing = expected_column_names - current_columns
            
            if missing:
                print(f"❌ Colonnes manquantes: {missing}")
                missing_columns[table_name] = []
                
                for col_name, col_type, nullable in expected_columns:
                    if col_name in missing:
                        missing_columns[table_name].append((col_name, col_type, nullable))
                        print(f"  - {col_name} ({col_type}) {nullable}")
            else:
                print(f"✅ Toutes les colonnes sont présentes")
    
    return missing_columns

def create_missing_columns(missing_columns):
    """Créer les colonnes manquantes"""
    
    print("\n=== Ajout des colonnes manquantes ===")
    
    with connection.cursor() as cursor:
        for table_name, columns in missing_columns.items():
            print(f"\n--- Modification de {table_name} ---")
            
            for col_name, col_type, nullable in columns:
                try:
                    # Construire la commande ALTER TABLE
                    null_constraint = "" if "NULL" in nullable else "NOT NULL"
                    
                    # Valeurs par défaut appropriées pour certaines colonnes
                    default_value = ""
                    if col_name == 'token_checksum':
                        default_value = " DEFAULT ''"
                    elif col_name == 'token_family_id':
                        default_value = " DEFAULT NULL"
                    
                    sql = f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN IF NOT EXISTS {col_name} {col_type}{default_value}
                    """
                    
                    if "NOT NULL" in nullable and default_value == "":
                        # Pour les colonnes NOT NULL sans défaut, d'abord ajouter avec NULL
                        sql_temp = f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN IF NOT EXISTS {col_name} {col_type}
                        """
                        cursor.execute(sql_temp)
                        
                        # Puis remplir avec une valeur par défaut
                        if col_name == 'token_checksum':
                            cursor.execute(f"""
                                UPDATE {table_name} 
                                SET {col_name} = '' 
                                WHERE {col_name} IS NULL
                            """)
                        
                        # Enfin ajouter la contrainte NOT NULL
                        cursor.execute(f"""
                            ALTER TABLE {table_name} 
                            ALTER COLUMN {col_name} SET NOT NULL
                        """)
                    else:
                        cursor.execute(sql)
                    
                    print(f"  ✅ Colonne {col_name} ajoutée")
                    
                except Exception as e:
                    print(f"  ❌ Erreur pour {col_name}: {e}")
    
    return True

def main():
    """Fonction principale"""
    
    print("=== Diagnostic et Correction des colonnes oauth2_provider ===")
    
    # 1. Analyser la structure actuelle
    analyze_table_structure()
    
    # 2. Trouver les colonnes manquantes
    missing_columns = find_missing_columns()
    
    if not missing_columns:
        print("\n✅ Aucune colonne manquante détectée")
        return True
    
    # 3. Créer les colonnes manquantes
    create_missing_columns(missing_columns)
    
    # 4. Vérification finale
    print("\n=== Vérification finale ===")
    final_missing = find_missing_columns()
    
    if not final_missing:
        print("\n🎉 Toutes les colonnes ont été créées avec succès!")
        print("\n📋 Test final:")
        print("Ouvrez: http://127.0.0.1:8000/admin/oauth2_provider/accesstoken/")
        return True
    else:
        print(f"\n❌ Colonnes encore manquantes: {final_missing}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)