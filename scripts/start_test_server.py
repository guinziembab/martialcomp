#!/usr/bin/env python3
"""
Script pour démarrer le serveur de test avec SQLite
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import execute_from_command_line

def main():
    print("=" * 60)
    print("🚀 DÉMARRAGE DU SERVEUR DE TEST")
    print("=" * 60)
    print("Configuration:")
    print("   📊 Base de données: SQLite (db.sqlite3)")
    print("   🌐 Middleware tenant: Activé")
    print("   🎯 URL de test: http://fed-federation-test-fix.localhost:8000")
    print("   📋 Template attendu: organizations/sites/federation_template.html")
    print()
    print("⚠️  IMPORTANT:")
    print("   Configurez votre fichier hosts:")
    print("   127.0.0.1    fed-federation-test-fix.localhost")
    print()
    print("Appuyez sur Ctrl+C pour arrêter le serveur")
    print("=" * 60)
    
    # Démarrer le serveur Django
    sys.argv = ['manage.py', 'runserver', '0.0.0.0:8000']
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()