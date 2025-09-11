#!/usr/bin/env python
"""
Script pour extraire les chaînes de caractères à traduire et compiler les traductions.
Exécutez ce script depuis le répertoire racine du projet.
"""

import os
import subprocess
import sys
from pathlib import Path

# Récupérer le répertoire du projet
BASE_DIR = Path(__file__).resolve().parent

# Liste des langues prises en charge
LANGUAGES = [
    'fr',  # Français (langue par défaut)
    'en',  # Anglais
    'es',  # Espagnol
    'it',  # Italien
    'de',  # Allemand
    'no',  # Norvégien
    'ja',  # Japonais
    'zh',  # Chinois
    'hi',  # Hindi
    'ar',  # Arabe
    'sw',  # Swahili
    'am',  # Amharic
    'zu',  # Zulu
    'yo',  # Yoruba
    'pt',  # Portugais
    'ko',  # Coréen
]

def run_command(command):
    """Exécute une commande et affiche sa sortie."""
    print(f"Exécution de la commande : {' '.join(command)}")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {' '.join(command)}")
        print(f"Code de sortie: {e.returncode}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False

def extract_messages():
    """Extrait les messages à traduire pour toutes les langues."""
    print("Extraction des messages à traduire...")
    
    # Créer le répertoire locale s'il n'existe pas
    locale_dir = BASE_DIR / 'locale'
    os.makedirs(locale_dir, exist_ok=True)
    
    # Extraire les messages pour chaque langue
    for lang in LANGUAGES:
        # Créer le répertoire de la langue et de LC_MESSAGES s'ils n'existent pas
        lang_dir = locale_dir / lang / 'LC_MESSAGES'
        os.makedirs(lang_dir, exist_ok=True)
        
        # Extraire les messages pour cette langue
        success = run_command(['django-admin', 'makemessages', '-l', lang])
        if not success:
            print(f"Échec de l'extraction des messages pour la langue '{lang}'")

def compile_messages():
    """Compile les fichiers de traduction pour toutes les langues."""
    print("Compilation des messages...")
    success = run_command(['django-admin', 'compilemessages'])
    if not success:
        print("Échec de la compilation des messages")

def main():
    """Fonction principale."""
    # Vérifier si nous sommes dans le répertoire du projet
    if not os.path.exists('manage.py'):
        print("Erreur: Ce script doit être exécuté depuis le répertoire racine du projet.")
        return 1
    
    # Extraire et compiler les messages
    extract_messages()
    compile_messages()
    
    print("Terminé.")
    return 0

if __name__ == '__main__':
    sys.exit(main())