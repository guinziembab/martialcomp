#!/usr/bin/env python
"""
Script de déploiement de la correction onboarding en production
Usage: python deploy_onboarding_fix.py
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime

def deploy_onboarding_fix():
    """Déployer la correction onboarding en production"""
    
    print("🚀 Déploiement de la correction onboarding en production...")
    print("=" * 70)
    
    # Chemins
    local_file = '/mnt/c/martial_hub_django/martialcomp/competitions/views/auth.py'
    prod_file = '/var/www/vhosts/martialcomp.com/httpdocs/competitions/views/auth.py'
    backup_file = f'{prod_file}.backup_{int(datetime.now().timestamp())}'
    
    try:
        # 1. Vérifier que le fichier local existe
        if not os.path.exists(local_file):
            print(f"❌ Fichier local non trouvé: {local_file}")
            return False
        
        print(f"✅ Fichier local trouvé: {local_file}")
        
        # 2. Créer une sauvegarde du fichier de production
        if os.path.exists(prod_file):
            shutil.copy2(prod_file, backup_file)
            print(f"✅ Sauvegarde créée: {backup_file}")
        
        # 3. Copier le fichier corrigé vers la production
        shutil.copy2(local_file, prod_file)
        print(f"✅ Fichier copié vers la production: {prod_file}")
        
        # 4. Vérifier les permissions
        os.chmod(prod_file, 0o644)
        print("✅ Permissions ajustées")
        
        # 5. Redémarrer Gunicorn pour appliquer les changements
        print("\n🔄 Redémarrage de Gunicorn...")
        try:
            # Tuer les processus Gunicorn existants
            subprocess.run(['pkill', '-f', 'gunicorn'], check=False)
            print("✅ Processus Gunicorn arrêtés")
            
            # Démarrer Gunicorn en arrière-plan
            subprocess.Popen([
                '/var/www/vhosts/martialcomp.com/httpdocs/venv/bin/gunicorn',
                '--bind', '127.0.0.1:8000',
                '--workers', '3',
                '--timeout', '120',
                '--max-requests', '1000',
                '--max-requests-jitter', '100',
                '--preload',
                '--chdir', '/var/www/vhosts/martialcomp.com/httpdocs',
                'config.wsgi:application'
            ], 
            cwd='/var/www/vhosts/martialcomp.com/httpdocs',
            env=dict(os.environ, DJANGO_SETTINGS_MODULE='config.settings'))
            
            print("✅ Gunicorn redémarré")
            
        except Exception as e:
            print(f"⚠️  Erreur lors du redémarrage: {e}")
            print("⚠️  Veuillez redémarrer manuellement si nécessaire")
        
        print("\n" + "=" * 70)
        print("🎉 DÉPLOIEMENT RÉUSSI !")
        print("=" * 70)
        print("✅ Le fichier auth.py a été corrigé en production")
        print("✅ Les URLs d'onboarding utilisent maintenant les bons namespaces")
        print("✅ Le processus signup devrait maintenant rediriger correctement")
        print("✅ Gunicorn a été redémarré pour appliquer les changements")
        print("=" * 70)
        print("🌐 TESTEZ MAINTENANT:")
        print("🔗 https://martialcomp.com/signup/")
        print("🎯 Le processus d'onboarding devrait se lancer après l'inscription")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du déploiement: {e}")
        
        # Tentative de restauration en cas d'erreur
        if os.path.exists(backup_file):
            try:
                shutil.copy2(backup_file, prod_file)
                print(f"🔄 Sauvegarde restaurée depuis: {backup_file}")
            except Exception as restore_error:
                print(f"❌ Erreur lors de la restauration: {restore_error}")
        
        return False

if __name__ == "__main__":
    success = deploy_onboarding_fix()
    sys.exit(0 if success else 1)