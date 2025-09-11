#!/usr/bin/env python3
"""
Script de nettoyage pour MartialComp
Supprime les fichiers temporaires, de test et inutiles
"""
import os
import glob
import shutil
from pathlib import Path

def cleanup_files():
    """Nettoie les fichiers identifiés comme inutiles."""
    
    # Patterns de fichiers à supprimer
    patterns_to_delete = [
        # Scripts de test et utilitaires
        'test_*.py',
        '*_test.py',
        'debug_*.py',
        'fix_*.py',
        'emergency_*.py',
        'quick_*.py',
        'final_*.py',
        'diagnose_*.py',
        'analyze_*.py',
        'investigate_*.py',
        'verify_*.py',
        'check_*.py',
        'copy_*.py',
        'setup_*.py',
        'start_*.py',
        'run_*.py',
        'migrate_*.py',
        'backup_*.py',
        'restore_*.py',
        'sync_*.py',
        'translate_*.py',
        'align_*.py',
        'extract_*.py',
        'add_*.py',
        'remove_*.py',
        'clean_*.py',
        'find_*.py',
        'compare_*.py',
        'generate_*.py',
        'create_*.py',
        'populate_*.py',
        'initialize_*.py',
        'list_*.py',
        'search_*.py',
        'ultra_fast_*.py',
        'simple_*.py',
        'auto_*.py',
        'fast_*.py',
        
        # Fichiers HTML temporaires
        'martialcomp-business-model*.html',
        'martialcomp-features-form.html',
        
        # Fichiers de données temporaires
        'translation_progress_*.json',
        'project_inventory.csv',
        'po_analysis_report.json',
        'new_languages_report.json',
        'quick_translation_update_report.json',
        
        # Fichiers de configuration temporaires
        'fix_postgres_password.sql',
        'reset_db_password.sh',
        'correct_settings.sh',
        'fix_settings.py',
        'production.env',
        'requirements_updated.txt',
        
        # Fichiers de test spécifiques
        'test_onboarding_organisateur_non_membre.py',
        'test_email_system.py',
        'test_combat_namespace.py',
        'test_combat_urls.py',
        'setup_local_hosts.py',
        
        # Fichiers de traduction temporaires
        'update_all_po_from_en.py',
        'update_italian_po.py',
        'fix_grades_imports.py',
        'duplicate_en_po_to_all_languages.py',
        'extract_footer_to_en_po.py',
        'align_po_en_with_it.py',
        'align_po_it_with_en.py',
        'add_missing_footer_po_entries.py',
        'remove_po_duplicates_it.py',
        'add_missing_welcome_po_entries.py',
        'extract_trans_fields_from_welcome.py',
        'search_welcome_text_in_po.py',
        'align_italian_to_english.py',
        'align_po_with_italian.py',
        'find_missing_msgid.py',
        'compare_po_msgid_count.py',
        'check_po_translation.py',
        'translate_other_languages.py',
        'fix_italian_po.py',
        'ultra_fast_translate.py',
        'fast_translate_po.py',
        'simple_google_translate_po.py',
        'auto_translate_po_improved.py',
        'test_language_selector.py',
        'generate_and_translate_po.py',
        'clean_po_duplicates.py',
        'sync_po_translations.py',
        'add_new_languages.py',
        'quick_translation_update.py',
        'extract_translations_manual.py',
        'extract_and_update_translations.py',
        'compile_po_messages.py',
        'analyze_po_project.py',
        'add_english_translations.py',
        
        # Fichiers de migration temporaires
        'migration_0011.sql',
        
        # Fichiers de documentation temporaires
        '*.md',
        'GUIDE_*.md',
        'README_*.md',
        'IMPLEMENTATION_*.md',
        'FEATURE_*.md',
        'NEW_LANGUAGES_*.md',
        'TRANSLATION_*.md',
        'EMAIL_SYSTEM_*.md',
        'certificate-implementation-guide.md',
        
        # Fichiers de configuration temporaires
        'package_competition_structure.yaml',
        
        # Fichiers d'inventaire temporaires
        'project_inventory.*',
        'generate_project_inventory.py',
        
        # Fichiers de test de combat
        'test_combat_*.py',
        
        # Fichiers de test d'email
        'test_email_*.py',
        
        # Fichiers de configuration locale
        'setup_local_hosts.py',
        'GUIDE_HOSTS_WINDOWS.md',
        'GUIDE_TEST_LOCAL.md',
        
        # Fichiers de test d'import
        'fix_imports.py',
        'fix_grades_imports.py',
        
        # Fichiers de test de namespace
        'test_combat_namespace.py',
        'test_combat_urls.py',
    ]
    
    # Répertoires à exclure
    exclude_dirs = {
        '.git', '.venv', 'env', 'node_modules', '__pycache__', 
        'staticfiles', 'media', 'migrations', 'locale', 'scripts'
    }
    
    deleted_files = []
    total_size_freed = 0
    
    print("Debut du nettoyage MartialComp...")
    print("=" * 60)
    
    for pattern in patterns_to_delete:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            # Vérifier si le fichier est dans un répertoire à exclure
            if not any(exclude in file for exclude in exclude_dirs):
                file_path = Path(file)
                if file_path.exists():
                    try:
                        size = file_path.stat().st_size
                        file_path.unlink()  # Supprimer le fichier
                        deleted_files.append({
                            'path': str(file_path),
                            'size_mb': size / (1024 * 1024)
                        })
                        total_size_freed += size
                        print(f"Supprime: {file_path} ({size / (1024 * 1024):.2f} MB)")
                    except Exception as e:
                        print(f"Erreur lors de la suppression de {file_path}: {e}")
    
    # Nettoyer les répertoires vides
    print("\nNettoyage des repertoires vides...")
    for root, dirs, files in os.walk('.', topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"Repertoire vide supprime: {dir_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression du repertoire {dir_path}: {e}")
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"NETTOYAGE TERMINE!")
    print(f"Fichiers supprimes: {len(deleted_files)}")
    print(f"Espace libere: {total_size_freed / (1024 * 1024):.2f} MB")
    print("=" * 60)
    
    return deleted_files, total_size_freed

