#!/usr/bin/env python3
"""
Correcteur complet pour le fichier club.py
Corrige l'indentation, l'encodage UTF-8 et les imports manquants
"""

import os
import re

def fix_club_file_completely():
    """Corrige complètement le fichier club.py"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    print(f"🔧 CORRECTION COMPLÈTE DE: {file_path}")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print("❌ Le fichier n'existe pas !")
        return False
    
    try:
        # Lecture du fichier
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📊 Taille originale: {len(content)} caractères")
        
        # Sauvegarde complète
        backup_path = file_path + ".complete_fix_backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Sauvegarde créée: {backup_path}")
        
        # === CORRECTION 1: Caractères UTF-8 corrompus ===
        print("🔧 Correction des caractères UTF-8...")
        
        utf8_corrections = {
            'CrÃ©ation': 'Création',
            'crÃ©ation': 'création',
            'crÃ©Ã©': 'créé',
            'AccÃ¨s': 'Accès',
            'accÃ¨s': 'accès',
            'ÃƒÂªtre': 'être',
            'dÃ©jÃƒ': 'déjà',
            'dÃ©jÃ': 'déjà',
            'terminÃ©e': 'terminée',
            'terminÃ©': 'terminé',
            'succÃ¨s': 'succès',
            'Ã©tÃ©': 'été',
            'Ã©tape': 'étape',
            'rÃ©cupÃ©ration': 'récupération',
            'RÃ©cupÃ©ration': 'Récupération',
            'dÃ©tails': 'détails',
            'DÃ©tails': 'Détails',
            'additionnels': 'additionnels',
            'Ã ': 'à ',
            'Ãƒ ': 'à ',
            'mise Ãƒ  jour': 'mise à jour',
            'Passage Ãƒ  l': 'Passage à l',
            'catÃ©gories': 'catégories',
            'SÃ©curisation': 'Sécurisation',
            'sÃ©curisation': 'sécurisation',
            'associÃ©es': 'associées',
            'rÃ©cupÃ©ration': 'récupération',
            'complÃ©tÃ©': 'complété',
            'Ã©quipements': 'équipements',
            'vÃ©rification': 'vérification',
            'entrainement': 'entraînement',
            'pratiquants': 'pratiquants',
            'connectÃ©': 'connecté',
            'propriÃ©taire': 'propriétaire',
            'diffÃ©rentes': 'différentes',
            'rÃ©cupÃ©rer': 'récupérer',
            'RÃ©cupÃ©rer': 'Récupérer'
        }
        
        corrected_content = content
        corrections_made = 0
        
        for wrong, correct in utf8_corrections.items():
            if wrong in corrected_content:
                corrected_content = corrected_content.replace(wrong, correct)
                corrections_made += 1
                print(f"   ✓ {wrong} → {correct}")
        
        print(f"📊 {corrections_made} corrections UTF-8 appliquées")
        
        # === CORRECTION 2: Indentation ligne 2 ===
        print("🔧 Correction de l'indentation...")
        
        lines = corrected_content.splitlines()
        if len(lines) >= 2 and lines[1].startswith(' import'):
            lines[1] = lines[1].lstrip()  # Supprimer l'espace en début de ligne
            print("   ✓ Indentation ligne 2 corrigée")
        
        # === CORRECTION 3: Import manquant ===
        print("🔧 Ajout des imports manquants...")
        
        # Vérifier si Practitioner est utilisé mais non importé
        content_check = '\n'.join(lines)
        if 'Practitioner' in content_check and 'from ...models import' in content_check:
            # Trouver la ligne d'import des modèles et ajouter Practitioner
            for i, line in enumerate(lines):
                if line.startswith('from ...models import') and 'Practitioner' not in line:
                    # Ajouter Practitioner à l'import
                    if 'Club, Discipline' in line:
                        lines[i] = line.replace('Club, Discipline', 'Club, Discipline, Practitioner')
                        print("   ✓ Import Practitioner ajouté")
                    break
        
        # === CORRECTION 4: Nettoyage général ===
        print("🔧 Nettoyage général...")
        
        # Reconstruction du contenu
        corrected_content = '\n'.join(lines)
        
        # Supprimer les doubles espaces
        corrected_content = re.sub(r' {2,}', ' ', corrected_content)
        
        # Normaliser les fins de ligne
        corrected_content = corrected_content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Ajouter une fin de ligne si nécessaire
        if not corrected_content.endswith('\n'):
            corrected_content += '\n'
        
        # === SAUVEGARDE ===
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(corrected_content)
        
        print(f"✅ Fichier corrigé complètement !")
        print(f"📊 Nouvelle taille: {len(corrected_content)} caractères")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def validate_corrected_file():
    """Valide le fichier corrigé"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    print("🧪 VALIDATION DU FICHIER CORRIGÉ")
    print("=" * 30)
    
    try:
        # Test de syntaxe Python
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        print("✅ Syntaxe Python: VALIDE")
        
        # Vérification des imports
        if 'import logging' in content and not content.find('import logging') > content.find(' import logging'):
            print("✅ Import logging: CORRECT")
        else:
            print("⚠️  Import logging: VÉRIFIEZ")
        
        # Vérification UTF-8
        problematic_chars = ['CrÃ©', 'AccÃ¨', 'ÃƒÂª', 'dÃ©jÃƒ', 'Ã ']
        utf8_issues = any(char in content for char in problematic_chars)
        
        if not utf8_issues:
            print("✅ Encodage UTF-8: PROPRE")
        else:
            print("⚠️  Encodage UTF-8: ENCORE DES PROBLÈMES")
        
        # Vérification imports
        if 'Practitioner' in content:
            if 'from ...models import' in content and 'Practitioner' in content:
                models_import_line = [line for line in content.splitlines() if 'from ...models import' in line][0]
                if 'Practitioner' in models_import_line:
                    print("✅ Import Practitioner: CORRECT")
                else:
                    print("⚠️  Import Practitioner: MANQUANT")
            else:
                print("⚠️  Import Practitioner: À VÉRIFIER")
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe: {e}")
        print(f"   Ligne {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Erreur de validation: {e}")
        return False

def show_file_preview():
    """Affiche un aperçu du fichier corrigé"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    print("👁️  APERÇU DU FICHIER CORRIGÉ")
    print("=" * 30)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("Premières lignes:")
        for i, line in enumerate(lines[:10], 1):
            print(f"{i:2}: {line.rstrip()}")
        
        if len(lines) > 10:
            print(f"... ({len(lines) - 10} lignes supplémentaires)")
        
    except Exception as e:
        print(f"❌ Erreur d'aperçu: {e}")

def main():
    """Fonction principale"""
    print("🚀 CORRECTEUR COMPLET POUR club.py")
    print("=" * 50)
    
    # Correction complète
    if fix_club_file_completely():
        print("\n" + "=" * 50)
        
        # Validation
        if validate_corrected_file():
            print("\n" + "=" * 50)
            show_file_preview()
            
            print("\n🎉 SUCCÈS COMPLET !")
            print("💡 Testez maintenant:")
            print("   python manage.py check")
            print("   python manage.py runserver")
        else:
            print("\n⚠️  Validation échouée, vérification manuelle requise.")
    else:
        print("\n❌ Correction échouée.")

if __name__ == "__main__":
    main()