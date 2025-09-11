#!/usr/bin/env python3
"""
Script de nettoyage final et redémarrage stable de Django
Nettoie tous les caches et redémarre avec une configuration figée
"""

import os
import sys
import subprocess
import shutil
import signal
import time

def run_command(cmd, check=True):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 Exécution: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(f"✅ Sortie: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️ Erreur: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec: {e}")
        if not check:
            return None
        raise

def cleanup_django():
    """Nettoyage complet de Django"""
    print("🧹 === NETTOYAGE COMPLET DJANGO ===")
    
    # 1. Arrêter tous les processus Django
    print("1. Arrêt des processus Django...")
    run_command("pkill -f 'python3.*manage.py' || true", check=False)
    run_command("pkill -f 'django' || true", check=False)
    time.sleep(2)
    
    # 2. Nettoyer tous les __pycache__
    print("2. Nettoyage des caches Python...")
    run_command("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true", check=False)
    run_command("find . -name '*.pyc' -delete 2>/dev/null || true", check=False)
    
    # 3. Nettoyer les logs Django
    print("3. Nettoyage des logs...")
    run_command("rm -f django.log* 2>/dev/null || true", check=False)
    run_command("rm -f nohup.out 2>/dev/null || true", check=False)
    
    # 4. Vérifier les variables d'environnement
    print("4. Nettoyage des variables d'environnement...")
    env_vars = ['DJANGO_SETTINGS_MODULE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"   Supprimé: {var}")

def verify_production_settings():
    """Vérifier que production.py est correct"""
    print("🔍 === VÉRIFICATION PRODUCTION.PY ===")
    
    settings_file = "config/settings/production.py"
    if not os.path.exists(settings_file):
        print(f"❌ Fichier {settings_file} manquant!")
        return False
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Vérifications critiques
    checks = [
        ("DATABASES", "martialcomp_user"),
        ("ALLOWED_HOSTS", "martialcomp.com"),
        ("DEBUG = False", "DEBUG = False")
    ]
    
    for check_name, check_content in checks:
        if check_content in content:
            print(f"✅ {check_name}: OK")
        else:
            print(f"❌ {check_name}: MANQUANT")
            return False
    
    return True

def start_django_stable():
    """Démarrer Django avec configuration stable"""
    print("🚀 === DÉMARRAGE DJANGO STABLE ===")
    
    # Commande de démarrage avec tous les paramètres explicites
    cmd = [
        "python3", "manage.py", "runserver", "0.0.0.0:8080", "--noreload",
        "--settings=config.settings.production"
    ]
    
    # Variables d'environnement explicites
    env = os.environ.copy()
    env.update({
        'DJANGO_SETTINGS_MODULE': 'config.settings.production',
        'PYTHONPATH': '/var/www/vhosts/martialcomp.com/httpdocs',
        'PYTHONUNBUFFERED': '1'
    })
    
    print(f"🔧 Commande: {' '.join(cmd)}")
    print("🔧 Variables d'environnement:")
    for key, value in env.items():
        if key.startswith('DJANGO') or key.startswith('PYTHON'):
            print(f"   {key}={value}")
    
    try:
        # Démarrer Django
        process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        print("⏳ Démarrage en cours...")
        
        # Attendre et afficher les premiers logs
        start_time = time.time()
        while time.time() - start_time < 30:  # Timeout de 30 secondes
            line = process.stdout.readline()
            if line:
                print(f"📝 {line.strip()}")
                if "Starting development server" in line:
                    print("✅ Django démarré avec succès!")
                    break
                elif "Error" in line or "Traceback" in line:
                    print("❌ Erreur au démarrage!")
                    break
            time.sleep(0.1)
        
        # Vérifier si le processus est toujours actif
        if process.poll() is None:
            print("✅ Django est en cours d'exécution")
            print(f"🔧 PID: {process.pid}")
            return True
        else:
            print("❌ Django s'est arrêté")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 === NETTOYAGE FINAL ET REDÉMARRAGE DJANGO ===")
    
    # Vérifier le répertoire de travail
    if not os.path.exists("manage.py"):
        print("❌ manage.py non trouvé. Vérifiez le répertoire de travail.")
        sys.exit(1)
    
    try:
        # 1. Nettoyage complet
        cleanup_django()
        
        # 2. Vérification des paramètres
        if not verify_production_settings():
            print("❌ Paramètres de production incorrects!")
            sys.exit(1)
        
        # 3. Démarrage stable
        if start_django_stable():
            print("🎉 === SUCCÈS: DJANGO REDÉMARRÉ ===")
            print("🌐 Testez maintenant: http://martialcomp.com")
        else:
            print("❌ === ÉCHEC: PROBLÈME AU DÉMARRAGE ===")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
"""
Script de nettoyage final et redémarrage stable de Django
Nettoie tous les caches et redémarre avec une configuration figée
"""

import os
import sys
import subprocess
import shutil
import signal
import time

def run_command(cmd, check=True):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 Exécution: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(f"✅ Sortie: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️ Erreur: {result.stderr.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec: {e}")
        if not check:
            return None
        raise

def cleanup_django():
    """Nettoyage complet de Django"""
    print("🧹 === NETTOYAGE COMPLET DJANGO ===")
    
    # 1. Arrêter tous les processus Django
    print("1. Arrêt des processus Django...")
    run_command("pkill -f 'python3.*manage.py' || true", check=False)
    run_command("pkill -f 'django' || true", check=False)
    time.sleep(2)
    
    # 2. Nettoyer tous les __pycache__
    print("2. Nettoyage des caches Python...")
    run_command("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true", check=False)
    run_command("find . -name '*.pyc' -delete 2>/dev/null || true", check=False)
    
    # 3. Nettoyer les logs Django
    print("3. Nettoyage des logs...")
    run_command("rm -f django.log* 2>/dev/null || true", check=False)
    run_command("rm -f nohup.out 2>/dev/null || true", check=False)
    
    # 4. Vérifier les variables d'environnement
    print("4. Nettoyage des variables d'environnement...")
    env_vars = ['DJANGO_SETTINGS_MODULE', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"   Supprimé: {var}")

def verify_production_settings():
    """Vérifier que production.py est correct"""
    print("🔍 === VÉRIFICATION PRODUCTION.PY ===")
    
    settings_file = "config/settings/production.py"
    if not os.path.exists(settings_file):
        print(f"❌ Fichier {settings_file} manquant!")
        return False
    
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Vérifications critiques
    checks = [
        ("DATABASES", "martialcomp_user"),
        ("ALLOWED_HOSTS", "martialcomp.com"),
        ("DEBUG = False", "DEBUG = False")
    ]
    
    for check_name, check_content in checks:
        if check_content in content:
            print(f"✅ {check_name}: OK")
        else:
            print(f"❌ {check_name}: MANQUANT")
            return False
    
    return True

def start_django_stable():
    """Démarrer Django avec configuration stable"""
    print("🚀 === DÉMARRAGE DJANGO STABLE ===")
    
    # Commande de démarrage avec tous les paramètres explicites
    cmd = [
        "python3", "manage.py", "runserver", "0.0.0.0:8080", "--noreload",
        "--settings=config.settings.production"
    ]
    
    # Variables d'environnement explicites
    env = os.environ.copy()
    env.update({
        'DJANGO_SETTINGS_MODULE': 'config.settings.production',
        'PYTHONPATH': '/var/www/vhosts/martialcomp.com/httpdocs',
        'PYTHONUNBUFFERED': '1'
    })
    
    print(f"🔧 Commande: {' '.join(cmd)}")
    print("🔧 Variables d'environnement:")
    for key, value in env.items():
        if key.startswith('DJANGO') or key.startswith('PYTHON'):
            print(f"   {key}={value}")
    
    try:
        # Démarrer Django
        process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        print("⏳ Démarrage en cours...")
        
        # Attendre et afficher les premiers logs
        start_time = time.time()
        while time.time() - start_time < 30:  # Timeout de 30 secondes
            line = process.stdout.readline()
            if line:
                print(f"📝 {line.strip()}")
                if "Starting development server" in line:
                    print("✅ Django démarré avec succès!")
                    break
                elif "Error" in line or "Traceback" in line:
                    print("❌ Erreur au démarrage!")
                    break
            time.sleep(0.1)
        
        # Vérifier si le processus est toujours actif
        if process.poll() is None:
            print("✅ Django est en cours d'exécution")
            print(f"🔧 PID: {process.pid}")
            return True
        else:
            print("❌ Django s'est arrêté")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 === NETTOYAGE FINAL ET REDÉMARRAGE DJANGO ===")
    
    # Vérifier le répertoire de travail
    if not os.path.exists("manage.py"):
        print("❌ manage.py non trouvé. Vérifiez le répertoire de travail.")
        sys.exit(1)
    
    try:
        # 1. Nettoyage complet
        cleanup_django()
        
        # 2. Vérification des paramètres
        if not verify_production_settings():
            print("❌ Paramètres de production incorrects!")
            sys.exit(1)
        
        # 3. Démarrage stable
        if start_django_stable():
            print("🎉 === SUCCÈS: DJANGO REDÉMARRÉ ===")
            print("🌐 Testez maintenant: http://martialcomp.com")
        else:
            print("❌ === ÉCHEC: PROBLÈME AU DÉMARRAGE ===")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Interruption par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 