#!/usr/bin/env python3
"""
Script pour déployer la correction complète du formulaire practitioners.py
Corrige l'erreur 'invalid input syntax for type boolean' en production
"""

import os
import shutil
from datetime import datetime

def create_fixed_form():
    """Crée le fichier practitioners.py corrigé"""
    
    # Code de la méthode save() corrigée
    fixed_save_method = '''    def save(self, commit=True):
        # Fix boolean fields for PostgreSQL - avoid Unicode spaces and empty strings
        if hasattr(self, 'instance') and self.instance:
            for field_name in ['is_coach', 'is_active']:
                if hasattr(self.instance, field_name):
                    field_value = getattr(self.instance, field_name)
                    # Convert problematic values to False
                    if (isinstance(field_value, str) and 
                        (not field_value.strip() or '\\xa0' in field_value or field_value in ['', ' ', '  '])):
                        setattr(self.instance, field_name, False)
        
        practitioner = super().save(commit=commit)
        
        if commit:
            # Sauvegarder les grades
            self._save_grades(practitioner)
            # Sauvegarder les disciplines
            self._save_disciplines(practitioner)
        
        return practitioner'''
    
    return fixed_save_method

def deploy_fix():
    """Déploie la correction sur le serveur de production"""
    
    print("🔧 DÉPLOIEMENT DE LA CORRECTION BOOLEAN POSTGRESQL")
    print("=" * 60)
    
    # Chemins
    target_file = "/opt/martialcomp/app/competitions/forms/practitioners.py"
    backup_file = f"{target_file}.backup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 1. Backup de sécurité
        print(f"📁 Création du backup: {backup_file}")
        shutil.copy2(target_file, backup_file)
        
        # 2. Lire le fichier actuel
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3. Trouver et remplacer la méthode save()
        start_marker = "    def save(self, commit=True):"
        end_marker = "    def _save_grades(self, practitioner):"
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos == -1:
            print("❌ Impossible de trouver la méthode save()")
            return False
        
        if end_pos == -1:
            print("❌ Impossible de trouver la méthode _save_grades()")
            return False
        
        # 4. Remplacer la méthode save()
        fixed_method = create_fixed_form()
        new_content = (
            content[:start_pos] + 
            fixed_method + "\n\n    " +
            content[end_pos:]
        )
        
        # 5. Écrire le fichier corrigé
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Correction appliquée avec succès")
        
        # 6. Test de syntaxe Python
        import subprocess
        result = subprocess.run(['python3', '-m', 'py_compile', target_file], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Syntaxe Python validée")
            return True
        else:
            print(f"❌ Erreur de syntaxe: {result.stderr}")
            # Restaurer le backup
            shutil.copy2(backup_file, target_file)
            print("🔄 Backup restauré")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors du déploiement: {e}")
        
        # Restaurer le backup en cas d'erreur
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, target_file)
            print("🔄 Backup restauré automatiquement")
        
        return False

def main():
    print("🚀 SCRIPT DE CORRECTION FINALE - BOOLEAN POSTGRESQL")
    print("=" * 70)
    print("🎯 Objectif: Corriger l'erreur 'invalid input syntax for type boolean'")
    print("📋 Méthode: Remplacer complètement la méthode save() du formulaire")
    print()
    
    # Déployer la correction
    success = deploy_fix()
    
    print("\n" + "=" * 70)
    
    if success:
        print("🎉 CORRECTION DÉPLOYÉE AVEC SUCCÈS!")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. 🔄 Redémarrer Django:")
        print("   sudo systemctl restart martialcomp")
        print("2. 🧪 Tester l'enregistrement d'un practitioner:")
        print("   https://martialcomp.com/fr/competitions/club/practitioners/add/")
        print("3. ✅ Vérifier que l'erreur boolean est résolue")
        
        print("\n🔍 DÉTAILS DE LA CORRECTION:")
        print("   - Détection des valeurs Unicode problématiques (\\xa0)")
        print("   - Conversion automatique des chaînes vides en False")
        print("   - Gestion robuste des champs is_coach et is_active")
        print("   - Correction appliquée AVANT super().save()")
        
    else:
        print("❌ ÉCHEC DU DÉPLOIEMENT")
        print("   Le fichier original a été restauré automatiquement")
        print("   Vérifiez manuellement le fichier practitioners.py")
    
    print(f"\n📁 Backup disponible: practitioners.py.backup_final_*")
    print("🔧 Fichier corrigé: /opt/martialcomp/app/competitions/forms/practitioners.py")

if __name__ == "__main__":
    main()