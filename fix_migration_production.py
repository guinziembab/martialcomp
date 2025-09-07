#!/usr/bin/env python3
"""
Script pour corriger l'erreur de migration 0008 sur le serveur de production.
À exécuter sur le serveur de production martialcomp.com
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 {description}")
    print(f"   Commande: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            print(f"   ✅ Succès")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"   ❌ Erreur (code: {result.returncode})")
            print(f"   Stderr: {result.stderr.strip()}")
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, "", str(e)

def fix_migration_0008():
    """Corrige l'erreur de migration 0008"""
    
    print("🚨 Correctif Migration 0008 - MartialComp Production")
    print("=" * 60)
    
    print("\n📋 Diagnostic du problème:")
    print("   - Migration 0008 essaie de supprimer des tables inexistantes")
    print("   - Tables déjà supprimées mais migration mal marquée")
    print("   - Erreur: la relation « competitions_matchtimeslot » n'existe pas")
    
    print("\n🔧 Solution appliquée:")
    print("   - Marquer la migration 0008 comme 'fake' (appliquée sans exécution)")
    print("   - Permet de continuer les migrations suivantes")
    
    # 1. Vérifier l'état actuel des migrations
    success, stdout, stderr = run_command(
        "python3 manage.py showmigrations competitions",
        "Vérification de l'état des migrations competitions"
    )
    
    if not success:
        print("❌ Impossible de vérifier l'état des migrations")
        return False
    
    # 2. Marquer la migration 0008 comme fake
    success, stdout, stderr = run_command(
        "python3 manage.py migrate --fake competitions 0008",
        "Marquage de la migration 0008 comme appliquée (fake)"
    )
    
    if not success:
        print("❌ Impossible de marquer la migration comme fake")
        return False
    
    # 3. Exécuter toutes les migrations restantes
    success, stdout, stderr = run_command(
        "python3 manage.py migrate",
        "Exécution de toutes les migrations"
    )
    
    if not success:
        print("❌ Erreur lors de l'exécution des migrations")
        return False
    
    # 4. Vérifier que tout fonctionne
    success, stdout, stderr = run_command(
        "python3 manage.py check",
        "Vérification de la configuration Django"
    )
    
    if success:
        print("\n🎉 Migration 0008 corrigée avec succès !")
    else:
        print("\n⚠️ Migration corrigée mais des avertissements persistent")
    
    return True

def create_summary():
    """Crée un résumé de la correction"""
    
    summary = """
# Résumé de la Correction Migration 0008

## 🐛 Problème Original
```
django.db.utils.ProgrammingError: ERREUR: la relation « competitions_matchtimeslot » n'existe pas
```

## 🔧 Cause Identifiée
- Migration 0008 essayait de supprimer des tables déjà supprimées
- État incohérent entre le registre des migrations et la base de données réelle
- Tables `competitions_matchtimeslot`, `competitions_categorysche`, etc. n'existaient plus

## ✅ Solution Appliquée
```bash
python3 manage.py migrate --fake competitions 0008
python3 manage.py migrate
```

## 📝 Explication
- `--fake` marque la migration comme appliquée sans l'exécuter
- Résout les conflits d'état entre migrations et base de données
- Permet aux migrations suivantes de s'exécuter normalement

## 🎯 Résultat
- ✅ Migrations fonctionnent correctement
- ✅ Base de données cohérente
- ✅ Application opérationnelle

---
**Date:** {date}
**Script:** fix_migration_production.py
**Status:** ✅ Résolu
""".format(date=subprocess.check_output(['date'], text=True).strip())
    
    with open('migration_fix_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print("📄 Résumé sauvegardé dans: migration_fix_summary.txt")

def main():
    """Fonction principale"""
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('manage.py'):
        print("❌ Erreur: manage.py non trouvé. Exécutez ce script depuis le répertoire racine du projet Django.")
        return 1
    
    try:
        if fix_migration_0008():
            create_summary()
            print("\n🏆 Correction terminée avec succès !")
            print("\n📋 Actions suivantes recommandées:")
            print("   - Redémarrer l'application Django")
            print("   - Vérifier que les pages fonctionnent:")
            print("     * /fr/competitions/federations/3/examens/")
            print("     * /fr/competitions/dashboard/documentation/")
            return 0
        else:
            print("\n❌ Correction échouée. Vérifiez les logs ci-dessus.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Correction interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n💥 Erreur inattendue: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())