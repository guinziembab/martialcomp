#!/usr/bin/env python
"""
Script de migration et correction des importations pour la transition
de 'competitions.models.grades' vers l'application 'grades'

Utilisation:
    python migration_grades.py

Ce script effectue les actions suivantes:
1. Identifie les fichiers Python utilisant l'ancien module
2. Corrige les importations dans ces fichiers
3. Met à jour toutes les références aux classes renommées
"""

import os
import re
from pathlib import Path

# Configuration
PROJECT_ROOT = Path('.')  # Ajustez si nécessaire pour pointer vers la racine de votre projet
SEARCH_PATHS = [
    'competitions', 
    'martialcomp',
]
OLD_IMPORT = r'from competitions\.models\.grades import (.+)'
NEW_IMPORT_TEMPLATE = 'from grades.models import {}'

# Classes qui ont été renommées
CLASS_MAPPINGS = {
    'GradeSystem': 'GradeCategory',
    'PractitionerGradeHistory': 'PractitionerGrade',
}

def find_python_files():
    """Trouve tous les fichiers Python dans les chemins spécifiés."""
    python_files = []
    for search_path in SEARCH_PATHS:
        path = PROJECT_ROOT / search_path
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
    return python_files

def contains_old_import(file_path):
    """Vérifie si le fichier contient l'ancien import."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        return re.search(OLD_IMPORT, content) is not None

def update_file_imports(file_path):
    """Met à jour les importations dans le fichier."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rechercher les classes importées
    match = re.search(OLD_IMPORT, content)
    if not match:
        return False

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
    updated_content = re.sub(OLD_IMPORT, new_import, content)
    
    # Enregistrer les modifications
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return True

def main():
    """Point d'entrée principal du script."""
    python_files = find_python_files()
    files_with_old_imports = [f for f in python_files if contains_old_import(f)]
    
    print(f"Trouvé {len(files_with_old_imports)} fichiers avec d'anciennes importations:")
    for file_path in files_with_old_imports:
        print(f"- {file_path}")
        success = update_file_imports(file_path)
        if success:
            print(f"  ✅ Importations mises à jour")
        else:
            print(f"  ❌ Échec de la mise à jour")

if __name__ == "__main__":
    main()