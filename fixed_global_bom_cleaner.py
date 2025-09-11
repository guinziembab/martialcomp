#!/usr/bin/env python3
"""
Nettoyeur global de BOM corrigé pour Windows
Gère correctement les liens symboliques et erreurs d'accès
"""

import os
import sys
from pathlib import Path
import subprocess

def fix_categories_file_immediately():
    """Correction immédiate du fichier categories.py qui pose problème"""
    categories_file = Path("apps/competitions/views/onboarding/categories.py")
    
    print("🚨 CORRECTION URGENTE: categories.py")
    print("=" * 40)
    
    if not categories_file.exists():
        print("❌ Fichier categories.py non trouvé")
        return False
    
    try:
        # Lecture en binaire pour détecter BOM
        with open(categories_file, 'rb') as f:
            raw_content = f.read()
        
        print(f"📊 Taille originale: {len(raw_content)} bytes")
        print(f"🔍 Premiers bytes: {raw_content[:10].hex()}")
        
        # Détecter et supprimer BOM UTF-8
        if raw_content.startswith(b'\xef\xbb\xbf'):
            print("🚨 BOM UTF-8 détecté dans categories.py !")
            
            # Supprimer BOM
            clean_content = raw_content[3:]  # Enlever les 3 premiers bytes
            
            # Sauvegarde
            backup_file = categories_file.with_suffix('.py.bom_backup')
            with open(backup_file, 'wb') as backup:
                backup.write(raw_content)
            print(f"💾 Sauvegarde: {backup_file}")
            
            # Réécriture propre
            with open(categories_file, 'wb') as f:
                f.write(clean_content)
            
            print(f"✅ BOM supprimé ! Nouvelle taille: {len(clean_content)} bytes")
            
            # Test syntaxe
            try:
                with open(categories_file, 'r', encoding='utf-8') as f:
                    content_text = f.read()
                compile(content_text, str(categories_file), 'exec')
                print("✅ Syntaxe Python validée")
                return True
            except SyntaxError as e:
                print(f"❌ Erreur syntaxe: {e}")
                return False
                
        else:
            print("ℹ️ Aucun BOM UTF-8 détecté")
            # Vérifier s'il y a d'autres caractères invisibles
            try:
                content_text = raw_content.decode('utf-8')
                compile(content_text, str(categories_file), 'exec')
                print("✅ Fichier déjà propre")
                return True
            except UnicodeDecodeError:
                print("❌ Problème d'encodage détecté")
                return False
            except SyntaxError as e:
                print(f"❌ Erreur syntaxe: {e}")
                return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def safe_scan_python_files():
    """Scan sécurisé des fichiers Python évitant les erreurs Windows"""
    python_files = []
    problematic_paths = []
    
    print("🔍 SCAN SÉCURISÉ DES FICHIERS PYTHON")
    print("=" * 40)
    
    # Dossiers à scanner (éviter les environnements virtuels)
    target_dirs = [
        "apps",
        "config", 
        "static",
        "templates"
    ]
    
    # Scan des dossiers ciblés
    for target_dir in target_dirs:
        target_path = Path(target_dir)
        if target_path.exists():
            print(f"📁 Scan: {target_dir}")
            
            try:
                for py_file in target_path.rglob("*.py"):
                    try:
                        # Test d'accès au fichier
                        if py_file.is_file():
                            # Test de lecture rapide
                            with open(py_file, 'rb') as f:
                                f.read(10)  # Juste les premiers bytes
                            python_files.append(py_file)
                    except (OSError, PermissionError) as e:
                        problematic_paths.append((py_file, str(e)))
                        
            except Exception as e:
                print(f"⚠️ Erreur scan {target_dir}: {e}")
    
    # Scan des fichiers Python à la racine
    try:
        for py_file in Path(".").glob("*.py"):
            if py_file.is_file():
                python_files.append(py_file)
    except Exception as e:
        print(f"⚠️ Erreur scan racine: {e}")
    
    print(f"📊 Fichiers Python accessibles: {len(python_files)}")
    if problematic_paths:
        print(f"⚠️ Fichiers inaccessibles: {len(problematic_paths)}")
    
    return python_files

