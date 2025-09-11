#!/usr/bin/env python
import os
import re
import sys
from pathlib import Path

"""
Script pour mettre à jour les références à l'application 'grades' dans les fichiers Python et HTML
de l'application 'competitions'.

Ce script:
1. Parcourt tous les fichiers .py et .html dans le répertoire 'competitions'
2. Met à jour les imports de modules/classes depuis 'grades'
3. Corrige les références aux URLs 'grades'
4. Sauvegarde une copie de chaque fichier modifié avec une extension .bak
"""

# Configuration
COMPETITIONS_DIR = 'competitions'  # Répertoire de l'application competitions
BACKUP_EXTENSION = '.bak'          # Extension pour les fichiers de sauvegarde
DRY_RUN = False                    # Mode simulation (True) ou modification réelle (False)

# Motifs à remplacer dans les fichiers Python
PYTHON_PATTERNS = [
    # Import patterns
    (r'from competitions\.models\.grades import', r'from grades.models import'),
    (r'from competitions\.forms\.grades import', r'from grades.forms import'),
    (r'from competitions\.views\.grades import', r'from grades.views import'),
    
    # Import specific models, forms, or views
    (r'from competitions\.(models|forms|views) import .*?(Grade\w*)', r'from grades.\1 import \2'),
    
    # Direct model references
    (r'competitions\.models\.grades\.', r'grades.models.'),
    
    # Namespace references in reverse/resolve
    (r'reverse\([\'"]competitions:grades:', r'reverse([\'"]grades:'),
    (r'resolve\([\'"]competitions:grades:', r'resolve([\'"]grades:'),
    (r'reverse_lazy\([\'"]competitions:grades:', r'reverse_lazy([\'"]grades:'),
]

# Motifs à remplacer dans les fichiers HTML
HTML_PATTERNS = [
    # URL tags
    (r'{%\s*url\s+[\'"]competitions:grades:', r'{% url \'grades:'),
    (r'{%\s*url\s+[\'"]competitions:club_management[\'"]', r'{% url \'grades:club_management\''),
    (r'{%\s*url\s+[\'"]competitions:club:grade', r'{% url \'grades:'),
    
    # Autres références potentielles
    (r'competitions:grades:', r'grades:'),
    (r'competitions:club:grades:', r'grades:'),
]

def should_process_file(file_path):
    """Vérifie si le fichier doit être traité."""
    # Exclure les fichiers de sauvegarde et les fichiers dans __pycache__
    if file_path.endswith(BACKUP_EXTENSION) or '__pycache__' in file_path:
        return False
    # Exclure les fichiers de migration
    if '/migrations/' in file_path:
        return False
    # Traiter uniquement les fichiers Python et HTML
    return file_path.endswith(('.py', '.html'))

def backup_file(file_path):
    """Crée une sauvegarde du fichier."""
    backup_path = f"{file_path}{BACKUP_EXTENSION}"
    try:
        # Vérifier si une sauvegarde existe déjà
        if os.path.exists(backup_path):
            i = 1
            while os.path.exists(f"{backup_path}.{i}"):
                i += 1
            backup_path = f"{backup_path}.{i}"
        
        # Copier le contenu du fichier original
        with open(file_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        return True
    except Exception as e:
        print(f"Erreur lors de la sauvegarde de {file_path}: {str(e)}")
        return False

def process_file(file_path):
    """Traite un fichier pour remplacer les motifs."""
    try:
        # Lire le contenu du fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Appliquer les remplacements selon le type de fichier
        patterns = PYTHON_PATTERNS if file_path.endswith('.py') else HTML_PATTERNS
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Si le contenu a été modifié et qu'on n'est pas en mode simulation
        if content != original_content:
            if DRY_RUN:
                print(f"[SIMULATION] Modifications à appliquer dans {file_path}")
                return True
            else:
                # Créer une sauvegarde avant de modifier
                if backup_file(file_path):
                    # Écrire le contenu modifié
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✅ Fichier mis à jour: {file_path}")
                    return True
        else:
            print(f"ℹ️ Aucune modification nécessaire: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {file_path}: {str(e)}")
        return False

def get_all_files(directory):
    """Retourne tous les fichiers à traiter dans le répertoire spécifié."""
    files_to_process = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if should_process_file(file_path):
                files_to_process.append(file_path)
    return files_to_process

def main():
    """Fonction principale."""
    # Déterminer le chemin de base
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    competitions_dir = os.path.join(base_dir, COMPETITIONS_DIR)
    
    # Vérifier si le répertoire existe
    if not os.path.isdir(competitions_dir):
        print(f"Le répertoire '{competitions_dir}' n'existe pas.")
        competitions_dir = input("Veuillez entrer le chemin complet du répertoire de l'application competitions: ")
        if not os.path.isdir(competitions_dir):
            print(f"Le répertoire '{competitions_dir}' n'existe pas non plus. Arrêt du script.")
            sys.exit(1)
    
    print(f"Mode: {'SIMULATION' if DRY_RUN else 'MODIFICATION RÉELLE'}")
    print(f"Traitement des fichiers dans: {competitions_dir}")
    
    # Récupérer tous les fichiers à traiter
    files = get_all_files(competitions_dir)
    print(f"Nombre de fichiers à traiter: {len(files)}")
    
    # Traiter chaque fichier
    modified_files = 0
    for file_path in files:
        if process_file(file_path):
            modified_files += 1
    
    # Afficher un résumé
    print(f"\nRésumé:")
    print(f"Fichiers traités: {len(files)}")
    print(f"Fichiers modifiés: {modified_files}")
    
    if DRY_RUN:
        print("\nCe script a été exécuté en mode SIMULATION.")
        print("Aucune modification n'a été apportée aux fichiers.")
        print("Pour appliquer les modifications, définissez DRY_RUN = False dans le script.")

if __name__ == "__main__":
    main()