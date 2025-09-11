#!/usr/bin/env python3
"""
Script pour restaurer les fichiers de développement vers la production
"""

import os
import shutil
import subprocess

def restore_files():
    """Restaure les fichiers de développement vers la production"""
    print("🔄 Restauration des fichiers de développement...")
    
    # Fichiers critiques à restaurer
    critical_files = [
        'competitions/models/__init__.py',
        'config/settings/base.py',
        'config/translation_service.py',
    ]
    
    restored_count = 0
    
    for file_path in critical_files:
        dev_path = f"../{file_path}"
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        
        if os.path.exists(dev_path):
            try:
                # Créer une sauvegarde
                backup_path = f"{prod_path}.backup_before_restore"
                if os.path.exists(prod_path):
                    shutil.copy2(prod_path, backup_path)
                    print(f"📦 Sauvegarde créée: {backup_path}")
                
                # Copier le fichier de développement
                shutil.copy2(dev_path, prod_path)
                print(f"✅ Restauré: {file_path}")
                restored_count += 1
                
            except Exception as e:
                print(f"❌ Erreur avec {file_path}: {e}")
        else:
            print(f"⚠️ Fichier de développement non trouvé: {dev_path}")
    
    print(f"\n📊 Résumé: {restored_count} fichiers restaurés")
    return restored_count > 0

def restart_gunicorn():
    """Redémarre gunicorn après restauration"""
    print("\n🔄 Redémarrage de gunicorn...")
    
    # Arrêter gunicorn
    os.system("pkill -f gunicorn")
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    import time
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon"
    
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Gunicorn redémarré")
        return True
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🚀 RESTAURATION DEPUIS LE DÉVELOPPEMENT")
    print("=" * 50)
    
    # Restaurer les fichiers
    restore_ok = restore_files()
    
    if restore_ok:
        # Redémarrer gunicorn
        restart_ok = restart_gunicorn()
        
        if restart_ok:
            print("\n✅ RESTAURATION RÉUSSIE!")
            print("🌐 Testez maintenant l'interface admin")
        else:
            print("\n⚠️ Fichiers restaurés mais problème avec gunicorn")
    else:
        print("\n❌ ÉCHEC DE LA RESTAURATION") 