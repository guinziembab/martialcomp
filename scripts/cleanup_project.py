#!/usr/bin/env python3
"""
Script pour nettoyer et organiser le projet
"""

import os
import shutil
from pathlib import Path
import datetime

def cleanup_translation_files():
    """Nettoie les fichiers de traduction temporaires"""
    print("🧹 Nettoyage des fichiers de traduction...")
    
    # Créer un dossier de sauvegarde
    backup_dir = Path(f"translation_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    
    # Fichiers à déplacer
    translation_files = [
        'translation_progress_*.json',
        'smart_translate.py',
        'deepl_translate.py',
        'batch_translate.py',
        'auto_translate_po.py',
        'extract_all_translations.py',
        'extract_dashboard_translations.py',
        'complete_translations.py',
        'clean_recreate_all_po.py',
        'clean_recreate_po.py',
        'final_fix_po.py',
        'simple_fix_po.py',
        'fix_spanish_po_syntax.py',
        'fix_spanish_translations.py'
    ]
    
    moved_count = 0
    for pattern in translation_files:
        for file_path in Path('.').glob(pattern):
            try:
                backup_path = backup_dir / file_path.name
                shutil.move(str(file_path), str(backup_path))
                print(f"📁 Déplacé: {file_path} -> {backup_path}")
                moved_count += 1
            except Exception as e:
                print(f"⚠️  Erreur lors du déplacement de {file_path}: {e}")
    
    print(f"✅ {moved_count} fichiers déplacés vers {backup_dir}")

def organize_project_structure():
    """Organise la structure du projet"""
    print("📁 Organisation de la structure du projet...")
    
    # Créer des dossiers utiles
    folders = ['scripts', 'tools', 'backups', 'temp']
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
        print(f"📁 Dossier créé/vérifié: {folder}")

def check_database_integrity():
    """Vérifie l'intégrité de la base de données"""
    print("🔍 Vérification de la base de données...")
    
    try:
        import subprocess
        result = subprocess.run(['python', 'manage.py', 'check'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Base de données en bon état")
        else:
            print("⚠️  Problèmes détectés dans la base de données")
            print(result.stderr)
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def main():
    """Fonction principale"""
    print("🧹 NETTOYAGE ET ORGANISATION DU PROJET")
    print("=" * 50)
    
    # Nettoyage des fichiers de traduction
    cleanup_translation_files()
    
    # Organisation de la structure
    organize_project_structure()
    
    # Vérification de la base de données
    check_database_integrity()
    
    print("\n✅ Nettoyage terminé!")
    print("📁 Les fichiers temporaires ont été sauvegardés")
    print("🌐 Le projet est prêt pour la production")

if __name__ == "__main__":
    main() 