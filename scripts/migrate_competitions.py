#!/usr/bin/env python3
"""
Script pour appliquer les migrations avec Django configuré
"""
import sys
import os

# Ajouter le chemin parent au sys.path
sys.path.insert(0, '/mnt/c/martial_hub_django/martialcomp')
sys.path.insert(0, '/mnt/c/martial_hub_django/venv/lib/python3.12/site-packages')

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    
    from django.core.management import execute_from_command_line
    
    # Appliquer les migrations
    print("Application des migrations pour competitions...")
    execute_from_command_line(['manage.py', 'migrate', 'competitions'])
    
    print("\n✓ Migrations appliquées avec succès !")
    
except ImportError:
    print("Erreur : Django n'est pas installé. Activez l'environnement virtuel.")
    sys.exit(1)
except Exception as e:
    print(f"Erreur : {e}")
    sys.exit(1)