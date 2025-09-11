#!/usr/bin/env python3
"""
Script d'aide au développement pour MartialComp
"""

import os
import subprocess
import sys
from pathlib import Path

def run_server():
    """Lance le serveur de développement"""
    print("🚀 Lancement du serveur de développement...")
    os.system('python manage.py runserver')

def run_migrations():
    """Exécute les migrations"""
    print("🔄 Exécution des migrations...")
    os.system('python manage.py makemigrations')
    os.system('python manage.py migrate')

def create_superuser():
    """Crée un superutilisateur"""
    print("👤 Création d'un superutilisateur...")
    os.system('python manage.py createsuperuser')

def load_initial_data():
    """Charge les données initiales"""
    print("📊 Chargement des données initiales...")
    commands = [
        'python manage.py load_disciplines',
        'python manage.py load_competition_types',
        'python manage.py initialize_grade_systems'
    ]
    
    for cmd in commands:
        print(f"Exécution: {cmd}")
        os.system(cmd)

def compile_translations():
    """Compile les traductions"""
    print("🌐 Compilation des traductions...")
    os.system('python manage.py compilemessages')

def check_project():
    """Vérifie l'état du projet"""
    print("🔍 Vérification du projet...")
    os.system('python manage.py check')

def show_menu():
    """Affiche le menu principal"""
    print("\n" + "="*50)
    print("🛡️  MARTIALCOMP - AIDE AU DÉVELOPPEMENT")
    print("="*50)
    print("1. 🚀 Lancer le serveur")
    print("2. 🔄 Exécuter les migrations")
    print("3. 👤 Créer un superutilisateur")
    print("4. 📊 Charger les données initiales")
    print("5. 🌐 Compiler les traductions")
    print("6. 🔍 Vérifier le projet")
    print("7. 🧹 Nettoyer le projet")
    print("8. 🇫🇷 Finaliser les traductions françaises")
    print("9. 📊 Statut du projet")
    print("0. ❌ Quitter")
    print("="*50)

def show_project_status():
    """Affiche le statut du projet"""
    print("\n📊 STATUT DU PROJET")
    print("="*30)
    
    # Vérifier le serveur
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
        if ':8000' in result.stdout:
            print("✅ Serveur Django: En cours (port 8000)")
        else:
            print("❌ Serveur Django: Arrêté")
    except:
        print("⚠️  Impossible de vérifier le serveur")
    
    # Vérifier les traductions
    po_file = Path('locale/fr/LC_MESSAGES/django.po')
    if po_file.exists():
        with open(po_file, 'r', encoding='utf-8') as f:
            content = f.read()
        total = content.count('msgid "')
        translated = content.count('msgstr "') - content.count('msgstr ""')
        print(f"🌐 Traductions françaises: {translated}/{total}")
    
    # Vérifier la base de données
    if Path('db.sqlite3').exists():
        size = Path('db.sqlite3').stat().st_size / (1024*1024)
        print(f"💾 Base de données: {size:.1f} MB")
    
    print("="*30)

def main():
    """Fonction principale"""
    while True:
        show_menu()
        
        try:
            choice = input("\nChoisissez une option (0-9): ").strip()
            
            if choice == '1':
                run_server()
            elif choice == '2':
                run_migrations()
            elif choice == '3':
                create_superuser()
            elif choice == '4':
                load_initial_data()
            elif choice == '5':
                compile_translations()
            elif choice == '6':
                check_project()
            elif choice == '7':
                os.system('python cleanup_project.py')
            elif choice == '8':
                os.system('python complete_french_translations.py')
            elif choice == '9':
                show_project_status()
            elif choice == '0':
                print("👋 Au revoir!")
                break
            else:
                print("❌ Option invalide")
                
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            break
        except Exception as e:
            print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main() 