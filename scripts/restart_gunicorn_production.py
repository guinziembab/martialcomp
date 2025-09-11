#!/usr/bin/env python3
"""
Script simple pour redémarrer gunicorn en production
"""

import os
import subprocess
import time

def restart_gunicorn():
    """Redémarre gunicorn proprement"""
    print("🔄 Redémarrage de gunicorn en production...")
    
    # Arrêter tous les processus gunicorn
    os.system("pkill -f gunicorn")
    print("✅ Processus gunicorn arrêtés")
    
    # Attendre un peu
    time.sleep(3)
    
    # Redémarrer gunicorn sur le port 8002
    cmd = "cd /var/www/vhosts/martialcomp.com/httpdocs && sudo -u www-data .venv/bin/gunicorn --bind 127.0.0.1:8002 --workers 2 --timeout 30 --access-logfile logs/gunicorn_access.log --error-logfile logs/gunicorn_error.log --log-level info config.wsgi:application --daemon"
    
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Gunicorn redémarré avec succès")
        
        # Attendre un peu et vérifier
        time.sleep(5)
        
        # Vérifier que gunicorn fonctionne
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
    print("🚀 SCRIPT DE REDÉMARRAGE GUNICORN")
    print("=" * 40)
    
    success = restart_gunicorn()
    
    if success:
        print("\n✅ REDÉMARRAGE RÉUSSI!")
        print("🌐 Testez maintenant l'interface admin")
    else:
        print("\n❌ ÉCHEC DU REDÉMARRAGE")
        print("🔧 Vérifiez les logs pour plus de détails") 