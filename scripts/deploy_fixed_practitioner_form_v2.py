#!/usr/bin/env python3
"""
Script pour déployer la correction complète du formulaire practitioners.py - VERSION 2
Corrige l'erreur 'invalid input syntax for type boolean' en production
"""

import os
import shutil
from datetime import datetime

def deploy_fix():
    """Déploie la correction sur le serveur de production"""
    
    print("🔧 DÉPLOIEMENT DE LA CORRECTION BOOLEAN POSTGRESQL - V2")
    print("=" * 60)
    
    # Chemins
    target_file = "/opt/martialcomp/app/competitions/forms/practitioners.py"
    backup_file = f"{target_file}.backup_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # 1. Backup de sécurité
        print(f"📁 Création du backup: {backup_file}")
        shutil.copy2(target_file, backup_file)
        
        # 2. Lire le fichier actuel
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 3. Trouver la ligne exacte à modifier
        lines = content.split('\n')
        new_lines = []
        in_save_method = False
        save_method_found = False
        
        for i, line in enumerate(lines):
            if "def save(self, commit=True):" in line:
                save_method_found = True
                in_save_method = True
                # Ajouter la méthode save() corrigée
                new_lines.append(line)
                new_lines.append("        # Fix boolean fields for PostgreSQL - avoid Unicode spaces and empty strings")
                new_lines.append("        if hasattr(self, 'instance') and self.instance:")
                new_lines.append("            for field_name in ['is_coach', 'is_active']:")
                new_lines.append("                if hasattr(self.instance, field_name):")
                new_lines.append("                    field_value = getattr(self.instance, field_name)")
                new_lines.append("                    # Convert problematic values to False")
                new_lines.append("                    if (isinstance(field_value, str) and")
                new_lines.append("                        (not field_value.strip() or '\\xa0' in field_value or field_value in ['', ' ', '  '])):")
                new_lines.append("                        setattr(self.instance, field_name, False)")
                new_lines.append("")
                # Continuer avec le reste de la méthode originale
                continue
            elif in_save_method and line.strip().startswith("def ") and not line.strip().startswith("def save"):
                # Fin de la méthode save(), arrêter de sauter les lignes
                in_save_method = False
                new_lines.append(line)
            elif not in_save_method:
                # Garder toutes les lignes qui ne sont pas dans save()
                new_lines.append(line)
            # Si in_save_method = True, on saute les lignes originales de save()
        
        if not save_method_found:
            print("❌ Méthode save() non trouvée")
            return False
        
        # 4. Écrire le fichier corrigé
        new_content = '\n'.join(new_lines)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Correction appliquée avec succès")
        
        # 5. Test de syntaxe Python
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
    print("🚀 SCRIPT DE CORRECTION FINALE - BOOLEAN POSTGRESQL V2")
    print("=" * 70)
    print("🎯 Objectif: Corriger l'erreur 'invalid input syntax for type boolean'")
    print("📋 Méthode: Modifier uniquement le début de la méthode save()")
    print()
    
    # Déployer la correction
    success = deploy_fix()
    
    print("\n" + "=" * 70)
    
    if success:
        print("🎉 CORRECTION DÉPLOYÉE AVEC SUCCÈS!")
        print("\n📋 ÉTAPES SUIVANTES:")
        print("1. 🔄 Redémarrer Django:")
        print("   sudo systemctl restart martialcomp")
        print("2. 🧪 Tester l'enregistrement d'un practitioner")
        print("3. ✅ Vérifier que l'erreur boolean est résolue")
        
    else:
        print("❌ ÉCHEC DU DÉPLOIEMENT")
        print("   Le fichier original a été restauré automatiquement")
    
    print(f"\n📁 Backup disponible: practitioners.py.backup_v2_*")

if __name__ == "__main__":
    main()