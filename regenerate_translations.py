#!/usr/bin/env python
import os
import subprocess
import sys

# Activer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.conf import settings
from django.core.management import call_command

def main():
    print("=== Régénération des traductions ===")
    
    # Créer les dossiers locale si nécessaire
    for lang_code, _ in settings.LANGUAGES:
        locale_dir = os.path.join('locale', lang_code, 'LC_MESSAGES')
        os.makedirs(locale_dir, exist_ok=True)
        print(f"✓ Dossier créé/vérifié: {locale_dir}")
    
    # Traiter une langue à la fois
    for lang_code, lang_name in settings.LANGUAGES:
        if lang_code == 'fr':
            continue  # Le français est la langue source
            
        print(f"\nTraitement de {lang_name} ({lang_code})...")
        
        try:
            # Utiliser une commande plus simple
            cmd = [
                sys.executable,
                'manage.py',
                'makemessages',
                '-l', lang_code,
                '--no-wrap',
                '--no-obsolete',
                '--ignore=mobile/*',
                '--ignore=venv*',
                '--ignore=backups/*',
                '--ignore=*.tar.gz',
                '--ignore=*.zip',
                '--ignore=temp_*',
                '--ignore=__pycache__',
                '--ignore=staticfiles/*',
                '--ignore=media/*'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                print(f"✓ {lang_name} traité avec succès")
            else:
                print(f"✗ Erreur pour {lang_name}:")
                print(result.stderr)
                
        except subprocess.TimeoutExpired:
            print(f"✗ Timeout pour {lang_name}")
        except Exception as e:
            print(f"✗ Erreur inattendue pour {lang_name}: {e}")
    
    print("\n=== Compilation des messages ===")
    try:
        call_command('compilemessages')
        print("✓ Messages compilés avec succès")
    except Exception as e:
        print(f"✗ Erreur lors de la compilation: {e}")

if __name__ == '__main__':
    main()