#!/usr/bin/env python3
"""
Script flexible pour déployer les corrections des signaux Django
Peut être utilisé en local ou adapté pour la production
"""

import os
import shutil
from datetime import datetime

def find_django_project():
    """Trouve le répertoire du projet Django"""
    possible_paths = [
        "/opt/martialcomp/app",
        "/home/django/martialcomp",
        "/var/www/martialcomp",
        ".",
        "/mnt/c/martial_hub_django/martialcomp"
    ]
    
    for path in possible_paths:
        if os.path.exists(os.path.join(path, "manage.py")):
            return path
    
    return None

def apply_competitions_signal_fix(project_root):
    """Applique la correction au fichier competitions/signals.py"""
    
    signals_file = os.path.join(project_root, "competitions", "signals.py")
    
    if not os.path.exists(signals_file):
        print(f"❌ Fichier non trouvé: {signals_file}")
        return False
    
    backup_file = f"{signals_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Backup
        shutil.copy2(signals_file, backup_file)
        print(f"📁 Backup créé: {backup_file}")
        
        # Lire le fichier
        with open(signals_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Appliquer les corrections
        content = content.replace(
            'defaults={"is_active": True}',
            'defaults={\n                        "is_active": bool(True),\n                        "is_federation_validated": bool(False)\n                    }'
        )
        
        # Écrire le fichier corrigé
        with open(signals_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ competitions/signals.py corrigé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, signals_file)
        return False

def apply_grades_signal_fix(project_root):
    """Applique la correction au fichier grades/signals.py"""
    
    signals_file = os.path.join(project_root, "grades", "signals.py")
    
    if not os.path.exists(signals_file):
        print(f"❌ Fichier non trouvé: {signals_file}")
        return False
    
    backup_file = f"{signals_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Backup
        shutil.copy2(signals_file, backup_file)
        print(f"📁 Backup créé: {backup_file}")
        
        # Lire le fichier
        with open(signals_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Appliquer les corrections
        content = content.replace('is_current = True', 'is_current = bool(True)')
        content = content.replace('is_current=True', 'is_current=bool(True)')
        content = content.replace('is_current=False', 'is_current=bool(False)')
        content = content.replace('.update(is_current=False)', '.update(is_current=bool(False))')
        content = content.replace('certificate_issued = True', 'certificate_issued = bool(True)')
        
        # Écrire le fichier corrigé
        with open(signals_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ grades/signals.py corrigé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, signals_file)
        return False

def main():
    print("🚀 DÉPLOIEMENT FLEXIBLE DES CORRECTIONS DE SIGNAUX")
    print("=" * 60)
    
    # Trouver le projet Django
    project_root = find_django_project()
    
    if not project_root:
        print("❌ Impossible de trouver le projet Django")
        print("📋 Chemins vérifiés:")
        print("   - /opt/martialcomp/app")
        print("   - /home/django/martialcomp")
        print("   - /var/www/martialcomp")
        print("   - . (répertoire actuel)")
        return
    
    print(f"📁 Projet Django trouvé: {project_root}")
    print()
    
    # Appliquer les corrections
    success_competitions = apply_competitions_signal_fix(project_root)
    success_grades = apply_grades_signal_fix(project_root)
    
    print("\n" + "=" * 60)
    
    if success_competitions or success_grades:
        print("🎉 CORRECTIONS APPLIQUÉES!")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. 🔄 Redémarrer Django (si en production):")
        print("   sudo systemctl restart martialcomp")
        print("2. 🧪 Tester l'enregistrement d'un practitioner")
        print("3. ✅ Vérifier que l'erreur boolean est résolue")
        
        print("\n🔍 CORRECTIONS:")
        if success_competitions:
            print("   ✅ PractitionerQRCode boolean fields fixed")
        if success_grades:
            print("   ✅ PractitionerGrade boolean fields fixed")
        
    else:
        print("❌ AUCUNE CORRECTION APPLIQUÉE")
    
    print(f"\n📁 Backups disponibles dans: {project_root}")

if __name__ == "__main__":
    main()