#!/usr/bin/env python3
"""
Script de démarrage Django avec configuration corrigée
"""

import os
import sys
import subprocess

def start_django():
    """Démarre Django avec les bonnes variables d'environnement"""
    
    # Configuration des variables d'environnement
    env = os.environ.copy()
    env.update({
        'DJANGO_SETTINGS_MODULE': 'config.settings.production',
        'DB_NAME': 'martialcomp_db',
        'DB_USER': 'martialcomp_user', 
        'DB_PASSWORD': 'AQWZSX123ok,',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    })
    
    # Changer vers le répertoire du projet
    os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')
    
    print("🚀 Démarrage de Django...")
    print("📁 Répertoire:", os.getcwd())
    print("⚙️ Settings:", env.get('DJANGO_SETTINGS_MODULE'))
    print("🗃️ Database:", f"{env.get('DB_USER')}@{env.get('DB_HOST')}:{env.get('DB_PORT')}/{env.get('DB_NAME')}")
    
    try:
        # Démarrer Django
        cmd = [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8080', '--noreload']
        print(f"▶️ Commande: {' '.join(cmd)}")
        
        subprocess.run(cmd, env=env, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt de Django")
        return True
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 DEMARRAGE DJANGO - CONFIGURATION CORRIGEE")
    print("=" * 50)
    start_django() 
"""
Script de démarrage Django avec configuration corrigée
"""

import os
import sys
import subprocess

def start_django():
    """Démarre Django avec les bonnes variables d'environnement"""
    
    # Configuration des variables d'environnement
    env = os.environ.copy()
    env.update({
        'DJANGO_SETTINGS_MODULE': 'config.settings.production',
        'DB_NAME': 'martialcomp_db',
        'DB_USER': 'martialcomp_user', 
        'DB_PASSWORD': 'AQWZSX123ok,',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    })
    
    # Changer vers le répertoire du projet
    os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')
    
    print("🚀 Démarrage de Django...")
    print("📁 Répertoire:", os.getcwd())
    print("⚙️ Settings:", env.get('DJANGO_SETTINGS_MODULE'))
    print("🗃️ Database:", f"{env.get('DB_USER')}@{env.get('DB_HOST')}:{env.get('DB_PORT')}/{env.get('DB_NAME')}")
    
    try:
        # Démarrer Django
        cmd = [sys.executable, 'manage.py', 'runserver', '0.0.0.0:8080', '--noreload']
        print(f"▶️ Commande: {' '.join(cmd)}")
        
        subprocess.run(cmd, env=env, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt de Django")
        return True
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("🔧 DEMARRAGE DJANGO - CONFIGURATION CORRIGEE")
    print("=" * 50)
    start_django() 