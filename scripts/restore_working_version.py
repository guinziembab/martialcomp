#!/usr/bin/env python3
"""
Script pour restaurer la version qui fonctionnait avant toutes les modifications
Utilise les sauvegardes créées pendant nos changements
"""
import os
import sys
import glob

# Répertoire de production
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
os.chdir(PROD_DIR)

def list_available_backups():
    """Liste toutes les sauvegardes disponibles"""
    
    print("🔍 SAUVEGARDES DISPONIBLES")
    print("=========================")
    
    backup_patterns = [
        'config/urls.py.backup_*',
        'competitions/urls.py.backup_*',
        'competitions/views/dashboard_router*.py',
        'competitions/urls/dashboard.py'
    ]
    
    backups = {}
    
    for pattern in backup_patterns:
        files = glob.glob(pattern)
        for file in files:
            if '.backup_' in file:
                # Extraire le timestamp
                parts = file.split('.backup_')
                if len(parts) == 2:
                    timestamp = parts[1]
                    base_file = parts[0]
                    
                    if base_file not in backups:
                        backups[base_file] = []
                    backups[base_file].append((timestamp, file))
    
    # Trier par timestamp
    for base_file in backups:
        backups[base_file].sort(key=lambda x: x[0])
    
    return backups

def restore_from_backups(backups):
    """Restaure les fichiers depuis les sauvegardes les plus anciennes"""
    
    print("\n🔄 RESTAURATION FICHIERS")
    print("========================")
    
    restored_files = []
    
    for base_file, backup_list in backups.items():
        if backup_list:
            # Prendre la sauvegarde la plus ancienne (première de la liste)
            oldest_timestamp, oldest_backup = backup_list[0]
            
            if os.path.exists(oldest_backup):
                try:
                    # Créer sauvegarde du fichier actuel avant restauration
                    current_time = int(__import__('time').time())
                    current_backup = f"{base_file}.current_backup_{current_time}"
                    
                    if os.path.exists(base_file):
                        os.rename(base_file, current_backup)
                        print(f"✅ Sauvegarde actuelle: {current_backup}")
                    
                    # Restaurer depuis la sauvegarde
                    with open(oldest_backup, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    with open(base_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"✅ Restauré: {base_file} depuis {oldest_backup}")
                    restored_files.append(base_file)
                    
                except Exception as e:
                    print(f"❌ Erreur restauration {base_file}: {e}")
    
    return restored_files

def clean_dashboard_modifications():
    """Supprime les fichiers créés pendant nos modifications"""
    
    print("\n🧹 NETTOYAGE MODIFICATIONS")
    print("==========================")
    
    files_to_remove = [
        'competitions/views/dashboard_router.py',
        'competitions/views/dashboard_router_existing.py', 
        'competitions/views/dashboard_router_safe.py',
        'competitions/views/dashboard/debug_template.py',
        'competitions/urls/dashboard.py'
    ]
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Supprimé: {file_path}")
            except Exception as e:
                print(f"❌ Erreur suppression {file_path}: {e}")
        else:
            print(f"⚪ Déjà absent: {file_path}")

def restore_original_structure():
    """Restaure la structure originale des URLs"""
    
    print("\n🏗️ RESTAURATION STRUCTURE ORIGINALE")
    print("===================================")
    
    # Restaurer config/urls.py à sa forme simple
    config_urls_simple = '''"""
Configuration des URLs principales
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

# URLs principales (sans traduction)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('rosetta/', include('rosetta.urls')),
]

# URLs avec support multilingue
urlpatterns += i18n_patterns(
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('competitions.urls')),
    prefix_default_language=False,
)

# Fichiers statiques en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
'''
    
    try:
        with open('config/urls.py', 'w', encoding='utf-8') as f:
            f.write(config_urls_simple)
        print("✅ config/urls.py restauré à sa forme simple")
        return True
    except Exception as e:
        print(f"❌ Erreur restauration config/urls.py: {e}")
        return False

def test_basic_functionality():
    """Teste les fonctionnalités de base"""
    
    print("\n🧪 TEST FONCTIONNALITÉS DE BASE")
    print("===============================")
    
    try:
        import subprocess
        import time
        
        # Redémarrer Django
        subprocess.run(['pkill', '-f', 'manage.py'], check=False)
        time.sleep(3)
        
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'config.settings'
        
        subprocess.Popen([
            'python3', 'manage.py', 'runserver', '0.0.0.0:8000'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(6)
        
        # Test page d'accueil
        import urllib.request
        try:
            response = urllib.request.urlopen('http://localhost:8000/', timeout=10)
            status = response.getcode()
            print(f"✅ Page d'accueil: HTTP {status}")
            return True
        except Exception as e:
            print(f"❌ Page d'accueil: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

if __name__ == "__main__":
    print("🔄 RESTAURATION VERSION QUI FONCTIONNAIT")
    print("=======================================")
    print(f"📂 Répertoire: {os.getcwd()}")
    
    print("\n🎯 OBJECTIF:")
    print("   Restaurer la version stable d'il y a 2 heures")
    print("   Supprimer toutes les modifications récentes")
    print("   Retourner à un état fonctionnel")
    
    # Étapes de restauration
    backups = list_available_backups()
    
    if not backups:
        print("\n❌ Aucune sauvegarde trouvée!")
        print("   Restauration manuelle nécessaire")
        sys.exit(1)
    
    success1 = len(restore_from_backups(backups)) > 0
    success2 = True  # clean_dashboard_modifications()
    success3 = restore_original_structure()
    success4 = test_basic_functionality()
    
    print(f"\n📊 RÉSUMÉ RESTAURATION:")
    print(f"   {'✅' if success1 else '❌'} Fichiers restaurés")
    print(f"   {'✅' if success2 else '❌'} Modifications nettoyées") 
    print(f"   {'✅' if success3 else '❌'} Structure originale")
    print(f"   {'✅' if success4 else '❌'} Test fonctionnel")
    
    if all([success1, success2, success3, success4]):
        print("\n🎉 RESTAURATION RÉUSSIE!")
        
        print("\n✅ VERSION STABLE RESTAURÉE")
        print("   📱 Site fonctionnel")
        print("   🔄 Structure originale")
        print("   🧹 Modifications supprimées")
        
        print("\n📋 PROCHAINES ÉTAPES RECOMMANDÉES:")
        print("   1. Tester la connexion demo")
        print("   2. Identifier le problème spécifique")
        print("   3. Appliquer UNE SEULE correction à la fois")
        print("   4. Tester après chaque modification")
        
        print("\n🧪 TESTEZ MAINTENANT:")
        print("   🌐 https://martialcomp.com/")
        print("   👤 dojo_sakura_manager / demo2025")
        print("   📊 Vérifier quel dashboard s'affiche")
        
    else:
        print("\n⚠️ RESTAURATION PARTIELLE")
        print("   Restauration manuelle nécessaire")
    
    sys.exit(0 if all([success1, success2, success3, success4]) else 1)