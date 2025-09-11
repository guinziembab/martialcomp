#!/usr/bin/env python3
"""
Script de déploiement pour la correction des champs famille
Corrige l'erreur PostgreSQL 'invalid input syntax for type boolean'
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime

def create_backup_dir():
    """Crée un répertoire de sauvegarde horodaté"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backups/family_fields_fix_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def backup_files(backup_dir):
    """Sauvegarde les fichiers qui vont être modifiés"""
    files_to_backup = [
        "competitions/models/practitioners.py",
        "competitions/migrations/"
    ]
    
    print("💾 SAUVEGARDE DES FICHIERS")
    print("=" * 30)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copy2(file_path, backup_path)
                print(f"✅ Sauvegardé: {file_path} → {backup_path}")
            elif os.path.isdir(file_path):
                backup_path = os.path.join(backup_dir, os.path.basename(file_path))
                shutil.copytree(file_path, backup_path, dirs_exist_ok=True)
                print(f"✅ Sauvegardé: {file_path}/ → {backup_path}/")

def update_practitioner_model():
    """Met à jour le modèle Practitioner avec les corrections"""
    model_file = "competitions/models/practitioners.py"
    
    print("🔧 MISE À JOUR DU MODÈLE PRACTITIONER")
    print("=" * 40)
    
    if not os.path.exists(model_file):
        print(f"❌ Fichier non trouvé: {model_file}")
        return False
    
    # Créer un backup du fichier
    backup_file = f"{model_file}.backup_{datetime.now().strftime('%H%M%S')}"
    shutil.copy2(model_file, backup_file)
    print(f"📁 Backup créé: {backup_file}")
    
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier si les corrections sont déjà appliquées
        if 'null=True' in content and 'family_role' in content:
            print("✅ Les corrections semblent déjà appliquées au modèle")
            return True
        
        # Appliquer les corrections si nécessaires
        corrections = [
            (
                'family_role = models.CharField(\n        _("Rôle familial"),\n        max_length=20,\n        choices=[\n            (\'parent\', _(\'Parent\')),\n            (\'guardian\', _(\'Tuteur légal\')),\n            (\'child\', _(\'Enfant\')),\n            (\'spouse\', _(\'Conjoint(e)\')),\n            (\'sibling\', _(\'Frère/Sœur\')),\n            (\'other\', _(\'Autre\'))\n        ],\n        blank=True,\n        help_text=_("Rôle de ce pratiquant dans sa famille")\n    )',
                'family_role = models.CharField(\n        _("Rôle familial"),\n        max_length=20,\n        choices=[\n            (\'parent\', _(\'Parent\')),\n            (\'guardian\', _(\'Tuteur légal\')),\n            (\'child\', _(\'Enfant\')),\n            (\'spouse\', _(\'Conjoint(e)\')),\n            (\'sibling\', _(\'Frère/Sœur\')),\n            (\'other\', _(\'Autre\'))\n        ],\n        blank=True,\n        null=True,\n        help_text=_("Rôle de ce pratiquant dans sa famille")\n    )'
            ),
            (
                'family_emergency_contact = models.CharField(\n        _("Contact d\'urgence familial"),\n        max_length=200,\n        blank=True,\n        help_text=_("Contact d\'urgence si différent du responsable familial")\n    )',
                'family_emergency_contact = models.CharField(\n        _("Contact d\'urgence familial"),\n        max_length=200,\n        blank=True,\n        null=True,\n        help_text=_("Contact d\'urgence si différent du responsable familial")\n    )'
            )
        ]
        
        corrections_applied = 0
        for old_pattern, new_pattern in corrections:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                corrections_applied += 1
                print(f"✅ Correction appliquée: ajout de null=True")
        
        if corrections_applied > 0:
            with open(model_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {corrections_applied} corrections appliquées au modèle")
        else:
            print("ℹ️  Aucune correction nécessaire - modèle déjà à jour")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        # Restaurer le backup
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, model_file)
            print("🔄 Backup restauré")
        return False

