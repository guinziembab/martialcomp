#!/usr/bin/env python3
"""
Script de déploiement pour competitions/signals.py
À placer à la racine du projet Django et exécuter
"""

import os
import shutil
from datetime import datetime

def deploy_competitions_signal():
    """Déploie la correction pour competitions/signals.py"""
    
    print("🔧 DÉPLOIEMENT DE competitions/signals.py")
    print("=" * 45)
    
    # Chemin du fichier à corriger
    signal_file = "competitions/signals.py"
    
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
        
        # 3. APPLICATION DE LA CORRECTION
        print("🔄 Application de la correction...")
        
        # Rechercher et remplacer la ligne problématique
        old_line = '                    defaults={"is_active": True}'
        new_line = '''                    defaults={
                        "is_active": bool(True),
                        "is_federation_validated": bool(False)
                    }'''
        
        if old_line in content:
            content = content.replace(old_line, new_line)
            print("✅ Correction appliquée")
        else:
            # Essayer une autre variante
            old_line_alt = 'defaults={"is_active": True}'
            if old_line_alt in content:
                new_line_alt = '''defaults={
                        "is_active": bool(True),
                        "is_federation_validated": bool(False)
                    }'''
                content = content.replace(old_line_alt, new_line_alt)
                print("✅ Correction appliquée (variante)")
            else:
                print("⚠️  Pattern à corriger non trouvé - fichier peut-être déjà corrigé")
        
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
        print("✅ Fichier: competitions/signals.py")
        print("✅ Correction: PractitionerQRCode boolean fields")
        print("✅ Change: is_active: True → bool(True)")
        print("✅ Ajout: is_federation_validated: bool(False)")
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
    print("🚀 SCRIPT DE DÉPLOIEMENT - COMPETITIONS SIGNAL")
    print("=" * 50)
    print("🎯 Objectif: Corriger l'erreur boolean PostgreSQL")
    print("📂 Fichier: competitions/signals.py")
    print()
    
    success = deploy_competitions_signal()
    
    print()
    print("=" * 50)
    
    if success:
        print("🎉 DÉPLOIEMENT RÉUSSI!")
        print()
        print("📋 ÉTAPES SUIVANTES:")
        print("1. Exécuter le script pour grades/signals.py")
        print("2. Redémarrer Django (si en production):")
        print("   sudo systemctl restart martialcomp")
        print("3. Tester l'ajout d'un pratiquant")
        
    else:
        print("❌ DÉPLOIEMENT ÉCHOUÉ")
        print("   Le fichier original a été restauré")
        print("   Vérifiez les erreurs ci-dessus")
    
    print()
    print("🔧 Pour restaurer manuellement:")
    print(f"   cp competitions/signals.py.backup_* competitions/signals.py")

if __name__ == "__main__":
    main()