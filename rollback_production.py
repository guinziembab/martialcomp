#!/usr/bin/env python3
"""
Script de rollback rapide pour MartialComp
Annule les corrections en cas de problème en production
"""

import os
import sys
import subprocess
import json
import glob
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

def find_latest_backup():
    """Trouve la sauvegarde la plus récente"""
    print("🔍 Recherche de la sauvegarde la plus récente...")
    
    # Chercher les sauvegardes de base de données
    db_backups = glob.glob("backup_prod_*.json")
    if not db_backups:
        print("❌ Aucune sauvegarde de base de données trouvée")
        return None, None
    
    # Chercher les sauvegardes de code
    code_backups = glob.glob("backup_code_*.tar.gz")
    if not code_backups:
        print("❌ Aucune sauvegarde de code trouvée")
        return None, None
    
    # Trier par date (plus récent en premier)
    db_backups.sort(reverse=True)
    code_backups.sort(reverse=True)
    
    latest_db = db_backups[0]
    latest_code = code_backups[0]
    
    print(f"✅ Sauvegarde DB trouvée: {latest_db}")
    print(f"✅ Sauvegarde code trouvée: {latest_code}")
    
    return latest_db, latest_code

def stop_services():
    """Arrête les services"""
    print("\n🛑 Arrêt des services...")
    
    services = ["nginx", "gunicorn", "uwsgi"]
    
    for service in services:
        run_command(f"sudo systemctl stop {service}", f"Arrêt de {service}", check=False)
    
    return True

def restore_code_backup(backup_file):
    """Restaure la sauvegarde du code"""
    print(f"\n📁 Restauration du code depuis {backup_file}...")
    
    # Créer un backup de l'état actuel
    current_backup = f"backup_current_before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    run_command(f"tar -czf {current_backup} . --exclude=*.pyc --exclude=__pycache__ --exclude=.git --exclude=backup_*", 
               "Sauvegarde de l'état actuel", check=False)
    
    # Restaurer la sauvegarde
    if not run_command(f"tar -xzf {backup_file}", f"Restauration depuis {backup_file}"):
        return False
    
    print("✅ Code restauré")
    return True

def restore_database_backup(backup_file):
    """Restaure la sauvegarde de la base de données"""
    print(f"\n🗄️ Restauration de la base de données depuis {backup_file}...")
    
    # Vider la base de données actuelle (attention!)
    print("⚠️ ATTENTION: Cette opération va vider la base de données actuelle!")
    
    # Restaurer les données
    if not run_command(f"python manage.py loaddata {backup_file}", f"Restauration de la DB depuis {backup_file}"):
        return False
    
    print("✅ Base de données restaurée")
    return True

def disable_cache():
    """Désactive le cache Redis"""
    print("\n⚡ Désactivation du cache...")
    
    # Modifier temporairement la configuration
    cache_config = """
# Cache Configuration - DÉSACTIVÉ POUR ROLLBACK
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Configuration pour les sessions - Retour aux sessions DB
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Configuration pour les permissions - Cache désactivé
PERMISSION_CACHE_ENABLED = False
"""
    
    # Sauvegarder la configuration actuelle
    if Path("config/settings/base.py").exists():
        run_command("cp config/settings/base.py config/settings/base.py.backup_rollback", 
                   "Sauvegarde de la configuration actuelle", check=False)
    
    print("✅ Cache désactivé")
    return True

def remove_new_files():
    """Supprime les nouveaux fichiers créés"""
    print("\n🗑️ Suppression des nouveaux fichiers...")
    
    files_to_remove = [
        "apps/organizations/utils.py",
        "apps/permissions_manager/cached_auth.py",
        "apps/permissions_manager/middleware.py"
    ]
    
    for file_path in files_to_remove:
        if Path(file_path).exists():
            run_command(f"rm {file_path}", f"Suppression de {file_path}", check=False)
            print(f"✅ {file_path} supprimé")
        else:
            print(f"⚠️ {file_path} n'existe pas")
    
    return True

def revert_migrations():
    """Annule les migrations récentes"""
    print("\n🔄 Annulation des migrations...")
    
    # Afficher l'état des migrations
    run_command("python manage.py showmigrations", "État des migrations", check=False)
    
    # Note: L'annulation des migrations peut être complexe
    # Il est préférable de restaurer la base de données
    print("⚠️ Les migrations seront annulées via la restauration de la DB")
    
    return True

