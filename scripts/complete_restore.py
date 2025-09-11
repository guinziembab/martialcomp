#!/usr/bin/env python3
"""
Script de restauration complète depuis le développement
"""

import os
import shutil
import subprocess
import time

def complete_restore():
    """Restaure complètement les fichiers de développement"""
    print("🚨 RESTAURATION COMPLÈTE DEPUIS LE DÉVELOPPEMENT")
    print("=" * 60)
    
    # Créer une sauvegarde de la production
    print("📦 Création d'une sauvegarde de production...")
    backup_dir = "/var/www/vhosts/martialcomp.com/httpdocs/backup_before_restore"
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    os.makedirs(backup_dir)
    
    # Sauvegarder les fichiers critiques
    critical_files = [
        'competitions/models/__init__.py',
        'config/settings/base.py',
        'config/translation_service.py',
        'complete_translations.py',
        'smart_translate.py',
        'fix_languages.py',
        'check_languages.py',
    ]
    
    for file_path in critical_files:
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        if os.path.exists(prod_path):
            backup_path = f"{backup_dir}/{file_path}"
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(prod_path, backup_path)
            print(f"📦 Sauvegardé: {file_path}")
    
    print("✅ Sauvegarde créée dans /backup_before_restore/")
    
    # Restaurer depuis le développement
    print("\n🔄 Restauration des fichiers de développement...")
    
    restored_count = 0
    for file_path in critical_files:
        dev_path = f"../{file_path}"
        prod_path = f"/var/www/vhosts/martialcomp.com/httpdocs/{file_path}"
        
        if os.path.exists(dev_path):
            try:
                # Créer le répertoire de destination si nécessaire
                os.makedirs(os.path.dirname(prod_path), exist_ok=True)
                
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

def restart_services():
    """Redémarre tous les services"""
    print("\n🔄 Redémarrage des services...")
    
    # Arrêter tous les processus gunicorn
    os.system("pkill -f gunicorn")
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre
    time.sleep(3)
    
    # Redémarrer gunicorn
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon"
    
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Gunicorn redémarré")
        
        # Attendre et vérifier
        time.sleep(5)
        check_cmd = "netstat -tlnp | grep :8002"
        check_result = os.system(check_cmd)
        
        if check_result == 0:
            print("✅ Gunicorn fonctionne sur le port 8002")
            return True
        else:
            print("❌ Gunicorn ne répond pas sur le port 8002")
            return False
    else:
        print("❌ Échec du redémarrage de gunicorn")
        return False

if __name__ == "__main__":
    print("🚨 SCRIPT DE RESTAURATION COMPLÈTE")
    print("=" * 60)
    
    # Restaurer les fichiers
    restore_ok = complete_restore()
    
    if restore_ok:
        # Redémarrer les services
        restart_ok = restart_services()
        
        if restart_ok:
            print("\n✅ RESTAURATION COMPLÈTE RÉUSSIE!")
            print("🌐 Testez maintenant l'interface admin")
            print("📦 Sauvegarde disponible dans /backup_before_restore/")
        else:
            print("\n⚠️ Fichiers restaurés mais problème avec gunicorn")
            print("🔧 Vérifiez les logs pour plus de détails")
    else:
        print("\n❌ ÉCHEC DE LA RESTAURATION")
        print("🔧 Vérifiez les permissions et l'espace disque") 