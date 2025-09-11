#!/usr/bin/env python3
"""
Script final de démarrage Django - Configuration forcée et stable
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def start_django_final():
    """Démarre Django avec configuration forcée"""
    
    # Changer vers le répertoire du projet
    os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')
    
    # Configuration Django FORCÉE - ne dépend d'AUCUNE variable d'environnement
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
    
    print("🚀 DÉMARRAGE DJANGO FINAL")
    print("=" * 50)
    print(f"📁 Répertoire: {os.getcwd()}")
    print(f"⚙️ Settings: {os.environ['DJANGO_SETTINGS_MODULE']}")
    
    # Ajouter le répertoire au path Python
    sys.path.insert(0, os.getcwd())
    
    try:
        # Configuration Django
        django.setup()
        
        print("✅ Django configuré avec succès")
        
        # Vérifier la configuration de base de données
        from django.conf import settings
        db_config = settings.DATABASES['default']
        print(f"🗃️ Base de données configurée:")
        print(f"   - ENGINE: {db_config['ENGINE']}")
        print(f"   - NAME: {db_config['NAME']}")
        print(f"   - USER: {db_config['USER']}")
        print(f"   - HOST: {db_config['HOST']}")
        print(f"   - PORT: {db_config['PORT']}")
        
        print(f"🌐 ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # Test de connexion base de données
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, version()")
            result = cursor.fetchone()
            print(f"✅ Connexion DB réussie - Utilisateur: {result[0]}")
        
        print("\n🎯 Démarrage du serveur Django...")
        print("=" * 50)
        
        # Démarrer le serveur Django
        sys.argv = ['manage.py', 'runserver', '0.0.0.0:8080', '--noreload']
        execute_from_command_line(sys.argv)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    start_django_final() 
"""
Script final de démarrage Django - Configuration forcée et stable
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def start_django_final():
    """Démarre Django avec configuration forcée"""
    
    # Changer vers le répertoire du projet
    os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')
    
    # Configuration Django FORCÉE - ne dépend d'AUCUNE variable d'environnement
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
    
    print("🚀 DÉMARRAGE DJANGO FINAL")
    print("=" * 50)
    print(f"📁 Répertoire: {os.getcwd()}")
    print(f"⚙️ Settings: {os.environ['DJANGO_SETTINGS_MODULE']}")
    
    # Ajouter le répertoire au path Python
    sys.path.insert(0, os.getcwd())
    
    try:
        # Configuration Django
        django.setup()
        
        print("✅ Django configuré avec succès")
        
        # Vérifier la configuration de base de données
        from django.conf import settings
        db_config = settings.DATABASES['default']
        print(f"🗃️ Base de données configurée:")
        print(f"   - ENGINE: {db_config['ENGINE']}")
        print(f"   - NAME: {db_config['NAME']}")
        print(f"   - USER: {db_config['USER']}")
        print(f"   - HOST: {db_config['HOST']}")
        print(f"   - PORT: {db_config['PORT']}")
        
        print(f"🌐 ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # Test de connexion base de données
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user, version()")
            result = cursor.fetchone()
            print(f"✅ Connexion DB réussie - Utilisateur: {result[0]}")
        
        print("\n🎯 Démarrage du serveur Django...")
        print("=" * 50)
        
        # Démarrer le serveur Django
        sys.argv = ['manage.py', 'runserver', '0.0.0.0:8080', '--noreload']
        execute_from_command_line(sys.argv)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    start_django_final() 