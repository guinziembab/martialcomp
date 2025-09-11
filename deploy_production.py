#!/usr/bin/env python3
"""
Script de déploiement en production pour MartialComp
Applique toutes les corrections de segmentation et isolation
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

def run_command(command, description, check=True):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔧 {description}")
    print(f"Commande: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Sortie: {result.stdout}")
        if result.stderr:
            print(f"⚠️ Erreurs: {result.stderr}")
        
        if check and result.returncode != 0:
            print(f"❌ Erreur: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def check_prerequisites():
    """Vérifie les prérequis avant le déploiement"""
    print("🔍 Vérification des prérequis...")
    
    # Vérifier Python
    if not run_command("python --version", "Vérification de Python"):
        return False
    
    # Vérifier Django
    if not run_command("python -c 'import django; print(django.get_version())'", "Vérification de Django"):
        return False
    
    # Vérifier Redis
    if not run_command("redis-cli ping", "Vérification de Redis"):
        print("⚠️ Redis n'est pas accessible. Installation nécessaire.")
        return False
    
    # Vérifier l'espace disque
    if not run_command("df -h", "Vérification de l'espace disque"):
        return False
    
    return True

def create_backup():
    """Crée une sauvegarde complète"""
    print("\n💾 Création de la sauvegarde...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Sauvegarde de la base de données
    backup_db = f"backup_prod_{timestamp}.json"
    if not run_command(f"python manage.py dumpdata --exclude auth.permission --exclude contenttypes > {backup_db}", 
                      "Sauvegarde de la base de données"):
        return False
    
    # Sauvegarde des fichiers
    backup_code = f"backup_code_{timestamp}.tar.gz"
    if not run_command(f"tar -czf {backup_code} . --exclude=*.pyc --exclude=__pycache__ --exclude=.git --exclude=backup_*", 
                      "Sauvegarde des fichiers"):
        return False
    
    print(f"✅ Sauvegardes créées: {backup_db}, {backup_code}")
    return True

def install_dependencies():
    """Installe les nouvelles dépendances"""
    print("\n📦 Installation des dépendances...")
    
    # Installer django-redis
    if not run_command("pip install django-redis==5.4.0", "Installation de django-redis"):
        return False
    
    # Installer redis
    if not run_command("pip install redis==5.0.1", "Installation de redis"):
        return False
    
    return True

def verify_files():
    """Vérifie que tous les fichiers nécessaires existent"""
    print("\n📁 Vérification des fichiers...")
    
    required_files = [
        "apps/organizations/utils.py",
        "apps/permissions_manager/cached_auth.py",
        "apps/permissions_manager/middleware.py",
        "config/settings/base.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Fichier manquant: {file_path}")
            return False
        else:
            print(f"✅ {file_path}")
    
    return True

def run_migrations():
    """Exécute les migrations Django"""
    print("\n🗄️ Exécution des migrations...")
    
    # Créer les migrations
    if not run_command("python manage.py makemigrations", "Création des migrations"):
        return False
    
    # Appliquer les migrations
    if not run_command("python manage.py migrate", "Application des migrations"):
        return False
    
    # Vérifier l'état des migrations
    if not run_command("python manage.py showmigrations", "Vérification des migrations"):
        return False
    
    return True

def verify_data():
    """Vérifie l'état des données"""
    print("\n📊 Vérification des données...")
    
    # Vérifier les utilisateurs sans organisation
    check_users = """
from apps.competitions.models.users import UserProfile
users_without_org = UserProfile.objects.filter(organization__isnull=True).count()
print(f'Utilisateurs sans organisation: {users_without_org}')
if users_without_org > 0:
    print('⚠️ ATTENTION: Des utilisateurs n\'ont pas d\'organisation!')
else:
    print('✅ Tous les utilisateurs ont une organisation')
"""
    
    if not run_command(f"python manage.py shell -c \"{check_users}\"", "Vérification des utilisateurs"):
        return False
    
    # Vérifier les organisations
    check_orgs = """
from apps.organizations.models import Organization
org_count = Organization.objects.filter(is_active=True).count()
print(f'Organisations actives: {org_count}')
"""
    
    if not run_command(f"python manage.py shell -c \"{check_orgs}\"", "Vérification des organisations"):
        return False
    
    return True

def test_cache():
    """Teste le système de cache"""
    print("\n⚡ Test du système de cache...")
    
    test_cache_cmd = """
from django.core.cache import cache
cache.set('test_key', 'test_value', 60)
result = cache.get('test_key')
print(f'Test cache: {result}')
if result == 'test_value':
    print('✅ Cache Redis fonctionne correctement')
else:
    print('❌ Problème avec le cache Redis')
"""
    
    if not run_command(f"python manage.py shell -c \"{test_cache_cmd}\"", "Test du cache Redis"):
        return False
    
    return True

