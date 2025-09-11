#!/usr/bin/env python3
"""
Script pour transférer les fichiers de développement vers la production
"""

import os
import shutil
import subprocess
import time

def identify_critical_files():
    """Identifie les fichiers critiques à transférer"""
    print("🔍 IDENTIFICATION DES FICHIERS CRITIQUES")
    print("=" * 50)
    
    # Fichiers critiques à transférer depuis le développement
    critical_files = [
        'competitions/models/__init__.py',
        'config/wsgi.py',
        'config/settings/base.py',
        'config/settings/production.py',
        'gunicorn.conf.py',
        'config/translation_service.py',
    ]
    
    print("📋 FICHIERS CRITIQUES À TRANSFÉRER:")
    for file_path in critical_files:
        print(f"   - {file_path}")
    
    return critical_files

def backup_production_files():
    """Sauvegarde les fichiers de production avant transfert"""
    print("\n📦 SAUVEGARDE DES FICHIERS DE PRODUCTION")
    print("=" * 40)
    
    backup_dir = "/var/www/vhosts/martialcomp.com/httpdocs/backup_before_dev_transfer"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'competitions/models/__init__.py',
        'config/wsgi.py',
        'config/settings/base.py',
        'config/settings/production.py',
        'gunicorn.conf.py',
        'config/translation_service.py',
    ]
    
    for file_path in files_to_backup:
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        if os.path.exists(prod_path):
            backup_path = f"{backup_dir}/{file_path.replace('/', '_')}"
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(prod_path, backup_path)
            print(f"✅ Sauvegardé: {file_path}")
    
    print(f"📦 Sauvegarde complète dans: {backup_dir}")
    return True

def transfer_dev_files():
    """Transfère les fichiers de développement vers la production"""
    print("\n🔄 TRANSFERT DES FICHIERS DE DÉVELOPPEMENT")
    print("=" * 40)
    
    # Fichiers à transférer (chemin relatif depuis le répertoire scripts)
    files_to_transfer = [
        '../competitions/models/__init__.py',
        '../config/wsgi.py',
        '../config/settings/base.py',
        '../config/settings/production.py',
        '../gunicorn.conf.py',
        '../config/translation_service.py',
    ]
    
    transferred_count = 0
    
    for dev_file in files_to_transfer:
        # Chemin complet du fichier de développement
        dev_path = os.path.abspath(dev_file)
        # Chemin de destination en production
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{dev_file[3:]}"
        
        if os.path.exists(dev_path):
            try:
                # Créer le répertoire de destination si nécessaire
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                
                # Copier le fichier
                shutil.copy2(dev_path, prod_path)
                print(f"✅ Transféré: {dev_file[3:]}")
                transferred_count += 1
                
            except Exception as e:
                print(f"❌ Erreur avec {dev_file}: {e}")
        else:
            print(f"⚠️ Fichier de développement non trouvé: {dev_path}")
    
    return transferred_count

def adapt_production_settings():
    """Adapte les paramètres pour la production"""
    print("\n🔧 ADAPTATION DES PARAMÈTRES POUR LA PRODUCTION")
    print("=" * 50)
    
    # Adapter le fichier wsgi.py pour la production
    wsgi_path = "/var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py"
    
    if os.path.exists(wsgi_path):
        with open(wsgi_path, 'r') as f:
            content = f.read()
        
        # Remplacer les settings de développement par la production
        if 'config.settings.development' in content:
            content = content.replace('config.settings.development', 'config.settings.production')
            with open(wsgi_path, 'w') as f:
                f.write(content)
            print("✅ Settings adaptés pour la production")
    
    # Adapter gunicorn.conf.py pour le port 8002
    gunicorn_path = "/var/www/vhosts/martialcomp.com/httpdocs/gunicorn.conf.py"
    
    if os.path.exists(gunicorn_path):
        with open(gunicorn_path, 'r') as f:
            content = f.read()
        
        # Remplacer le port 8001 par 8002
        if '127.0.0.1:8001' in content:
            content = content.replace('127.0.0.1:8001', '127.0.0.1:8002')
            with open(gunicorn_path, 'w') as f:
                f.write(content)
            print("✅ Port gunicorn adapté pour 8002")
    
    return True