if __name__ == "__main__":
    deleted_files, total_size_freed = cleanup_files() 
"""
Script de nettoyage pour MartialComp
Supprime les fichiers temporaires, de test et inutiles
"""
import os
import glob
import shutil
from pathlib import Path

def cleanup_files():
    """Nettoie les fichiers identifiés comme inutiles."""
    
    # Patterns de fichiers à supprimer
    patterns_to_delete = [
        # Scripts de test et utilitaires
        'test_*.py',
        '*_test.py',
        'debug_*.py',
        'fix_*.py',
        'emergency_*.py',
        'quick_*.py',
        'final_*.py',
        'diagnose_*.py',
        'analyze_*.py',
        'investigate_*.py',
        'verify_*.py',
        'check_*.py',
        'copy_*.py',
        'setup_*.py',
        'start_*.py',
        'run_*.py',
        'migrate_*.py',
        'backup_*.py',
        'restore_*.py',
        'sync_*.py',
        'translate_*.py',
        'align_*.py',
        'extract_*.py',
        'add_*.py',
        'remove_*.py',
        'clean_*.py',
        'find_*.py',
        'compare_*.py',
        'generate_*.py',
        'create_*.py',
        'populate_*.py',
        'initialize_*.py',
        'list_*.py',
        'search_*.py',
        'ultra_fast_*.py',
        'simple_*.py',
        'auto_*.py',
        'fast_*.py',
        
        # Fichiers HTML temporaires
        'martialcomp-business-model*.html',
        'martialcomp-features-form.html',
        
        # Fichiers de données temporaires
        'translation_progress_*.json',
        'project_inventory.csv',
        'po_analysis_report.json',
        'new_languages_report.json',
        'quick_translation_update_report.json',
        
        # Fichiers de configuration temporaires
        'fix_postgres_password.sql',
        'reset_db_password.sh',
        'correct_settings.sh',
        'fix_settings.py',
        'production.env',
        'requirements_updated.txt',
        
        # Fichiers de test spécifiques
        'test_onboarding_organisateur_non_membre.py',
        'test_email_system.py',
        'test_combat_namespace.py',
        'test_combat_urls.py',
        'setup_local_hosts.py',
        
        # Fichiers de traduction temporaires
        'update_all_po_from_en.py',
        'update_italian_po.py',
        'fix_grades_imports.py',
        'duplicate_en_po_to_all_languages.py',
        'extract_footer_to_en_po.py',
        'align_po_en_with_it.py',
        'align_po_it_with_en.py',
        'add_missing_footer_po_entries.py',
        'remove_po_duplicates_it.py',
        'add_missing_welcome_po_entries.py',
        'extract_trans_fields_from_welcome.py',
        'search_welcome_text_in_po.py',
        'align_italian_to_english.py',
        'align_po_with_italian.py',
        'find_missing_msgid.py',
        'compare_po_msgid_count.py',
        'check_po_translation.py',
        'translate_other_languages.py',
        'fix_italian_po.py',
        'ultra_fast_translate.py',
        'fast_translate_po.py',
        'simple_google_translate_po.py',
        'auto_translate_po_improved.py',
        'test_language_selector.py',
        'generate_and_translate_po.py',
        'clean_po_duplicates.py',
        'sync_po_translations.py',
        'add_new_languages.py',
        'quick_translation_update.py',
        'extract_translations_manual.py',
        'extract_and_update_translations.py',
        'compile_po_messages.py',
        'analyze_po_project.py',
        'add_english_translations.py',
        
        # Fichiers de migration temporaires
        'migration_0011.sql',
        
        # Fichiers de documentation temporaires
        '*.md',
        'GUIDE_*.md',
        'README_*.md',
        'IMPLEMENTATION_*.md',
        'FEATURE_*.md',
        'NEW_LANGUAGES_*.md',
        'TRANSLATION_*.md',
        'EMAIL_SYSTEM_*.md',
        'certificate-implementation-guide.md',
        
        # Fichiers de configuration temporaires
        'package_competition_structure.yaml',
        
        # Fichiers d'inventaire temporaires
        'project_inventory.*',
        'generate_project_inventory.py',
        
        # Fichiers de test de combat
        'test_combat_*.py',
        
        # Fichiers de test d'email
        'test_email_*.py',
        
        # Fichiers de configuration locale
        'setup_local_hosts.py',
        'GUIDE_HOSTS_WINDOWS.md',
        'GUIDE_TEST_LOCAL.md',
        
        # Fichiers de test d'import
        'fix_imports.py',
        'fix_grades_imports.py',
        
        # Fichiers de test de namespace
        'test_combat_namespace.py',
        'test_combat_urls.py',
    ]
    
    # Répertoires à exclure
    exclude_dirs = {
        '.git', '.venv', 'env', 'node_modules', '__pycache__', 
        'staticfiles', 'media', 'migrations', 'locale', 'scripts'
    }
    
    deleted_files = []
    total_size_freed = 0
    
    print("Debut du nettoyage MartialComp...")
    print("=" * 60)
    
    for pattern in patterns_to_delete:
        files = glob.glob(pattern, recursive=True)
        for file in files:
            # Vérifier si le fichier est dans un répertoire à exclure
            if not any(exclude in file for exclude in exclude_dirs):
                file_path = Path(file)
                if file_path.exists():
                    try:
                        size = file_path.stat().st_size
                        file_path.unlink()  # Supprimer le fichier
                        deleted_files.append({
                            'path': str(file_path),
                            'size_mb': size / (1024 * 1024)
                        })
                        total_size_freed += size
                        print(f"Supprime: {file_path} ({size / (1024 * 1024):.2f} MB)")
                    except Exception as e:
                        print(f"Erreur lors de la suppression de {file_path}: {e}")
    
    # Nettoyer les répertoires vides
    print("\nNettoyage des repertoires vides...")
    for root, dirs, files in os.walk('.', topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    print(f"Repertoire vide supprime: {dir_path}")
            except Exception as e:
                print(f"Erreur lors de la suppression du repertoire {dir_path}: {e}")
    
    # Résumé
    print("\n" + "=" * 60)
    print(f"NETTOYAGE TERMINE!")
    print(f"Fichiers supprimes: {len(deleted_files)}")
    print(f"Espace libere: {total_size_freed / (1024 * 1024):.2f} MB")
    print("=" * 60)
    
    return deleted_files, total_size_freed

if __name__ == "__main__":
    deleted_files, total_size_freed = cleanup_files() 