#!/usr/bin/env python
"""
Script simple pour compiler les fichiers .po en fichiers .mo 
sans avoir besoin des outils gettext.
"""

import os
import sys
import polib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def find_po_files():
    """Trouver tous les fichiers .po dans le répertoire locale."""
    po_files = []
    locale_dir = BASE_DIR / 'locale'
    
    for root, dirs, files in os.walk(locale_dir):
        for file in files:
            if file.endswith('.po'):
                po_files.append(os.path.join(root, file))
    
    return po_files

def compile_po_file(po_file_path):
    """Compiler un fichier .po en .mo."""
    try:
        # Charger le fichier .po
        po = polib.pofile(po_file_path)
        
        # Déterminer le chemin du fichier .mo
        mo_file_path = po_file_path.replace('.po', '.mo')
        
        # Compiler et enregistrer
        po.save_as_mofile(mo_file_path)
        
        print(f"Compilé avec succès: {po_file_path} -> {mo_file_path}")
        return True
    except Exception as e:
        print(f"Erreur lors de la compilation de {po_file_path}: {str(e)}")
        return False

def main():
    """Fonction principale."""
    # Vérifier si polib est installé
    try:
        import polib
    except ImportError:
        print("Erreur: Le module 'polib' n'est pas installé.")
        print("Installez-le avec: pip install polib")
        return 1
    
    # Trouver tous les fichiers .po
    po_files = find_po_files()
    if not po_files:
        print("Aucun fichier .po trouvé dans le répertoire 'locale'.")
        return 1
    
    # Compiler tous les fichiers
    success_count = 0
    for po_file in po_files:
        if compile_po_file(po_file):
            success_count += 1
    
    # Afficher le résumé
    print(f"\nCompilation terminée. {success_count}/{len(po_files)} fichiers compilés avec succès.")
    return 0

if __name__ == '__main__':
    sys.exit(main())