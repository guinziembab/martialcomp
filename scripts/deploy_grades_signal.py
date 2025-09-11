#!/usr/bin/env python3
"""
Script de déploiement pour grades/signals.py
À placer à la racine du projet Django et exécuter
"""

import os
import shutil
from datetime import datetime

def deploy_grades_signal():
    """Déploie la correction pour grades/signals.py"""
    
    print("🔧 DÉPLOIEMENT DE grades/signals.py")
    print("=" * 35)
    
    # Chemin du fichier à corriger
    signal_file = "grades/signals.py"
    
    # Vérifier que le fichier existe
    if not os.path.exists(signal_file):
        print(f"❌ Fichier non trouvé: {signal_file}")
        print("   Assurez-vous d'exécuter ce script à la racine du projet Django")
        return False
    
    # Créer un backup avec timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{signal_file}.backup_{timestamp}"
    
    try:
        # 1. SAUVEGARDE
        print(f"💾 Sauvegarde: {backup_file}")
        shutil.copy2(signal_file, backup_file)
        print("✅ Sauvegarde créée")
        
        # 2. LECTURE DU FICHIER
        print("📖 Lecture du fichier actuel...")
        with open(signal_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3. APPLICATION DES CORRECTIONS
        print("🔄 Application des corrections...")
        
        corrections_applied = 0
        
        # Liste des corrections à appliquer
        corrections = [
            ('latest_grade.is_current = True', 'latest_grade.is_current = bool(True)'),
            ('is_current = True', 'is_current = bool(True)'),
            ('is_current=True', 'is_current=bool(True)'),
            ('is_current=False', 'is_current=bool(False)'),
            ('certificate_issued = True', 'certificate_issued = bool(True)'),
            ('.update(is_current=False)', '.update(is_current=bool(False))')
        ]
        
        for old_pattern, new_pattern in corrections:
            if old_pattern in content:
                content = content.replace(old_pattern, new_pattern)
                corrections_applied += 1
                print(f"  ✅ {old_pattern} → {new_pattern}")
        
        if corrections_applied > 0:
            print(f"✅ {corrections_applied} corrections appliquées")
        else:
            print("⚠️  Aucun pattern à corriger trouvé - fichier peut-être déjà corrigé")
        
        # 4. ÉCRITURE DU FICHIER CORRIGÉ
        print("💾 Écriture du fichier corrigé...")
        with open(signal_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fichier mis à jour")
        
        # 5. VALIDATION SYNTAXE
        print("🧪 Validation de la syntaxe Python...")
        import subprocess
        import sys
        
        result = subprocess.run([sys.executable, '-m', 'py_compile', signal_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Syntaxe Python valide")
        else:
            print("❌ Erreur de syntaxe détectée!")
            print(f"Erreur: {result.stderr}")
            
            # Restaurer le backup
            print("🔄 Restauration du backup...")
            shutil.copy2(backup_file, signal_file)
            print("✅ Backup restauré")
            return False
        
        # 6. RÉSUMÉ
        print()
        print("📋 RÉSUMÉ DES MODIFICATIONS")
        print("=" * 26)
        print("✅ Fichier: grades/signals.py")
        print("✅ Corrections: PractitionerGrade boolean fields")
        print("✅ Patterns corrigés:")
        print("   - is_current = True → bool(True)")
        print("   - is_current=True → bool(True)")
        print("   - is_current=False → bool(False)")
        print("   - certificate_issued = True → bool(True)")
        print("   - .update(is_current=False) → bool(False)")
        print(f"📁 Backup: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du déploiement: {e}")
        
        # Restaurer le backup si possible
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, signal_file)
            print("🔄 Backup restauré automatiquement")
        
        return False

def main():
    print("🚀 SCRIPT DE DÉPLOIEMENT - GRADES SIGNAL")
    print("=" * 42)
    print("🎯 Objectif: Corriger l'erreur boolean PostgreSQL")
    print("📂 Fichier: grades/signals.py")
    print()
    
    success = deploy_grades_signal()
    
    print()
    print("=" * 42)
    
    if success:
        print("🎉 DÉPLOIEMENT RÉUSSI!")
        print()
        print("📋 ÉTAPES SUIVANTES:")
        print("1. Redémarrer Django (si en production):")
        print("   sudo systemctl restart martialcomp")
        print("2. Tester l'ajout d'un pratiquant")
        print("3. Vérifier les logs:")
        print("   sudo journalctl -u martialcomp -f")
        
    else:
        print("❌ DÉPLOIEMENT ÉCHOUÉ")
        print("   Le fichier original a été restauré")
        print("   Vérifiez les erreurs ci-dessus")
    
    print()
    print("🔧 Pour restaurer manuellement:")
    print(f"   cp grades/signals.py.backup_* grades/signals.py")

if __name__ == "__main__":
    main()