def test_django_import():
    """Teste l'import Django après transfert"""
    print("\n🔍 TEST DE L'IMPORT DJANGO")
    print("=" * 30)
    
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/python -c 'import config.wsgi; print(\"✅ Application Django importée avec succès\")'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Application Django OK")
            print(result.stdout)
            return True
        else:
            print("❌ Erreur d'import Django:")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - import Django")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def restart_gunicorn():
    """Redémarre gunicorn après transfert"""
    print("\n🔄 REDÉMARRAGE DE GUNICORN")
    print("=" * 30)
    
    # Arrêter gunicorn
    subprocess.run(["pkill", "-f", "gunicorn"])
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application --daemon"
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
        
        if ":8002" in check_result.stdout:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🔄 TRANSFERT DÉVELOPPEMENT VERS PRODUCTION")
    print("=" * 60)
    
    # Identifier les fichiers critiques
    critical_files = identify_critical_files()
    
    # Sauvegarder les fichiers de production
    backup_ok = backup_production_files()
    
    if backup_ok:
        # Transférer les fichiers de développement
        transferred_count = transfer_dev_files()
        
        if transferred_count > 0:
            # Adapter les paramètres pour la production
            adapt_ok = adapt_production_settings()
            
            if adapt_ok:
                # Tester l'import Django
                django_ok = test_django_import()
                
                if django_ok:
                    # Redémarrer gunicorn
                    restart_ok = restart_gunicorn()
                    
                    if restart_ok:
                        print("\n✅ TRANSFERT RÉUSSI!")
                        print("🌐 Gunicorn fonctionne sur le port 8002")
                        print("🌐 Testez maintenant l'interface admin")
                        print("📦 Sauvegarde disponible dans: /var/www/vhosts/martialcomp.com/httpdocs/backup_before_dev_transfer")
                    else:
                        print("\n⚠️ Transfert réussi mais problème avec gunicorn")
                else:
                    print("\n❌ Problème avec l'import Django après transfert")
            else:
                print("\n❌ Problème avec l'adaptation des paramètres")
        else:
            print("\n❌ Aucun fichier transféré")
    else:
        print("\n❌ ÉCHEC DE LA SAUVEGARDE") 
"""
Script pour transférer les fichiers de développement vers la production
"""

import os
import shutil
import subprocess
import time

def identify_critical_files():
    """Identifie les fichiers critiques à transférer"""
    print("🔍 IDENTIFICATION DES FICHIERS CRITIQUES")
    print("=" * 50)
    
    # Fichiers critiques à transférer depuis le développement
    critical_files = [
        'competitions/models/__init__.py',
        'config/wsgi.py',
        'config/settings/base.py',
        'config/settings/production.py',
        'gunicorn.conf.py',
        'config/translation_service.py',
    ]
    
    print("📋 FICHIERS CRITIQUES À TRANSFÉRER:")
    for file_path in critical_files:
        print(f"   - {file_path}")
    
    return critical_files

def backup_production_files():
    """Sauvegarde les fichiers de production avant transfert"""
    print("\n📦 SAUVEGARDE DES FICHIERS DE PRODUCTION")
    print("=" * 40)
    
    backup_dir = "/var/www/vhosts/martialcomp.com/httpdocs/backup_before_dev_transfer"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'competitions/models/__init__.py',
        'config/wsgi.py',
        'config/settings/base.py',
        'config/settings/production.py',
        'gunicorn.conf.py',
        'config/translation_service.py',
    ]
    
    for file_path in files_to_backup:
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        if os.path.exists(prod_path):
            backup_path = f"{backup_dir}/{file_path.replace('/', '_')}"
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(prod_path, backup_path)
            print(f"✅ Sauvegardé: {file_path}")
    
    print(f"📦 Sauvegarde complète dans: {backup_dir}")
    return True

def transfer_dev_files():
    """Transfère les fichiers de développement vers la production"""
    print("\n🔄 TRANSFERT DES FICHIERS DE DÉVELOPPEMENT")
    print("=" * 40)
    
    # Fichiers à transférer (chemin relatif depuis le répertoire scripts)
    files_to_transfer = [
        '../competitions/models/__init__.py',
        '../config/wsgi.py',
        '../config/settings/base.py',
        '../config/settings/production.py',
        '../gunicorn.conf.py',
        '../config/translation_service.py',
    ]
    
    transferred_count = 0
    
    for dev_file in files_to_transfer:
        # Chemin complet du fichier de développement
        dev_path = os.path.abspath(dev_file)
        # Chemin de destination en production
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{dev_file[3:]}"
        
        if os.path.exists(dev_path):
            try:
                # Créer le répertoire de destination si nécessaire
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                
                # Copier le fichier
                shutil.copy2(dev_path, prod_path)
                print(f"✅ Transféré: {dev_file[3:]}")
                transferred_count += 1
                
            except Exception as e:
                print(f"❌ Erreur avec {dev_file}: {e}")
        else:
            print(f"⚠️ Fichier de développement non trouvé: {dev_path}")
    
    return transferred_count

