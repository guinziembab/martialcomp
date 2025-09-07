#!/usr/bin/env python3
"""
Script pour corriger tous les problèmes identifiés sur le serveur de production.
Exécute toutes les corrections en séquence de manière sécurisée.
"""

import subprocess
import sys
import os
import shutil
from datetime import datetime

def run_command(command, description):
    """Exécute une commande et retourne le résultat"""
    print(f"🔧 {description}")
    print(f"   Commande: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print(f"   ✅ Succès")
            if result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines[:5]:  # Afficher seulement les 5 premières lignes
                    print(f"   {line}")
                if len(lines) > 5:
                    print(f"   ... ({len(lines)-5} lignes supplémentaires)")
        else:
            print(f"   ❌ Erreur (code: {result.returncode})")
            if result.stderr.strip():
                print(f"   Stderr: {result.stderr.strip()}")
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, "", str(e)

def backup_files():
    """Créer des sauvegardes des fichiers critiques"""
    print("💾 Création des sauvegardes...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_corrections_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "api/urls.py",
        "config/settings/development.py",
        "config/translation_service.py",
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_dir, file_path.replace('/', '_'))
            shutil.copy2(file_path, backup_path)
            print(f"   ✅ Sauvegardé: {file_path} → {backup_path}")
    
    print(f"   📁 Dossier de sauvegarde: {backup_dir}")
    return backup_dir

def fix_url_namespace():
    """Corriger le namespace 'api_auth' dupliqué"""
    print("🔗 Correction du namespace URL api_auth...")
    
    file_path = "api/urls.py"
    if not os.path.exists(file_path):
        print(f"   ❌ Fichier non trouvé: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer le namespace dupliqué
    old_line = "path('v1/auth/', include('api_auth.urls', namespace='api_auth')),"
    new_line = "path('v1/auth/', include('api_auth.urls', namespace='api_auth_v1')),"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ Namespace api_auth → api_auth_v1")
        return True
    else:
        print("   ℹ️ Namespace déjà corrigé ou introuvable")
        return True

def fix_allauth_settings():
    """Corriger les paramètres django-allauth dépréciés"""
    print("⚙️ Correction des paramètres django-allauth...")
    
    file_path = "config/settings/development.py"
    if not os.path.exists(file_path):
        print(f"   ❌ Fichier non trouvé: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer le paramètre déprécié
    old_line = "ACCOUNT_USERNAME_REQUIRED = True"
    new_line = "ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ ACCOUNT_USERNAME_REQUIRED → ACCOUNT_SIGNUP_FIELDS")
        return True
    else:
        print("   ℹ️ Paramètre déjà corrigé ou introuvable")
        return True

def fix_deepl_logging():
    """Réduire le bruit des logs DeepL"""
    print("📝 Correction du niveau de log DeepL...")
    
    file_path = "config/translation_service.py"
    if not os.path.exists(file_path):
        print(f"   ❌ Fichier non trouvé: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remplacer le niveau de log
    old_line = 'logger.info("DeepL API key not found; DeepL features disabled")'
    new_line = 'logger.debug("DeepL API key not found; DeepL features disabled")'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("   ✅ Niveau de log DeepL: info → debug")
        return True
    else:
        print("   ℹ️ Log DeepL déjà corrigé ou introuvable")
        return True

def fix_migrations():
    """Corriger les migrations en supprimant les migrations problématiques"""
    print("🗄️ Correction des migrations...")
    
    # Supprimer les migrations problématiques s'elles existent
    problematic_migrations = [
        "apps/competitions/migrations/0008_remove_matchtimeslot_category_schedule_and_more.py",
        "apps/competitions/migrations/0009_alter_userprofile_organization_competitionschedule_and_more.py"
    ]
    
    for migration_file in problematic_migrations:
        if os.path.exists(migration_file):
            os.remove(migration_file)
            print(f"   ✅ Supprimé: {migration_file}")
    
    # Revenir à la migration 0007 et nettoyer
    success, stdout, stderr = run_command(
        "python3 manage.py migrate --fake competitions 0007",
        "Revenir à la migration 0007"
    )
    
    if not success:
        print("   ⚠️ Erreur lors du retour à la migration 0007, mais on continue...")
    
    # Créer de nouvelles migrations propres
    success, stdout, stderr = run_command(
        "python3 manage.py makemigrations",
        "Créer de nouvelles migrations propres"
    )
    
    if not success:
        print("   ❌ Erreur lors de la création des migrations")
        return False
    
    # Appliquer toutes les migrations
    success, stdout, stderr = run_command(
        "python3 manage.py migrate",
        "Appliquer toutes les migrations"
    )
    
    return success

def final_check():
    """Vérification finale que tout fonctionne"""
    print("🔍 Vérification finale...")
    
    success, stdout, stderr = run_command(
        "python3 manage.py check",
        "Vérification Django complète"
    )
    
    if success:
        if "System check identified no issues" in stdout:
            print("   🎉 Aucun problème détecté !")
            return True
        else:
            print("   ⚠️ Quelques avertissements restent, mais pas d'erreurs critiques")
            return True
    else:
        print("   ❌ Des erreurs persistent")
        return False

def main():
    """Fonction principale"""
    print("🚀 Correction Complète des Problèmes - MartialComp")
    print("=" * 60)
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('manage.py'):
        print("❌ Erreur: manage.py non trouvé. Exécutez ce script depuis le répertoire racine du projet Django.")
        return 1
    
    try:
        # 1. Créer des sauvegardes
        backup_dir = backup_files()
        
        # 2. Corrections des fichiers de configuration
        print("\n🔧 Phase 1: Corrections de configuration")
        fix_url_namespace()
        fix_allauth_settings() 
        fix_deepl_logging()
        
        # 3. Corrections des migrations
        print("\n🗄️ Phase 2: Corrections des migrations")
        if not fix_migrations():
            print("❌ Erreur lors de la correction des migrations")
            return 1
        
        # 4. Vérification finale
        print("\n✅ Phase 3: Vérification finale")
        if final_check():
            print("\n🏆 Toutes les corrections appliquées avec succès !")
            print(f"\n📄 Sauvegarde disponible dans: {backup_dir}")
            
            print("\n📋 Actions suivantes recommandées:")
            print("   - Redémarrer l'application Django")
            print("   - Collecter les fichiers statiques: python3 manage.py collectstatic")
            print("   - Vérifier les pages problématiques:")
            print("     * /fr/competitions/federations/3/examens/")
            print("     * /fr/competitions/dashboard/documentation/")
            
            return 0
        else:
            print("\n❌ La vérification finale a échoué")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Correction interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())