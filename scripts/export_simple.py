#!/usr/bin/env python
"""
Script d'export simple avec gestion d'erreur
"""
import os
import sys

# Utilise les settings de base
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command

print("🚀 Export des données en cours...")

try:
    # Export simple par applications
    print("📊 Export des utilisateurs...")
    call_command('dumpdata', 'auth.User', '--output=users_export.json')
    
    print("🏢 Export des applications principales...")
    call_command('dumpdata', 'competitions', '--output=competitions_export.json')
    
    print("📋 Export des autres données...")
    call_command('dumpdata', 'multitenant', '--output=multitenant_export.json')
    
    print("✅ Export terminé en plusieurs fichiers")
    print("- users_export.json")
    print("- competitions_export.json") 
    print("- multitenant_export.json")
    
except Exception as e:
    print(f"❌ Erreur : {e}")
    print("Essayons un export plus simple...")
    
    try:
        # Export ultra-simple
        call_command('dumpdata', '--output=simple_export.json')
        print("✅ Export simple terminé : simple_export.json")
    except Exception as e2:
        print(f"❌ Erreur export simple : {e2}")