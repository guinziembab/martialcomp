#!/usr/bin/env python
"""
Script pour corriger les importations résiduelles de 'competitions.models.grades'
vers l'application 'grades'

Usage:
    python repair_imports.py

Ce script corrige automatiquement les importations dans le code source
et imprime les fichiers qui ont été modifiés.
"""

import os
import re
from pathlib import Path

# Configuration
BASE_DIR = Path('.')  # À la racine du projet
SEARCH_PATHS = ['competitions']
OLD_IMPORT_PATTERN = r'from competitions\.models\.grades import (.+)'
NEW_IMPORT_TEMPLATE = 'from grades.models import {}'

# Mappings pour les classes qui ont été renommées
CLASS_MAPPINGS = {
    'GradeSystem': 'GradeCategory',
    'PractitionerGradeHistory': 'PractitionerGrade',
}

def find_python_files():
    """Trouve tous les fichiers Python dans les chemins spécifiés."""
    python_files = []
    for search_path in SEARCH_PATHS:
        for root, _, files in os.walk(BASE_DIR / search_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
    return python_files

def contains_old_import(file_path):
    """Vérifie si le fichier contient l'ancien import."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        return re.search(OLD_IMPORT_PATTERN, content) is not None

def update_imports(file_path):
    """Met à jour les importations dans le fichier."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rechercher l'ancien pattern d'importation
    match = re.search(OLD_IMPORT_PATTERN, content)
    if not match:
        return False, "Aucun import ancien trouvé"
    
    # Extraire les classes importées
    imported_classes = [c.strip() for c in match.group(1).split(',')]
    
    # Préparer la nouvelle importation
    mapped_imports = []
    for class_name in imported_classes:
        if class_name in CLASS_MAPPINGS:
            mapped_imports.append(f"{CLASS_MAPPINGS[class_name]} as {class_name}")
        else:
            mapped_imports.append(class_name)
    
    new_import = NEW_IMPORT_TEMPLATE.format(', '.join(mapped_imports))
    
    # Remplacer l'importation
    content = re.sub(OLD_IMPORT_PATTERN, new_import, content)
    
    # Sauvegarder les modifications
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True, f"Import modifié: {', '.join(imported_classes)}"

def main():
    """Fonction principale du script."""
    print("🔍 Recherche des fichiers avec d'anciennes importations...")
    
    # Trouver tous les fichiers Python
    python_files = find_python_files()
    print(f"📁 {len(python_files)} fichiers Python trouvés à analyser.")
    
    # Trouver ceux avec d'anciennes imports
    files_with_old_imports = [f for f in python_files if contains_old_import(f)]
    
    if not files_with_old_imports:
        print("✅ Aucun fichier avec d'anciennes importations trouvé.")
        return
    
    print(f"🔧 {len(files_with_old_imports)} fichiers avec d'anciennes importations trouvés.")
    
    # Mettre à jour les imports
    updated_files = []
    for file_path in files_with_old_imports:
        success, message = update_imports(file_path)
        if success:
            updated_files.append(file_path)
            rel_path = os.path.relpath(file_path, BASE_DIR)
            print(f"✅ {rel_path}: {message}")
        else:
            rel_path = os.path.relpath(file_path, BASE_DIR)
            print(f"❌ {rel_path}: {message}")
    
    print(f"\n📊 Résumé: {len(updated_files)}/{len(files_with_old_imports)} fichiers mis à jour.")
    
    if updated_files:
        print("\n🔍 Fichiers modifiés:")
        for file_path in updated_files:
            rel_path = os.path.relpath(file_path, BASE_DIR)
            print(f"  - {rel_path}")

if __name__ == "__main__":
    main()