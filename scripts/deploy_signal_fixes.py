#!/usr/bin/env python3
"""
Script pour déployer les corrections des signaux Django en production
Corrige l'erreur 'invalid input syntax for type boolean' dans les signaux
"""

import os
import shutil
from datetime import datetime

def deploy_competitions_signals():
    """Déploie la correction pour competitions/signals.py"""
    
    source_file = "/mnt/c/martial_hub_django/martialcomp/competitions/signals.py"
    target_file = "/opt/martialcomp/app/competitions/signals.py"
    backup_file = f"{target_file}.backup_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Backup de sécurité
        print(f"📁 Backup competitions/signals.py: {backup_file}")
        shutil.copy2(target_file, backup_file)
        
        # Copier le fichier corrigé
        shutil.copy2(source_file, target_file)
        
        print("✅ competitions/signals.py corrigé déployé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du déploiement de competitions/signals.py: {e}")
        # Restaurer le backup
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, target_file)
            print("🔄 Backup restauré")
        return False

def deploy_grades_signals():
    """Déploie la correction pour grades/signals.py"""
    
    source_file = "/mnt/c/martial_hub_django/martialcomp/grades/signals.py"
    target_file = "/opt/martialcomp/app/grades/signals.py"
    backup_file = f"{target_file}.backup_signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Backup de sécurité
        print(f"📁 Backup grades/signals.py: {backup_file}")
        shutil.copy2(target_file, backup_file)
        
        # Copier le fichier corrigé
        shutil.copy2(source_file, target_file)
        
        print("✅ grades/signals.py corrigé déployé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du déploiement de grades/signals.py: {e}")
        # Restaurer le backup
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, target_file)
            print("🔄 Backup restauré")
        return False

def main():
    print("🚀 DÉPLOIEMENT DES CORRECTIONS DE SIGNAUX")
    print("=" * 60)
    print("🎯 Objectif: Corriger l'erreur 'invalid input syntax for type boolean' dans les signaux")
    print("📋 Fichiers: competitions/signals.py et grades/signals.py")
    print()
    
    # Déployer les corrections
    success_competitions = deploy_competitions_signals()
    success_grades = deploy_grades_signals()
    
    print("\n" + "=" * 60)
    
    if success_competitions and success_grades:
        print("🎉 CORRECTIONS DÉPLOYÉES AVEC SUCCÈS!")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. 🔄 Redémarrer Django:")
        print("   sudo systemctl restart martialcomp")
        print("2. 🧪 Tester l'enregistrement d'un practitioner:")
        print("   https://martialcomp.com/fr/competitions/club/practitioners/add/")
        print("3. ✅ Vérifier que l'erreur boolean est résolue")
        
        print("\n🔍 CORRECTIONS APPLIQUÉES:")
        print("   - PractitionerQRCode.is_active: bool(True)")
        print("   - PractitionerQRCode.is_federation_validated: bool(False)")
        print("   - PractitionerGrade.is_current: bool(True/False)")
        print("   - GradeExamRegistration.certificate_issued: bool(True)")
        
    else:
        print("❌ ÉCHEC DU DÉPLOIEMENT")
        print("   Les fichiers originaux ont été restaurés automatiquement")
    
    print(f"\n📁 Backups disponibles: *.backup_signals_*")

if __name__ == "__main__":
    main()