#!/usr/bin/env python3
"""
Correcteur d'urgence d'indentation pour club.py
Spécialement conçu pour corriger l'erreur de la ligne 19-20
"""

import os
import re

def fix_indentation_emergency():
    """Corrige spécifiquement l'indentation du fichier club.py"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    print(f"🚨 CORRECTION D'URGENCE D'INDENTATION: {file_path}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print("❌ Le fichier n'existe pas !")
        return False
    
    try:
        # Lecture du fichier ligne par ligne
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📊 Nombre de lignes: {len(lines)}")
        
        # Sauvegarde d'urgence
        backup_path = file_path + ".emergency_backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"💾 Sauvegarde d'urgence: {backup_path}")
        
        # Analyse et correction des lignes problématiques
        corrected_lines = []
        in_function = False
        function_indent = 0
        
        for i, line in enumerate(lines, 1):
            original_line = line
            stripped = line.strip()
            
            # Ignorer les lignes vides et commentaires
            if not stripped or stripped.startswith('#'):
                corrected_lines.append(line)
                continue
            
            # Détecter les déclarations de fonction
            if stripped.startswith('def ') or stripped.startswith('class '):
                in_function = True
                function_indent = 0
                corrected_lines.append(line.lstrip() + '\n' if not line.lstrip().endswith('\n') else line.lstrip())
                print(f"🔍 Ligne {i}: Fonction/classe détectée")
                continue
            
            # Détecter la fin de fonction (ligne sans indentation qui n'est pas import/from)
            elif not line.startswith((' ', '\t')) and not stripped.startswith(('import ', 'from ')) and in_function:
                in_function = False
                function_indent = 0
            
            # Imports et déclarations de niveau module (pas d'indentation)
            elif stripped.startswith(('import ', 'from ', 'logger ')) and i <= 15:
                corrected_line = stripped + '\n'
                corrected_lines.append(corrected_line)
                if original_line != corrected_line:
                    print(f"🔧 Ligne {i}: Import corrigé")
                continue
            
            # Dans une fonction
            elif in_function:
                # Mots-clés qui définissent des blocs
                block_keywords = ['if ', 'elif ', 'else:', 'try:', 'except', 'for ', 'while ', 'with ', 'def ', 'class ']
                is_block_start = any(stripped.startswith(kw) for kw in block_keywords)
                
                # Docstrings
                if stripped.startswith(('"""', "'''")):
                    corrected_line = '    ' + stripped + '\n'
                    corrected_lines.append(corrected_line)
                    print(f"🔧 Ligne {i}: Docstring indenté")
                    continue
                
                # Décorateurs
                elif stripped.startswith('@'):
                    corrected_line = stripped + '\n'
                    corrected_lines.append(corrected_line)
                    continue
                
                # Début de blocs (if, try, etc.) - indentation de base
                elif is_block_start:
                    corrected_line = '    ' + stripped + '\n'
                    corrected_lines.append(corrected_line)
                    if original_line.strip() != corrected_line.strip():
                        print(f"🔧 Ligne {i}: Bloc de contrôle indenté - {stripped[:30]}...")
                    continue
                
                # Contenu des blocs - indentation double
                else:
                    # Vérifier si la ligne précédente était un bloc
                    prev_line = lines[i-2].strip() if i > 1 else ""
                    prev_is_block = any(prev_line.startswith(kw) for kw in block_keywords)
                    
                    if prev_is_block or (i >= 20 and 'messages.' in stripped):  # Ligne 20 spécifique
                        corrected_line = '        ' + stripped + '\n'  # Double indentation
                        corrected_lines.append(corrected_line)
                        if original_line.strip() != corrected_line.strip():
                            print(f"🔧 Ligne {i}: Contenu de bloc indenté - {stripped[:30]}...")
                        continue
                    else:
                        # Indentation simple pour le code normal dans les fonctions
                        corrected_line = '    ' + stripped + '\n'
                        corrected_lines.append(corrected_line)
                        continue
            
            # Lignes normales (hors fonction)
            else:
                corrected_lines.append(line)
        
        # Vérification spécifique des lignes 19-20
        if len(corrected_lines) >= 20:
            line_19 = corrected_lines[18].strip()  # Index 18 = ligne 19
            line_20 = corrected_lines[19].strip()  # Index 19 = ligne 20
            
            print(f"🔍 Vérification ligne 19: {line_19}")
            print(f"🔍 Vérification ligne 20: {line_20}")
            
            # Si ligne 19 est un if et ligne 20 n'est pas indentée correctement
            if line_19.startswith('if ') and line_20.startswith('messages.'):
                if not corrected_lines[19].startswith('        '):  # 8 espaces
                    corrected_lines[19] = '        ' + line_20 + '\n'
                    print(f"🔧 CORRECTION SPÉCIALE ligne 20 appliquée")
        
        # Réécriture du fichier
        with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
            f.writelines(corrected_lines)
        
        print("✅ Correction d'indentation terminée !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def validate_syntax():
    """Valide la syntaxe du fichier corrigé"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    print("🧪 VALIDATION DE LA SYNTAXE")
    print("=" * 30)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, file_path, 'exec')
        print("✅ Syntaxe Python: VALIDE !")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erreur de syntaxe persistante:")
        print(f"   Ligne {e.lineno}: {e.text}")
        print(f"   Erreur: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Erreur de validation: {e}")
        return False

def show_problematic_lines():
    """Affiche les lignes autour du problème pour diagnostic"""
    file_path = "apps/competitions/views/onboarding/club.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("👁️  LIGNES AUTOUR DU PROBLÈME (15-25)")
        print("=" * 40)
        
        for i in range(14, min(25, len(lines))):  # Lignes 15-25
            line_num = i + 1
            line_content = lines[i].rstrip()
            indent_spaces = len(lines[i]) - len(lines[i].lstrip())
            
            print(f"{line_num:2}: [{indent_spaces:2}] {repr(line_content)}")
        
    except Exception as e:
        print(f"❌ Erreur d'affichage: {e}")

def main():
    """Fonction principale"""
    print("🚨 CORRECTEUR D'URGENCE - INDENTATION club.py")
    print("=" * 60)
    
    # Affichage des lignes problématiques avant correction
    print("AVANT CORRECTION:")
    show_problematic_lines()
    
    print("\n" + "=" * 60)
    
    # Correction d'urgence
    if fix_indentation_emergency():
        print("\nAPRÈS CORRECTION:")
        show_problematic_lines()
        
        print("\n" + "=" * 60)
        
        # Validation
        if validate_syntax():
            print("\n🎉 SUCCÈS ! Le fichier est maintenant syntaxiquement correct.")
            print("\n💡 Testez maintenant:")
            print("   python manage.py check")
            print("   python manage.py runserver")
        else:
            print("\n⚠️  Validation échouée. Vérification manuelle requise.")
    else:
        print("\n❌ Correction d'urgence échouée.")

if __name__ == "__main__":
    main()