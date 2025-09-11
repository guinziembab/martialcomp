#!/usr/bin/env python3
"""
Script de déploiement sécurisé avec sauvegarde automatique
À exécuter sur le serveur de production
"""

import os
import shutil
import sys
from datetime import datetime

def create_backup_dir():
    """Crée un répertoire de sauvegarde horodaté"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"/opt/martialcomp/backups/signals_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def backup_files(backup_dir):
    """Sauvegarde les fichiers originaux"""
    files_to_backup = [
        "/opt/martialcomp/app/competitions/signals.py",
        "/opt/martialcomp/app/grades/signals.py"
    ]
    
    backed_up = []
    
    print("💾 SAUVEGARDE DES FICHIERS ORIGINAUX")
    print("=" * 40)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            # Nom du fichier de sauvegarde
            filename = os.path.basename(file_path).replace('.py', '.py.backup')
            backup_path = os.path.join(backup_dir, filename)
            
            # Copier le fichier
            shutil.copy2(file_path, backup_path)
            backed_up.append((file_path, backup_path))
            print(f"✅ Sauvegardé: {file_path}")
            print(f"   → {backup_path}")
        else:
            print(f"⚠️  Fichier non trouvé: {file_path}")
    
    return backed_up

def apply_competitions_fix(file_path):
    """Applique la correction au fichier competitions/signals.py"""
    try:
        # Backup immédiat
        shutil.copy2(file_path, f"{file_path}.backup_{datetime.now().strftime('%H%M%S')}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Appliquer la correction
        old_pattern = 'defaults={"is_active": True}'
        new_pattern = '''defaults={
                        "is_active": bool(True),
                        "is_federation_validated": bool(False)
                    }'''
        
        content = content.replace(old_pattern, new_pattern)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def apply_grades_fix(file_path):
    """Applique les corrections au fichier grades/signals.py"""
    try:
        # Backup immédiat
        shutil.copy2(file_path, f"{file_path}.backup_{datetime.now().strftime('%H%M%S')}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Appliquer les corrections
        corrections = [
            ('is_current = True', 'is_current = bool(True)'),
            ('is_current=True', 'is_current=bool(True)'),
            ('is_current=False', 'is_current=bool(False)'),
            ('certificate_issued = True', 'certificate_issued = bool(True)'),
            ('.update(is_current=False)', '.update(is_current=bool(False))')
        ]
        
        for old, new in corrections:
            content = content.replace(old, new)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def validate_syntax(file_path):
    """Valide la syntaxe Python du fichier"""
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'py_compile', file_path], 
                          capture_output=True, text=True)
    return result.returncode == 0

def main():
    print("🔒 DÉPLOIEMENT SÉCURISÉ DES CORRECTIONS DE SIGNAUX")
    print("=" * 55)
    print("🎯 Sauvegarde automatique + Application des corrections")
    print()
    
    # 1. Créer le répertoire de sauvegarde
    backup_dir = create_backup_dir()
    print(f"📁 Répertoire de sauvegarde: {backup_dir}")
    print()
    
    # 2. Sauvegarder les fichiers originaux
    backed_up = backup_files(backup_dir)
    print()
    
    if not backed_up:
        print("❌ Aucun fichier sauvegardé - arrêt du script")
        return
    
    # 3. Appliquer les corrections
    print("🔧 APPLICATION DES CORRECTIONS")
    print("=" * 30)
    
    competitions_file = "/opt/martialcomp/app/competitions/signals.py"
    grades_file = "/opt/martialcomp/app/grades/signals.py"
    
    success_competitions = False
    success_grades = False
    
    if os.path.exists(competitions_file):
        print("🔄 Correction de competitions/signals.py...")
        success_competitions = apply_competitions_fix(competitions_file)
        if success_competitions:
            print("✅ competitions/signals.py corrigé")
        else:
            print("❌ Échec de la correction competitions/signals.py")
    
    if os.path.exists(grades_file):
        print("🔄 Correction de grades/signals.py...")
        success_grades = apply_grades_fix(grades_file)
        if success_grades:
            print("✅ grades/signals.py corrigé")
        else:
            print("❌ Échec de la correction grades/signals.py")
    
    # 4. Validation syntaxe
    print()
    print("🧪 VALIDATION SYNTAXE")
    print("=" * 20)
    
    if os.path.exists(competitions_file):
        if validate_syntax(competitions_file):
            print("✅ competitions/signals.py - syntaxe OK")
        else:
            print("❌ competitions/signals.py - erreur syntaxe")
    
    if os.path.exists(grades_file):
        if validate_syntax(grades_file):
            print("✅ grades/signals.py - syntaxe OK")
        else:
            print("❌ grades/signals.py - erreur syntaxe")
    
    # 5. Instructions finales
    print()
    print("📋 ÉTAPES SUIVANTES")
    print("=" * 18)
    print("1. 🔄 Redémarrer Django:")
    print("   sudo systemctl restart martialcomp")
    print()
    print("2. 📊 Surveiller les logs:")
    print("   sudo journalctl -u martialcomp -f")
    print()
    print("3. 🧪 Tester l'ajout d'un pratiquant")
    print()
    print("4. 🔄 En cas de problème, restaurer avec:")
    for original, backup in backed_up:
        print(f"   cp {backup} {original}")
    print("   sudo systemctl restart martialcomp")
    print()
    print(f"📁 Toutes les sauvegardes dans: {backup_dir}")
    
    if success_competitions or success_grades:
        print("\n🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!")
    else:
        print("\n⚠️  DÉPLOIEMENT PARTIEL - Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()