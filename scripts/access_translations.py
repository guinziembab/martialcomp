#!/usr/bin/env python3
"""
Script pour accéder facilement aux traductions
"""
import subprocess
import sys
import time

def start_server():
    """Démarre le serveur Django"""
    print("🚀 DÉMARRAGE DU SERVEUR DJANGO")
    print("=" * 50)
    
    try:
        # Utiliser settings_minimal pour éviter les problèmes de middleware
        cmd = [sys.executable, "manage.py", "runserver", "0.0.0.0:8000", "--settings=config.settings_minimal"]
        
        print("Commande exécutée:")
        print(" ".join(cmd))
        print()
        
        print("🌍 URLS D'ACCÈS AUX TRADUCTIONS:")
        print("=" * 50)
        print("• Interface Rosetta:     http://localhost:8000/rosetta/")
        print("• Dashboard traductions: http://localhost:8000/admin/translations/dashboard/")
        print("• Admin Django:          http://localhost:8000/admin/")
        print("• Page d'accueil:        http://localhost:8000/")
        print()
        
        print("🔐 AUTHENTIFICATION:")
        print("• Créer un superuser: python3 manage.py createsuperuser")
        print("• Se connecter avec vos identifiants admin")
        print()
        
        print("📝 INSTRUCTIONS:")
        print("1. Laissez ce serveur tourner")
        print("2. Ouvrez http://localhost:8000/rosetta/ dans votre navigateur")
        print("3. Connectez-vous avec un compte admin")
        print("4. Gérez vos traductions dans l'interface web")
        print()
        
        print("Appuyez sur Ctrl+C pour arrêter le serveur")
        print("=" * 50)
        
        # Démarrer le serveur
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n👋 Serveur arrêté")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\nEssayez avec la commande manuelle:")
        print("python3 manage.py runserver 0.0.0.0:8000")

if __name__ == '__main__':
    start_server()