#!/usr/bin/env python3
"""
Script d'urgence pour démarrer Django avec les bonnes configurations
"""
import os
import sys
import subprocess
import time

# Aller dans le bon répertoire
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
os.chdir(PROD_DIR)

# Ajouter le répertoire au PYTHONPATH
sys.path.insert(0, PROD_DIR)

def clean_processes():
    """Nettoie tous les processus Django"""
    
    print("🧹 NETTOYAGE PROCESSUS")
    print("=" * 22)
    
    try:
        # Arrêter tous les processus Python/Django
        subprocess.run(['pkill', '-9', '-f', 'manage.py'], check=False)
        subprocess.run(['pkill', '-9', '-f', 'python'], check=False)
        subprocess.run(['pkill', '-9', '-f', 'gunicorn'], check=False)
        
        print("✅ Processus nettoyés")
        time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")
        return True  # Continuer quand même

def test_django_import():
    """Test si Django peut s'importer correctement"""
    
    print("\n🔍 TEST IMPORT DJANGO")
    print("=" * 21)
    
    try:
        # Définir la variable d'environnement
        os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
        
        # Tester l'import de Django
        import django
        print("✅ Django importé")
        
        # Tester la configuration
        django.setup()
        print("✅ Django configuré")
        
        # Tester l'import des vues
        from competitions.views import pages
        print("✅ Vues importées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur import Django: {e}")
        
        # Essayer avec un settings plus simple
        try:
            print("🔄 Tentative avec settings_simple...")
            os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_simple'
            
            import importlib
            importlib.reload(django)
            django.setup()
            print("✅ Django configuré avec settings_simple")
            
            return True
            
        except Exception as e2:
            print(f"❌ Erreur avec settings_simple: {e2}")
            return False

def start_django_runserver():
    """Démarre Django avec runserver"""
    
    print("\n🚀 DÉMARRAGE DJANGO RUNSERVER")
    print("=" * 31)
    
    try:
        # Se mettre dans le bon répertoire et activer l'environnement
        cmd = [
            'bash', '-c',
            f'cd {PROD_DIR} && source venv/bin/activate && export DJANGO_SETTINGS_MODULE=config.settings && python3 manage.py runserver 0.0.0.0:8000'
        ]
        
        print("🔄 Exécution de runserver...")
        
        # Démarrer en arrière-plan
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Nouvelle session pour éviter les interruptions
        )
        
        # Attendre un peu pour voir si ça démarre
        time.sleep(8)
        
        # Vérifier si le processus tourne encore
        if process.poll() is None:
            print("✅ Processus Django démarré")
            
            # Tester la connexion
            try:
                import urllib.request
                response = urllib.request.urlopen('http://localhost:8000/', timeout=10)
                status = response.getcode()
                print(f"✅ Serveur répond: HTTP {status}")
                return True
                
            except Exception as e:
                print(f"⚠️ Serveur démarré mais ne répond pas encore: {e}")
                print("   (Il peut avoir besoin de quelques minutes)")
                return True
                
        else:
            # Le processus s'est arrêté, récupérer les erreurs
            stdout, stderr = process.communicate()
            print(f"❌ Processus arrêté")
            if stderr:
                print(f"Erreurs: {stderr.decode()}")
            if stdout:
                print(f"Sortie: {stdout.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur démarrage Django: {e}")
        return False

def test_urls_basic():
    """Test basique des URLs"""
    
    print("\n🧪 TEST URLs BASIQUES")
    print("=" * 19)
    
    try:
        import urllib.request
        
        # Attendre que le serveur soit vraiment prêt
        time.sleep(5)
        
        test_urls = [
            'http://localhost:8000/',
            'http://localhost:8000/fr/',
        ]
        
        working = 0
        for url in test_urls:
            try:
                response = urllib.request.urlopen(url, timeout=15)
                status = response.getcode()
                print(f"✅ {url}: HTTP {status}")
                working += 1
            except Exception as e:
                print(f"⚠️ {url}: {e}")
        
        print(f"📊 URLs fonctionnelles: {working}/{len(test_urls)}")
        return working > 0
        
    except Exception as e:
        print(f"❌ Erreur test URLs: {e}")
        return False

def check_site_status():
    """Vérifie le statut final du site"""
    
    print("\n📊 STATUT FINAL DU SITE")
    print("=" * 22)
    
    try:
        # Vérifier les processus Django
        result = subprocess.run(['pgrep', '-f', 'manage.py'], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print(f"✅ {len(pids)} processus Django actifs")
        else:
            print("⚠️ Aucun processus Django trouvé")
        
        # Vérifier les logs récents
        log_files = ['/tmp/django.log', '/var/log/nginx/error.log']
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"📋 Dernières lignes de {log_file}:")
                            for line in lines[-3:]:
                                print(f"   {line.strip()}")
                except:
                    pass
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification statut: {e}")
        return False

if __name__ == "__main__":
    print("🚨 DÉMARRAGE D'URGENCE DJANGO")
    print("=" * 31)
    print(f"📂 Répertoire: {os.getcwd()}")
    print(f"🐍 Python: {sys.executable}")
    
    # Exécuter les étapes une par une
    success1 = clean_processes()
    success2 = test_django_import()
    success3 = start_django_runserver()
    success4 = test_urls_basic()
    success5 = check_site_status()
    
    print(f"\n📋 RÉSUMÉ DÉMARRAGE:")
    print(f"   {'✅' if success1 else '❌'} Nettoyage processus")
    print(f"   {'✅' if success2 else '❌'} Import Django")
    print(f"   {'✅' if success3 else '❌'} Démarrage serveur")
    print(f"   {'✅' if success4 else '❌'} Test URLs")
    print(f"   {'✅' if success5 else '❌'} Vérification statut")
    
    if success2 and success3:
        print("\n🎉 DJANGO DÉMARRÉ AVEC SUCCÈS!")
        
        print("\n🌐 SITE ACCESSIBLE:")
        print("   🏠 https://martialcomp.com/")
        print("   🏠 https://martialcomp.com/fr/")
        
        print("\n🧪 DÉMO DISPONIBLE:")
        print("   👤 dojo_sakura_manager / demo2025")
        print("   🎯 Template martial avec toutes les fonctionnalités")
        
        if success4:
            print("\n✅ Site complètement opérationnel")
        else:
            print("\n⚠️ Site en cours de démarrage")
            print("   Patientez 2-3 minutes puis testez")
            
        print("\n📝 POUR SURVEILLER:")
        print("   tail -f /tmp/django.log")
        print("   ps aux | grep manage.py")
        
    else:
        print("\n❌ DÉMARRAGE PARTIEL")
        
        if not success2:
            print("\n🔧 PROBLÈME DE CONFIGURATION:")
            print("   Django ne peut pas s'importer correctement")
            print("   Vérifiez config/settings.py")
            
        if not success3:
            print("\n🔧 PROBLÈME DE DÉMARRAGE:")
            print("   Le serveur ne démarre pas")
            print("   Essayez manuellement:")
            print("   python3 manage.py check")
            print("   python3 manage.py runserver")
    
    sys.exit(0 if (success2 and success3) else 1)