def adapt_production_settings():
    """Adapte les paramètres pour la production"""
    print("\n🔧 ADAPTATION DES PARAMÈTRES POUR LA PRODUCTION")
    print("=" * 50)
    
    # Adapter le fichier wsgi.py pour la production
    wsgi_path = "/var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py"
    
    if os.path.exists(wsgi_path):
        with open(wsgi_path, 'r') as f:
            content = f.read()
        
        # Remplacer les settings de développement par la production
        if 'config.settings.development' in content:
            content = content.replace('config.settings.development', 'config.settings.production')
            with open(wsgi_path, 'w') as f:
                f.write(content)
            print("✅ Settings adaptés pour la production")
    
    # Adapter gunicorn.conf.py pour le port 8002
    gunicorn_path = "/var/www/vhosts/martialcomp.com/httpdocs/gunicorn.conf.py"
    
    if os.path.exists(gunicorn_path):
        with open(gunicorn_path, 'r') as f:
            content = f.read()
        
        # Remplacer le port 8001 par 8002
        if '127.0.0.1:8001' in content:
            content = content.replace('127.0.0.1:8001', '127.0.0.1:8002')
            with open(gunicorn_path, 'w') as f:
                f.write(content)
            print("✅ Port gunicorn adapté pour 8002")
    
    return True

def test_django_import():
    """Teste l'import Django après transfert"""
    print("\n🔍 TEST DE L'IMPORT DJANGO")
    print("=" * 30)
    
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/python -c 'import config.wsgi; print(\"✅ Application Django importée avec succès\")'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Application Django OK")
            print(result.stdout)
            return True
        else:
            print("❌ Erreur d'import Django:")
            print(f"Code de retour: {result.returncode}")
            print(f"Erreur: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - import Django")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def restart_gunicorn():
    """Redémarre gunicorn après transfert"""
    print("\n🔄 REDÉMARRAGE DE GUNICORN")
    print("=" * 30)
    
    # Arrêter gunicorn
    subprocess.run(["pkill", "-f", "gunicorn"])
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn -c gunicorn.conf.py config.wsgi:application --daemon"
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_result = subprocess.run(["netstat", "-tlnp"], capture_output=True, text=True)
        
        if ":8002" in check_result.stdout:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🔄 TRANSFERT DÉVELOPPEMENT VERS PRODUCTION")
    print("=" * 60)
    
    # Identifier les fichiers critiques
    critical_files = identify_critical_files()
    
    # Sauvegarder les fichiers de production
    backup_ok = backup_production_files()
    
    if backup_ok:
        # Transférer les fichiers de développement
        transferred_count = transfer_dev_files()
        
        if transferred_count > 0:
            # Adapter les paramètres pour la production
            adapt_ok = adapt_production_settings()
            
            if adapt_ok:
                # Tester l'import Django
                django_ok = test_django_import()
                
                if django_ok:
                    # Redémarrer gunicorn
                    restart_ok = restart_gunicorn()
                    
                    if restart_ok:
                        print("\n✅ TRANSFERT RÉUSSI!")
                        print("🌐 Gunicorn fonctionne sur le port 8002")
                        print("🌐 Testez maintenant l'interface admin")
                        print("📦 Sauvegarde disponible dans: /var/www/vhosts/martialcomp.com/httpdocs/backup_before_dev_transfer")
                    else:
                        print("\n⚠️ Transfert réussi mais problème avec gunicorn")
                else:
                    print("\n❌ Problème avec l'import Django après transfert")
            else:
                print("\n❌ Problème avec l'adaptation des paramètres")
        else:
            print("\n❌ Aucun fichier transféré")
    else:
        print("\n❌ ÉCHEC DE LA SAUVEGARDE") 