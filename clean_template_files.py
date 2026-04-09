#!/usr/bin/env python3
"""
Script pour nettoyer les fichiers .py dans les dossiers templates
qui causent des erreurs lors de makemessages
"""
import os
import sys
from pathlib import Path

# Dossiers à exclure
EXCLUDE_PATTERNS = [
    'production_complete',
    'production_transfer',
    'federation_fixes_backup',
    'federation_onboarding_patch',
    'onboarding_patch_production',
    'backups',
    'Backup',
    'Debug.bak',
    'Backup_Prod.bak',
    'node_modules',
    'mobile',
    'mobile_new',
    '.git',
    'venv',
    'env',
    '__pycache__',
]

# Dossiers templates Django à chercher
TEMPLATE_DIRS = [
    'apps/competitions/templates',
    'apps/family_management/templates',
    'apps/finances/templates',
    'apps/grades/templates',
    'apps/organizations/templates',
    'apps/shop/templates',
    'apps/documents/templates',
    'templates',
]

def is_excluded_path(file_path):
    """Vérifie si le fichier doit être exclu"""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)

def is_in_template_dir(file_path, root_dir):
    """Vérifie si le fichier est dans un dossier template Django"""
    path_str = str(file_path)
    rel_path = file_path.relative_to(root_dir)
    return any(rel_path.is_relative_to(Path(template_dir)) for template_dir in TEMPLATE_DIRS)

def find_template_py_files(root_dir):
    """Trouve tous les fichiers .py dans les dossiers templates Django"""
    template_py_files = []
    root = Path(root_dir)
    
    # Chercher tous les fichiers .html.py et .txt.py dans les dossiers templates
    for template_dir in TEMPLATE_DIRS:
        template_path = root / template_dir
        if template_path.exists():
            for ext in ['*.html.py', '*.txt.py']:
                for file_path in template_path.rglob(ext):
                    if not is_excluded_path(file_path):
                        template_py_files.append(file_path)
    
    # Chercher aussi les fichiers .txt.py à la racine
    for file_path in root.glob('*.txt.py'):
        if not is_excluded_path(file_path):
            template_py_files.append(file_path)
    
    return template_py_files

def main():
    root_dir = Path(__file__).parent
    print(f"🔍 Recherche des fichiers .py dans les dossiers templates...")
    print(f"   Répertoire racine: {root_dir}")
    print()
    
    template_files = find_template_py_files(root_dir)
    
    if not template_files:
        print("✅ Aucun fichier .py trouvé dans les dossiers templates (hors backups)")
        return 0
    
    print(f"📋 Trouvé {len(template_files)} fichier(s) .py dans les dossiers templates:")
    print()
    
    for file_path in sorted(template_files):
        print(f"   - {file_path.relative_to(root_dir)}")
    
    print()
    response = input("❓ Voulez-vous supprimer ces fichiers? (oui/non): ").strip().lower()
    
    if response in ['oui', 'o', 'yes', 'y']:
        deleted_count = 0
        for file_path in template_files:
            try:
                file_path.unlink()
                print(f"   ✅ Supprimé: {file_path.relative_to(root_dir)}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ Erreur lors de la suppression de {file_path.relative_to(root_dir)}: {e}")
        
        print()
        print(f"✅ {deleted_count} fichier(s) supprimé(s)")
        return 0
    else:
        print("❌ Suppression annulée")
        return 1

if __name__ == '__main__':
    sys.exit(main())
