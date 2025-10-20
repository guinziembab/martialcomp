#!/usr/bin/env python3
"""
Script de connexion à la production MartialComp
Vérifie la connectivité et l'état du système
"""

import os
import sys
import subprocess
import requests
import time
from datetime import datetime

def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)

def print_step(step, description):
    """Affiche une étape"""
    print(f"\n{step} {description}")
    print("-" * 40)

def check_server_environment():
    """Vérifie l'environnement du serveur"""
    print_step("1️⃣", "Vérification de l'environnement serveur")
    
    # Vérifier qu'on est sur le serveur de production
    if not os.path.exists("/var/www/vhosts/martialcomp.com/httpdocs"):
        print("❌ Ce script doit être exécuté sur le serveur de production")
        print("   Répertoire attendu: /var/www/vhosts/martialcomp.com/httpdocs")
        return False
    
    print("✅ Répertoire de production trouvé")
    
    # Vérifier l'environnement virtuel
    venv_path = "/var/www/vhosts/martialcomp.com/venv"
    if os.path.exists(venv_path):
        print("✅ Environnement virtuel trouvé")
    else:
        print("⚠️ Environnement virtuel non trouvé")
    
    # Vérifier les fichiers de configuration
    config_files = [
        "/var/www/vhosts/martialcomp.com/httpdocs/config/settings/production.py",
        "/var/www/vhosts/martialcomp.com/httpdocs/passenger_wsgi.py",
        "/var/www/vhosts/martialcomp.com/httpdocs/.env.production"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ {os.path.basename(config_file)} trouvé")
        else:
            print(f"⚠️ {os.path.basename(config_file)} manquant")
    
    return True

def check_database_connection():
    """Teste la connexion à la base de données"""
    print_step("2️⃣", "Test de connexion à la base de données PostgreSQL")
    
    try:
        # Changer vers le répertoire du projet
        os.chdir("/var/www/vhosts/martialcomp.com/httpdocs")
        
        # Activer l'environnement virtuel
        venv_python = "/var/www/vhosts/martialcomp.com/venv/bin/python"
        if not os.path.exists(venv_python):
            print("❌ Python de l'environnement virtuel non trouvé")
            return False
        
        # Exécuter le script de test de base de données
        result = subprocess.run([
            venv_python, 
            "/var/www/vhosts/martialcomp.com/httpdocs/scripts/test_database_connection.py"
        ], capture_output=True, text=True, timeout=30)
        
        print("📊 Résultat du test de base de données:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Erreurs:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Timeout lors du test de base de données")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test de base de données: {e}")
        return False

def check_service_status():
    """Vérifie le statut du service MartialComp"""
    print_step("3️⃣", "Vérification du statut du service")
    
    try:
        # Vérifier le service systemd
        result = subprocess.run([
            "systemctl", "is-active", "martialcomp.service"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Service MartialComp actif")
        else:
            print("❌ Service MartialComp inactif")
            print("📋 Détails du service:")
            subprocess.run(["systemctl", "status", "martialcomp.service", "--no-pager"])
            return False
        
        # Vérifier les processus
        result = subprocess.run([
            "ps", "aux", "|", "grep", "martialcomp"
        ], shell=True, capture_output=True, text=True)
        
        if "martialcomp" in result.stdout:
            print("✅ Processus MartialComp détectés")
            print("📋 Processus actifs:")
            for line in result.stdout.split('\n')[:3]:
                if line.strip():
                    print(f"   {line}")
        else:
            print("⚠️ Aucun processus MartialComp détecté")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du service: {e}")
        return False

def check_web_connectivity():
    """Teste la connectivité web"""
    print_step("4️⃣", "Test de connectivité web")
    
    urls_to_test = [
        "https://martialcomp.com",
        "https://martialcomp.com/fr/",
        "https://martialcomp.com/admin/",
        "https://martialcomp.com/fr/competitions/"
    ]
    
    success_count = 0
    
    for url in urls_to_test:
        try:
            print(f"🌐 Test de {url}...")
            response = requests.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                print(f"   ✅ {response.status_code} - OK")
                success_count += 1
            elif response.status_code in [301, 302]:
                print(f"   ⚠️ {response.status_code} - Redirection vers {response.headers.get('Location', 'Unknown')}")
                success_count += 1
            else:
                print(f"   ❌ {response.status_code} - Erreur")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Erreur de connexion")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print(f"\n📊 Connectivité: {success_count}/{len(urls_to_test)} URLs accessibles")
    return success_count > 0

def check_logs():
    """Vérifie les logs récents"""
    print_step("5️⃣", "Vérification des logs récents")
    
    log_files = [
        "/var/log/django/martialcomp.log",
        "/var/log/apache2/error.log",
        "/var/log/apache2/access.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📋 {os.path.basename(log_file)}:")
            try:
                # Afficher les 5 dernières lignes
                result = subprocess.run([
                    "tail", "-5", log_file
                ], capture_output=True, text=True)
                
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        print(f"   {line}")
                else:
                    print("   (fichier vide)")
                    
            except Exception as e:
                print(f"   ❌ Erreur lecture: {e}")
        else:
            print(f"⚠️ {os.path.basename(log_file)} non trouvé")

def restart_service():
    """Redémarre le service si nécessaire"""
    print_step("6️⃣", "Redémarrage du service (si nécessaire)")
    
    try:
        print("🔄 Redémarrage du service MartialComp...")
        result = subprocess.run([
            "sudo", "systemctl", "restart", "martialcomp.service"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Service redémarré avec succès")
            
            # Attendre un peu
            print("⏳ Attente du démarrage...")
            time.sleep(5)
            
            # Vérifier le statut
            result = subprocess.run([
                "systemctl", "is-active", "martialcomp.service"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Service actif après redémarrage")
                return True
            else:
                print("❌ Service inactif après redémarrage")
                return False
        else:
            print(f"❌ Erreur lors du redémarrage: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du redémarrage: {e}")
        return False

def main():
    """Fonction principale"""
    print_header("CONNEXION À LA PRODUCTION MARTIALCOMP")
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vérifications
    checks = {
        "Environnement": check_server_environment(),
        "Base de données": check_database_connection(),
        "Service": check_service_status(),
        "Web": check_web_connectivity()
    }
    
    # Afficher les logs
    check_logs()
    
    # Résumé
    print_header("RÉSUMÉ DE LA CONNEXION")
    
    all_good = True
    for check_name, status in checks.items():
        if status:
            print(f"✅ {check_name}: OK")
        else:
            print(f"❌ {check_name}: PROBLÈME")
            all_good = False
    
    if not all_good:
        print("\n🔧 ACTIONS RECOMMANDÉES:")
        
        if not checks["Service"]:
            print("• Redémarrer le service: sudo systemctl restart martialcomp.service")
        
        if not checks["Web"]:
            print("• Vérifier la configuration Apache")
            print("• Vérifier les certificats SSL")
        
        if not checks["Base de données"]:
            print("• Vérifier la connexion PostgreSQL")
            print("• Vérifier les variables d'environnement")
        
        # Proposer un redémarrage
        print("\n🔄 Voulez-vous redémarrer le service? (y/N): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes', 'oui']:
                restart_service()
        except KeyboardInterrupt:
            print("\n👋 Annulé par l'utilisateur")
    else:
        print("\n🎉 TOUT FONCTIONNE CORRECTEMENT!")
        print("🌐 Site accessible: https://martialcomp.com")
        print("🔐 Admin: https://martialcomp.com/admin/")
    
    print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()