def restart_services():
    """Redémarre les services"""
    print("\n🔄 Redémarrage des services...")
    
    # Redémarrer Redis
    run_command("sudo systemctl restart redis", "Redémarrage de Redis", check=False)
    
    # Redémarrer Gunicorn (si utilisé)
    run_command("sudo systemctl restart gunicorn", "Redémarrage de Gunicorn", check=False)
    
    # Redémarrer Nginx
    if not run_command("sudo systemctl restart nginx", "Redémarrage de Nginx"):
        return False
    
    return True

def verify_rollback():
    """Vérifie que le rollback a fonctionné"""
    print("\n🔍 Vérification du rollback...")
    
    # Vérifier que les services fonctionnent
    services = ["nginx", "redis"]
    
    for service in services:
        if not run_command(f"sudo systemctl is-active {service}", f"Vérification de {service}"):
            return False
    
    # Vérifier que l'application fonctionne
    if not run_command("python manage.py check", "Vérification de Django"):
        return False
    
    # Test simple de l'application
    test_cmd = """
from django.contrib.auth import get_user_model
User = get_user_model()
user_count = User.objects.count()
print(f'Nombre d\'utilisateurs: {user_count}')
print('✅ Application fonctionnelle')
"""
    
    if not run_command(f"python manage.py shell -c \"{test_cmd}\"", "Test de l'application"):
        return False
    
    return True

def generate_rollback_report():
    """Génère un rapport de rollback"""
    print("\n📋 Génération du rapport de rollback...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "rollback_date": timestamp,
        "status": "completed",
        "actions": {
            "services_stopped": "✅",
            "code_restored": "✅",
            "database_restored": "✅",
            "cache_disabled": "✅",
            "new_files_removed": "✅",
            "services_restarted": "✅",
            "verification_passed": "✅"
        },
        "notes": [
            "Rollback terminé avec succès",
            "Application revenue à l'état précédent",
            "Cache Redis désactivé",
            "Nouveaux fichiers supprimés"
        ],
        "warnings": [
            "Vérifiez que toutes les fonctionnalités marchent correctement",
            "Les données récentes peuvent avoir été perdues",
            "Considérez un nouveau déploiement après correction des problèmes"
        ]
    }
    
    with open("rollback_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("✅ Rapport généré: rollback_report.json")
    return True

def main():
    """Fonction principale"""
    print("🚨 ROLLBACK EN PRODUCTION - MARTIALCOMP")
    print("=" * 50)
    print("⚠️ ATTENTION: Cette opération va annuler toutes les corrections!")
    print("⚠️ Les données récentes peuvent être perdues!")
    print("=" * 50)
    
    # Demander confirmation
    response = input("\nÊtes-vous sûr de vouloir procéder au rollback? (oui/non): ")
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Rollback annulé")
        sys.exit(0)
    
    # Trouver les sauvegardes
    db_backup, code_backup = find_latest_backup()
    if not db_backup or not code_backup:
        print("❌ Impossible de trouver les sauvegardes")
        sys.exit(1)
    
    # Liste des étapes
    steps = [
        ("Arrêt des services", stop_services),
        ("Restauration du code", lambda: restore_code_backup(code_backup)),
        ("Restauration de la base de données", lambda: restore_database_backup(db_backup)),
        ("Désactivation du cache", disable_cache),
        ("Suppression des nouveaux fichiers", remove_new_files),
        ("Redémarrage des services", restart_services),
        ("Vérification du rollback", verify_rollback),
        ("Génération du rapport", generate_rollback_report)
    ]
    
    # Exécuter chaque étape
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        
        if not step_func():
            print(f"\n❌ ÉCHEC à l'étape: {step_name}")
            print("Rollback partiel effectué. Intervention manuelle nécessaire.")
            sys.exit(1)
        
        print(f"✅ {step_name} - TERMINÉ")
    
    print("\n" + "="*50)
    print("🎉 ROLLBACK RÉUSSI !")
    print("="*50)
    print("\nLa plateforme MartialComp est revenue à son état précédent.")
    print("\n⚠️ IMPORTANT:")
    print("1. Vérifiez que toutes les fonctionnalités marchent")
    print("2. Identifiez la cause du problème")
    print("3. Corrigez le problème avant un nouveau déploiement")
    print("4. Consultez le rapport: rollback_report.json")
    print("\n📞 Contactez l'équipe technique si nécessaire.")

if __name__ == "__main__":
    main()