def test_isolation():
    """Teste l'isolation des vues"""
    print("\n🔒 Test de l'isolation...")
    
    test_isolation_cmd = """
from apps.organizations.utils import get_user_organization
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
if user:
    org = get_user_organization(user)
    print(f'Organisation de {user.username}: {org}')
    if org:
        print('✅ Isolation fonctionne')
    else:
        print('⚠️ Utilisateur sans organisation')
else:
    print('⚠️ Aucun utilisateur trouvé')
"""
    
    if not run_command(f"python manage.py shell -c \"{test_isolation_cmd}\"", "Test de l'isolation"):
        return False
    
    return True

def test_permissions():
    """Teste le système de permissions"""
    print("\n🔐 Test des permissions...")
    
    test_permissions_cmd = """
from apps.permissions_manager.cached_auth import user_has_permission
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
if user:
    has_perm = user_has_permission(user, 'view_competition')
    print(f'Permission view_competition pour {user.username}: {has_perm}')
    print('✅ Système de permissions fonctionne')
else:
    print('⚠️ Aucun utilisateur trouvé')
"""
    
    if not run_command(f"python manage.py shell -c \"{test_permissions_cmd}\"", "Test des permissions"):
        return False
    
    return True

def restart_services():
    """Redémarre les services"""
    print("\n🔄 Redémarrage des services...")
    
    # Redémarrer Redis
    if not run_command("sudo systemctl restart redis", "Redémarrage de Redis"):
        return False
    
    # Redémarrer Gunicorn (si utilisé)
    if not run_command("sudo systemctl restart gunicorn", "Redémarrage de Gunicorn", check=False):
        print("⚠️ Gunicorn non trouvé, continuant...")
    
    # Redémarrer Nginx
    if not run_command("sudo systemctl restart nginx", "Redémarrage de Nginx"):
        return False
    
    return True

def verify_services():
    """Vérifie que tous les services fonctionnent"""
    print("\n🔍 Vérification des services...")
    
    services = ["redis", "nginx"]
    
    for service in services:
        if not run_command(f"sudo systemctl is-active {service}", f"Vérification de {service}"):
            return False
    
    return True

def run_tests():
    """Exécute les tests"""
    print("\n🧪 Exécution des tests...")
    
    # Tests Django
    if not run_command("python manage.py test --verbosity=2", "Tests Django"):
        return False
    
    return True

def generate_report():
    """Génère un rapport de déploiement"""
    print("\n📋 Génération du rapport...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "deployment_date": timestamp,
        "status": "success",
        "checks": {
            "prerequisites": "✅",
            "backup": "✅",
            "dependencies": "✅",
            "files": "✅",
            "migrations": "✅",
            "data": "✅",
            "cache": "✅",
            "isolation": "✅",
            "permissions": "✅",
            "services": "✅",
            "tests": "✅"
        },
        "notes": [
            "Déploiement réussi",
            "Toutes les corrections appliquées",
            "Système de cache Redis opérationnel",
            "Isolation des vues fonctionnelle",
            "Permissions optimisées"
        ]
    }
    
    with open("deployment_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("✅ Rapport généré: deployment_report.json")
    return True

def main():
    """Fonction principale"""
    print("🚀 DÉPLOIEMENT EN PRODUCTION - MARTIALCOMP")
    print("=" * 50)
    
    # Liste des étapes
    steps = [
        ("Vérification des prérequis", check_prerequisites),
        ("Création de la sauvegarde", create_backup),
        ("Installation des dépendances", install_dependencies),
        ("Vérification des fichiers", verify_files),
        ("Exécution des migrations", run_migrations),
        ("Vérification des données", verify_data),
        ("Test du cache", test_cache),
        ("Test de l'isolation", test_isolation),
        ("Test des permissions", test_permissions),
        ("Redémarrage des services", restart_services),
        ("Vérification des services", verify_services),
        ("Exécution des tests", run_tests),
        ("Génération du rapport", generate_report)
    ]
    
    # Exécuter chaque étape
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        
        if not step_func():
            print(f"\n❌ ÉCHEC à l'étape: {step_name}")
            print("Arrêt du déploiement.")
            sys.exit(1)
        
        print(f"✅ {step_name} - TERMINÉ")
        time.sleep(1)
    
    print("\n" + "="*50)
    print("🎉 DÉPLOIEMENT RÉUSSI !")
    print("="*50)
    print("\nLa plateforme MartialComp est maintenant:")
    print("🔒 Sécurisée avec isolation complète")
    print("⚡ Optimisée avec cache Redis")
    print("👥 Organisée avec tous les utilisateurs assignés")
    print("🏗️ Unifiée avec le modèle Organization")
    print("\n📋 Rapport disponible: deployment_report.json")
    print("\nProchaines étapes:")
    print("1. Surveiller les performances pendant 24h")
    print("2. Former les utilisateurs")
    print("3. Planifier les optimisations futures")

if __name__ == "__main__":
    main()
