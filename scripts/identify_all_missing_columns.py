#!/usr/bin/env python3
"""
Script pour identifier TOUTES les colonnes manquantes en analysant le modèle réel
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
from django.apps import apps

def get_current_table_columns():
    """Obtenir les colonnes actuelles de la table"""
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'competitions_technicalperformanceresult'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        return [row[0] for row in cursor.fetchall()]

def find_django_model_for_table():
    """Trouver le modèle Django correspondant à la table"""
    
    print("=== Recherche du modèle Django ===")
    
    # Chercher dans tous les modèles de l'app competitions
    for model in apps.get_models():
        if model._meta.app_label == 'competitions':
            table_name = model._meta.db_table
            if 'technicalperformanceresult' in table_name.lower():
                print(f"✅ Modèle trouvé: {model.__name__} -> {table_name}")
                return model
    
    print("❌ Aucun modèle correspondant trouvé")
    return None

def analyze_model_fields(model):
    """Analyser les champs du modèle Django"""
    
    if not model:
        return []
    
    print(f"\n=== Analyse du modèle {model.__name__} ===")
    
    expected_columns = []
    
    for field in model._meta.get_fields():
        if hasattr(field, 'column'):
            column_name = field.column
            field_type = type(field).__name__
            
            # Déterminer le type SQL
            if hasattr(field, 'get_internal_type'):
                internal_type = field.get_internal_type()
                
                sql_type = "TEXT"
                if internal_type == "BigAutoField":
                    sql_type = "BIGSERIAL"
                elif internal_type == "BigIntegerField":
                    sql_type = "BIGINT"
                elif internal_type == "DecimalField":
                    max_digits = getattr(field, 'max_digits', 10)
                    decimal_places = getattr(field, 'decimal_places', 2)
                    sql_type = f"DECIMAL({max_digits},{decimal_places})"
                elif internal_type == "DateTimeField":
                    sql_type = "TIMESTAMP WITH TIME ZONE"
                elif internal_type == "BooleanField":
                    sql_type = "BOOLEAN"
                elif internal_type == "IntegerField":
                    sql_type = "INTEGER"
                elif internal_type == "CharField":
                    max_length = getattr(field, 'max_length', 255)
                    sql_type = f"VARCHAR({max_length})"
                elif internal_type == "TextField":
                    sql_type = "TEXT"
                elif internal_type == "ForeignKey":
                    sql_type = "BIGINT"
                
                # Déterminer nullable
                nullable = "NULL" if field.null else "NOT NULL"
                
                expected_columns.append((column_name, sql_type, nullable, field_type))
                print(f"  - {column_name} ({sql_type}) {nullable} [{field_type}]")
    
    return expected_columns

def compare_and_find_missing(current_columns, expected_columns):
    """Comparer et trouver les colonnes manquantes"""
    
    print(f"\n=== Comparaison ===")
    print(f"Colonnes actuelles: {len(current_columns)}")
    print(f"Colonnes attendues: {len(expected_columns)}")
    
    missing_columns = []
    
    for col_name, sql_type, nullable, field_type in expected_columns:
        if col_name not in current_columns:
            missing_columns.append((col_name, sql_type, nullable))
            print(f"❌ Manquante: {col_name} ({sql_type}) {nullable}")
        else:
            print(f"✅ Présente: {col_name}")
    
    return missing_columns

def search_for_performance_order():
    """Rechercher spécifiquement la colonne performance_order"""
    
    print(f"\n=== Recherche spécifique de performance_order ===")
    
    # Chercher dans tous les modèles
    for model in apps.get_models():
        if model._meta.app_label == 'competitions':
            for field in model._meta.get_fields():
                if hasattr(field, 'column') and 'performance_order' in field.column:
                    print(f"✅ performance_order trouvée dans {model.__name__}.{field.name}")
                    return model, field
                elif hasattr(field, 'name') and 'performance_order' in field.name:
                    print(f"✅ performance_order trouvée dans {model.__name__}.{field.name}")
                    return model, field
    
    print("❌ performance_order non trouvée dans les modèles")
    return None, None

def analyze_query_patterns():
    """Analyser les patterns de requête pour comprendre les colonnes utilisées"""
    
    print(f"\n=== Analyse des patterns de requête ===")
    
    # L'erreur montre: ORDER BY competitions_competitioncategory.name ASC, competitions_technicalperformanceresult.performance_order
    # Cela suggère que performance_order est utilisé pour trier les résultats
    
    common_ordering_fields = [
        ('performance_order', 'INTEGER', 'NULL'),
        ('order', 'INTEGER', 'NULL'),
        ('position', 'INTEGER', 'NULL'),
        ('sequence', 'INTEGER', 'NULL'),
        ('ranking', 'INTEGER', 'NULL')
    ]
    
    print("Colonnes probables pour l'ordre:")
    for col_name, sql_type, nullable in common_ordering_fields:
        print(f"  - {col_name} ({sql_type}) {nullable}")
    
    return common_ordering_fields

def main():
    """Fonction principale d'analyse"""
    
    print("=== Identification complète des colonnes manquantes ===")
    
    # 1. Obtenir les colonnes actuelles
    current_columns = get_current_table_columns()
    print(f"Colonnes actuelles ({len(current_columns)}): {current_columns}")
    
    # 2. Trouver le modèle Django
    model = find_django_model_for_table()
    
    # 3. Analyser les champs du modèle
    expected_columns = []
    if model:
        expected_columns = analyze_model_fields(model)
    
    # 4. Comparer et trouver les manquantes
    missing_from_model = []
    if expected_columns:
        missing_from_model = compare_and_find_missing(current_columns, expected_columns)
    
    # 5. Recherche spécifique de performance_order
    perf_model, perf_field = search_for_performance_order()
    
    # 6. Analyser les patterns communs
    common_fields = analyze_query_patterns()
    
    # 7. Proposer toutes les colonnes à ajouter
    print(f"\n=== Colonnes à ajouter ===")
    
    all_missing = missing_from_model.copy()
    
    # Ajouter performance_order si pas trouvée
    if not any(col[0] == 'performance_order' for col in all_missing):
        all_missing.append(('performance_order', 'INTEGER', 'NULL'))
        print("+ Ajout de performance_order (basé sur l'erreur)")
    
    # Autres colonnes probablement nécessaires
    probable_columns = [
        ('competition_id', 'BIGINT', 'NULL'),
        ('judge_id', 'BIGINT', 'NULL'),
        ('technical_score', 'DECIMAL(5,2)', 'NULL'),
        ('artistic_score', 'DECIMAL(5,2)', 'NULL'),
        ('difficulty_score', 'DECIMAL(5,2)', 'NULL'),
        ('execution_score', 'DECIMAL(5,2)', 'NULL'),
        ('presentation_score', 'DECIMAL(5,2)', 'NULL'),
        ('notes', 'TEXT', 'NULL'),
        ('updated_at', 'TIMESTAMP WITH TIME ZONE', 'NOT NULL'),
        ('is_final', 'BOOLEAN', 'NULL'),
        ('rank', 'INTEGER', 'NULL')
    ]
    
    for col_name, sql_type, nullable in probable_columns:
        if col_name not in current_columns and not any(col[0] == col_name for col in all_missing):
            all_missing.append((col_name, sql_type, nullable))
    
    print(f"\nTotal de colonnes à ajouter: {len(all_missing)}")
    for col_name, sql_type, nullable in all_missing:
        print(f"  + {col_name} ({sql_type}) {nullable}")
    
    return all_missing

if __name__ == '__main__':
    missing_columns = main()
    print(f"\n📊 Résultat: {len(missing_columns)} colonnes manquantes identifiées")
    sys.exit(0)