def create_migration():
    """Crée la migration Django"""
    print("\n🔄 CRÉATION DE LA MIGRATION")
    print("=" * 30)
    
    try:
        # Vérifier si Django est configuré
        result = subprocess.run([
            sys.executable, 'manage.py', 'makemigrations', 'competitions', 
            '--name=fix_family_fields_null'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration créée avec succès")
            print(result.stdout)
            return True
        else:
            print(f"❌ Erreur lors de la création de la migration: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def apply_migration():
    """Applique la migration Django"""
    print("\n🚀 APPLICATION DE LA MIGRATION")
    print("=" * 35)
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migration appliquée avec succès")
            print(result.stdout)
            return True
        else:
            print(f"❌ Erreur lors de l'application de la migration: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def validate_fix():
    """Valide que la correction fonctionne"""
    print("\n🧪 VALIDATION DE LA CORRECTION")
    print("=" * 35)
    
    try:
        # Tester avec un script Python simple
        test_script = """
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from competitions.models.practitioners import Practitioner
from organizations.models import Organization
from datetime import date

try:
    org = Organization.objects.first()
    if org:
        # Test création avec champs vides
        p = Practitioner.objects.create(
            first_name="Test",
            last_name="Fix",
            birth_date=date(1990,1,1),
            organization=org,
            family_role="",
            family_emergency_contact=""
        )
        print("✅ Test réussi: Practitioner créé avec champs famille vides")
        p.delete()
    else:
        print("⚠️  Aucune organisation trouvée pour le test")
except Exception as e:
    print(f"❌ Test échoué: {e}")
"""
        
        result = subprocess.run([sys.executable, '-c', test_script], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(result.stdout)
            return True
        else:
            print(f"❌ Test de validation échoué: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la validation: {e}")
        return False

def main():
    print("🚀 DÉPLOIEMENT - CORRECTION CHAMPS FAMILLE")
    print("=" * 50)
    print("🎯 Objectif: Corriger l'erreur PostgreSQL 'invalid input syntax for type boolean'")
    print("📋 Action: Ajouter null=True aux champs family_role et family_emergency_contact")
    print()
    
    # Vérifier qu'on est à la racine du projet
    if not os.path.exists("manage.py"):
        print("❌ Erreur: Ce script doit être exécuté à la racine du projet Django")
        return
    
    # 1. Créer le répertoire de sauvegarde
    backup_dir = create_backup_dir()
    print(f"📁 Répertoire de sauvegarde: {backup_dir}")
    print()
    
    # 2. Sauvegarder les fichiers
    backup_files(backup_dir)
    print()
    
    # 3. Mettre à jour le modèle
    if not update_practitioner_model():
        print("❌ Échec de la mise à jour du modèle")
        return
    print()
    
    # 4. Créer la migration
    if not create_migration():
        print("❌ Échec de la création de la migration")
        return
    
    # 5. Appliquer la migration
    if not apply_migration():
        print("❌ Échec de l'application de la migration")
        return
    
    # 6. Valider la correction
    if not validate_fix():
        print("⚠️  La validation a échoué - vérifiez manuellement")
    
    print("\n" + "=" * 50)
    print("🎉 DÉPLOIEMENT TERMINÉ!")
    print()
    print("📋 RÉSUMÉ DES ACTIONS:")
    print("✅ Modèle Practitioner mis à jour")
    print("✅ Migration Django créée et appliquée")
    print("✅ Base de données PostgreSQL mise à jour")
    print()
    print("🧪 TESTS À EFFECTUER:")
    print("1. Aller sur l'interface d'ajout de pratiquant")
    print("2. Créer un nouveau pratiquant")
    print("3. Vérifier qu'aucune erreur PostgreSQL n'apparaît")
    print()
    print(f"📁 Sauvegardes disponibles dans: {backup_dir}")
    print("🔧 En cas de problème, restaurer avec:")
    print(f"   cp {backup_dir}/practitioners.py competitions/models/")

if __name__ == "__main__":
    main()