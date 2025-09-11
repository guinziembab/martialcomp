#!/usr/bin/env python3
"""
Script pour nettoyer les fichiers Python contenant des BOM (U+FEFF)
Utilisation: python clean_bom.py
"""

import os
import sys
from pathlib import Path

def remove_bom_from_file(file_path):
    """Supprime le BOM d'un fichier et le réenregistre sans BOM"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Vérifier si le fichier contient un BOM UTF-8
        if content.startswith(b'\xef\xbb\xbf'):
            print(f"🔍 BOM détecté dans: {file_path}")
            # Supprimer le BOM (3 premiers bytes)
            content = content[3:]
            
            # Réécrire le fichier sans BOM
            with open(file_path, 'wb') as f:
                f.write(content)
            print(f"✅ BOM supprimé de: {file_path}")
            return True
        else:
            print(f"✓ Aucun BOM trouvé dans: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du traitement de {file_path}: {e}")
        return False

def clean_directory(directory_path, extensions=['.py']):
    """Nettoie récursivement tous les fichiers Python d'un répertoire"""
    directory = Path(directory_path)
    files_cleaned = 0
    files_checked = 0
    
    print(f"🔄 Analyse du répertoire: {directory_path}")
    
    for file_path in directory.rglob('*'):
        try:
            # Éviter les dossiers .venv, __pycache__, .git, node_modules
            if any(part.startswith('.') or part == '__pycache__' or part == 'node_modules' 
                   for part in file_path.parts):
                continue
                
            if file_path.is_file() and file_path.suffix in extensions:
                files_checked += 1
                if remove_bom_from_file(file_path):
                    files_cleaned += 1
        except (OSError, PermissionError) as e:
            # Ignorer les erreurs d'accès aux liens symboliques ou permissions
            continue
    
    print(f"\n📊 Résumé:")
    print(f"   • Fichiers vérifiés: {files_checked}")
    print(f"   • Fichiers nettoyés: {files_cleaned}")
    
    return files_cleaned

def main():
    """Fonction principale"""
    print("🧹 Nettoyeur de BOM pour fichiers Python")
    print("=" * 50)
    
    # Fichier spécifique problématique
    problem_file = "apps/competitions/views/onboarding/club.py"
    
    if os.path.exists(problem_file):
        print(f"🎯 Traitement du fichier problématique: {problem_file}")
        remove_bom_from_file(problem_file)
        print()
    
    # Nettoyer tout le projet
    current_dir = os.getcwd()
    clean_directory(current_dir)
    
    print("\n🎉 Nettoyage terminé!")
    print("💡 Conseil: Configurez votre éditeur pour sauvegarder en UTF-8 sans BOM")

if __name__ == "__main__":
    main()