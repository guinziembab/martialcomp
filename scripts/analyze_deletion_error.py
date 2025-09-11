#!/usr/bin/env python3
"""
Script pour analyser l'erreur de suppression et identifier les tables manquantes
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

def check_competitions_tables():
    """Vérifier les tables competitions existantes et manquantes"""
    
    print("=== Vérification des tables competitions ===")
    
    with connection.cursor() as cursor:
        # Lister toutes les tables competitions
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'competitions_%'
            ORDER BY table_name
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Tables competitions existantes ({len(existing_tables)}):")
        for table in existing_tables:
            print(f"  ✅ {table}")
        
        # Tables attendues pour technical scoring
        expected_technical_tables = [
            'competitions_technicalperformanceresult',
            'competitions_technicalscoring',
            'competitions_technicalscoringcriteria',
            'competitions_technicalperformance',
            'competitions_performancecriteria'
        ]
        
        print(f"\nTables technical scoring attendues:")
        missing_technical = []
        for table in expected_technical_tables:
            if table in existing_tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (MANQUANTE)")
                missing_technical.append(table)
        
        return existing_tables, missing_technical

def check_practitioner_dependencies():
    """Analyser les dépendances de suppression pour Practitioner"""
    
    print("\n=== Analyse des dépendances Practitioner ===")
    
    try:
        from competitions.models import Practitioner
        
        # Obtenir les champs avec des relations
        practitioner_model = Practitioner._meta
        related_fields = []
        
        for field in practitioner_model.get_fields():
            if hasattr(field, 'related_model') and field.related_model:
                related_fields.append((field.name, field.related_model.__name__, getattr(field, 'on_delete', 'N/A')))
        
        print("Champs relationnels dans Practitioner:")
        for field_name, related_model, on_delete in related_fields:
            print(f"  - {field_name} -> {related_model} (on_delete: {on_delete})")
        
        # Chercher les modèles qui référencent Practitioner
        from django.apps import apps
        
        print("\nModèles qui référencent Practitioner:")
        referencing_models = []
        
        for model in apps.get_models():
            if model._meta.app_label == 'competitions':
                for field in model._meta.get_fields():
                    if (hasattr(field, 'related_model') and 
                        field.related_model and 
                        field.related_model.__name__ == 'Practitioner'):
                        referencing_models.append((model.__name__, field.name, getattr(field, 'on_delete', 'N/A')))
                        print(f"  - {model.__name__}.{field.name} (on_delete: {getattr(field, 'on_delete', 'N/A')})")
        
        return referencing_models
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        return []

def find_technical_scoring_models():
    """Trouver les modèles de scoring technique définis"""
    
    print("\n=== Modèles de scoring technique définis ===")
    
    try:
        from django.apps import apps
        
        technical_models = []
        
        for model in apps.get_models():
            if model._meta.app_label == 'competitions':
                model_name = model.__name__.lower()
                if 'technical' in model_name or 'performance' in model_name or 'scoring' in model_name:
                    table_name = model._meta.db_table
                    technical_models.append((model.__name__, table_name))
                    print(f"  - {model.__name__} -> {table_name}")
        
        return technical_models
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def check_migrations_status():
    """Vérifier l'état des migrations competitions"""
    
    print("\n=== État des migrations competitions ===")
    
    try:
        from django.core.management import execute_from_command_line
        import io
        import sys
        
        # Capturer la sortie de showmigrations
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        try:
            execute_from_command_line(['manage.py', 'showmigrations', 'competitions', '--settings=config.settings_postgres'])
        except SystemExit:
            pass
        
        sys.stdout = old_stdout
        migrations_output = captured_output.getvalue()
        
        print("Migrations competitions:")
        for line in migrations_output.split('\n'):
            if line.strip():
                print(f"  {line}")
        
        return migrations_output
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return ""

def propose_solutions(missing_technical):
    """Proposer des solutions pour corriger le problème"""
    
    print("\n=== Solutions proposées ===")
    
    if missing_technical:
        print(f"🔧 Solution 1: Créer les tables manquantes ({len(missing_technical)} tables)")
        print("   - Exécuter les migrations competitions")
        print("   - Ou créer manuellement les tables")
        
        print(f"\n🔧 Solution 2: Ajuster la logique de suppression")
        print("   - Modifier le code pour ignorer les tables manquantes")
        print("   - Ajouter des vérifications d'existence de table")
        
        print(f"\n🔧 Solution 3: Nettoyer les références obsolètes")
        print("   - Supprimer les références aux modèles non utilisés")
        print("   - Simplifier les dépendances")
    else:
        print("✅ Toutes les tables attendues existent")
        print("🔧 Le problème pourrait être ailleurs - vérifier les permissions ou la logique de suppression")

def main():
    """Fonction principale d'analyse"""
    
    print("=== Analyse de l'erreur de suppression de compte ===")
    
    # 1. Vérifier les tables
    existing_tables, missing_technical = check_competitions_tables()
    
    # 2. Analyser les dépendances
    referencing_models = check_practitioner_dependencies()
    
    # 3. Trouver les modèles techniques
    technical_models = find_technical_scoring_models()
    
    # 4. Vérifier les migrations
    migrations_output = check_migrations_status()
    
    # 5. Proposer des solutions
    propose_solutions(missing_technical)
    
    print(f"\n📊 Résumé:")
    print(f"  - Tables competitions: {len(existing_tables)}")
    print(f"  - Tables techniques manquantes: {len(missing_technical)}")
    print(f"  - Modèles référençant Practitioner: {len(referencing_models)}")
    print(f"  - Modèles techniques trouvés: {len(technical_models)}")
    
    return len(missing_technical) == 0

if __name__ == '__main__':
    success = main()
    print(f"\n{'🎉 Aucun problème détecté' if success else '⚠️ Problèmes détectés - correction nécessaire'}")
    sys.exit(0 if success else 1)