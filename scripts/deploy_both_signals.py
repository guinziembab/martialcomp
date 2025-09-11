#!/usr/bin/env python3
"""
Script de déploiement global pour les deux fichiers signals.py
À placer à la racine du projet Django et exécuter
Exécute les deux scripts de déploiement individuels
"""

import os
import subprocess
import sys
from datetime import datetime

def run_script(script_name):
    """Exécute un script et retourne le résultat"""
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🚀 DÉPLOIEMENT GLOBAL DES CORRECTIONS SIGNALS")
    print("=" * 48)
    print("🎯 Objectif: Corriger l'erreur boolean PostgreSQL")
    print("📂 Fichiers: competitions/signals.py + grades/signals.py")
    print()
    
    # Vérifier qu'on est à la racine du projet
    if not os.path.exists("manage.py"):
        print("❌ Erreur: Ce script doit être exécuté à la racine du projet Django")
        print("   Fichier manage.py non trouvé")
        return
    
    # Vérifier que les scripts individuels existent
    scripts = [
        "deploy_competitions_signal.py",
        "deploy_grades_signal.py"
    ]
    
    missing_scripts = []
    for script in scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        print("❌ Scripts manquants:")
        for script in missing_scripts:
            print(f"   - {script}")
        print("\nPlacez tous les scripts à la racine du projet avant de continuer")
        return
    
    print("✅ Vérifications préalables OK")
    print()
    
    # Déploiement des corrections
    results = []
    
    # 1. Déploiement competitions/signals.py
    print("🔧 ÉTAPE 1: DÉPLOIEMENT COMPETITIONS SIGNAL")
    print("=" * 43)
    success, stdout, stderr = run_script("deploy_competitions_signal.py")
    print(stdout)
    if stderr:
        print(f"Erreurs: {stderr}")
    results.append(("competitions/signals.py", success))
    print()
    
    # 2. Déploiement grades/signals.py
    print("🔧 ÉTAPE 2: DÉPLOIEMENT GRADES SIGNAL")
    print("=" * 35)
    success, stdout, stderr = run_script("deploy_grades_signal.py")
    print(stdout)
    if stderr:
        print(f"Erreurs: {stderr}")
    results.append(("grades/signals.py", success))
    print()
    
    # 3. Résumé final
    print("📋 RÉSUMÉ FINAL")
    print("=" * 15)
    
    all_success = True
    for filename, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{status} - {filename}")
        if not success:
            all_success = False
    
    print()
    print("=" * 48)
    
    if all_success:
        print("🎉 DÉPLOIEMENT GLOBAL RÉUSSI!")
        print()
        print("📋 PROCHAINES ÉTAPES:")
        print("1. 🔄 Redémarrer Django (si en production):")
        print("   sudo systemctl restart martialcomp")
        print()
        print("2. 📊 Surveiller les logs:")
        print("   sudo journalctl -u martialcomp -f")
        print()
        print("3. 🧪 Tester l'ajout d'un pratiquant:")
        print("   URL: /competitions/club/practitioners/add/")
        print()
        print("4. ✅ Vérifier que l'erreur 'invalid input syntax for type boolean' est résolue")
        print()
        print("🔍 CORRECTIONS APPLIQUÉES:")
        print("   ✅ PractitionerQRCode.is_active: bool(True)")
        print("   ✅ PractitionerQRCode.is_federation_validated: bool(False)")
        print("   ✅ PractitionerGrade.is_current: bool(True/False)")
        print("   ✅ GradeExamRegistration.certificate_issued: bool(True)")
        
    else:
        print("⚠️  DÉPLOIEMENT PARTIEL")
        print("   Certains fichiers n'ont pas pu être corrigés")
        print("   Vérifiez les erreurs ci-dessus")
    
    print()
    print("📁 Backups créés avec timestamp dans chaque répertoire")
    print("🔧 Pour restaurer si nécessaire:")
    print("   cp competitions/signals.py.backup_* competitions/signals.py")
    print("   cp grades/signals.py.backup_* grades/signals.py")

if __name__ == "__main__":
    main()