def clean_bom_from_files(python_files):
    """Nettoie le BOM des fichiers Python"""
    files_cleaned = 0
    files_with_issues = []
    
    print(f"\n🧹 NETTOYAGE DES FICHIERS")
    print("=" * 30)
    
    for py_file in python_files:
        try:
            # Lecture binaire
            with open(py_file, 'rb') as f:
                raw_content = f.read()
            
            original_size = len(raw_content)
            needs_cleaning = False
            
            # Détecter BOM UTF-8
            if raw_content.startswith(b'\xef\xbb\xbf'):
                print(f"🚨 BOM UTF-8: {py_file}")
                raw_content = raw_content[3:]
                needs_cleaning = True
            
            # Détecter autres BOM
            elif raw_content.startswith(b'\xff\xfe'):
                print(f"🚨 BOM UTF-16 LE: {py_file}")
                raw_content = raw_content[2:]
                needs_cleaning = True
            
            elif raw_content.startswith(b'\xfe\xff'):
                print(f"🚨 BOM UTF-16 BE: {py_file}")
                raw_content = raw_content[2:]
                needs_cleaning = True
            
            if needs_cleaning:
                # Sauvegarde
                backup_file = py_file.with_suffix('.py.auto_backup')
                with open(backup_file, 'wb') as backup:
                    with open(py_file, 'rb') as original:
                        backup.write(original.read())
                
                # Réécriture
                with open(py_file, 'wb') as f:
                    f.write(raw_content)
                
                files_cleaned += 1
                print(f"✅ Nettoyé: {original_size} → {len(raw_content)} bytes")
                
                # Test syntaxe
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, str(py_file), 'exec')
                    print(f"✅ Syntaxe OK: {py_file}")
                except SyntaxError as e:
                    print(f"⚠️ Erreur syntaxe: {py_file} - {e}")
                    files_with_issues.append((py_file, str(e)))
                    
        except Exception as e:
            print(f"❌ Erreur traitement {py_file}: {e}")
            files_with_issues.append((py_file, str(e)))
    
    return files_cleaned, files_with_issues

def test_django():
    """Test Django après nettoyage"""
    print(f"\n🧪 TEST DJANGO")
    print("=" * 20)
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'check'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Django check: SUCCÈS !")
            return True
        else:
            print("❌ Django check: ERREURS DÉTECTÉES")
            # Afficher les dernières lignes d'erreur
            if result.stderr:
                error_lines = result.stderr.strip().split('\n')[-5:]
                print("Dernières erreurs:")
                for line in error_lines:
                    print(f"   {line}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️ Timeout - Django check trop long")
        return False
    except Exception as e:
        print(f"❌ Impossible de lancer Django check: {e}")
        return False

def main():
    """Fonction principale"""
    print("🧹 NETTOYEUR BOM SÉCURISÉ - WINDOWS")
    print("=" * 50)
    
    # 1. Correction urgente de categories.py
    categories_fixed = fix_categories_file_immediately()
    
    # 2. Scan et nettoyage global sécurisé
    python_files = safe_scan_python_files()
    
    if python_files:
        files_cleaned, issues = clean_bom_from_files(python_files)
        
        print(f"\n📊 RÉSUMÉ")
        print("=" * 20)
        print(f"📁 Fichiers traités: {len(python_files)}")
        print(f"🧹 Fichiers nettoyés: {files_cleaned}")
        print(f"⚠️ Fichiers avec problèmes: {len(issues)}")
        
        if issues:
            print(f"\n⚠️ PROBLÈMES DÉTECTÉS:")
            for file_path, error in issues[:5]:  # Max 5 erreurs
                print(f"   • {file_path}: {error}")
    
    # 3. Test Django final
    django_ok = test_django()
    
    print(f"\n🎯 STATUT FINAL")
    print("=" * 20)
    print(f"categories.py: {'✅' if categories_fixed else '❌'}")
    print(f"Django check: {'✅' if django_ok else '❌'}")
    
    if categories_fixed and django_ok:
        print(f"\n🎉 SUCCÈS ! Projet fonctionnel.")
        print(f"💻 Commande: python manage.py runserver")
    elif categories_fixed:
        print(f"\n⚠️ categories.py corrigé, mais Django a encore des erreurs.")
    else:
        print(f"\n❌ Correction requise pour categories.py")

if __name__ == "__main__":
    main()