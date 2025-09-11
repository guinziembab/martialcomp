#!/usr/bin/env python3
"""
Nettoyeur global de BOM pour tous les fichiers Python du projet MartialComp
Traite le problème systémique de caractères U+FEFF dans les fichiers Python
"""

import os
import sys
from pathlib import Path
import subprocess

class GlobalBOMCleaner:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.files_processed = 0
        self.files_cleaned = 0
        self.files_with_bom = []
        self.errors = []
        
        # Dossiers à exclure
        self.exclude_dirs = {
            '.venv', 'venv', 'env', '.env',
            '__pycache__', '.git', '.idea', '.vscode',
            'node_modules', 'build', 'dist', '.pytest_cache',
            'temp_venv', '.tox', '.mypy_cache'
        }
        
        # Extensions à traiter
        self.target_extensions = {'.py'}
        
    def should_skip_path(self, path):
        """Détermine si un chemin doit être ignoré"""
        path_parts = path.parts
        
        # Vérifier si le chemin contient un dossier exclu
        for part in path_parts:
            if part in self.exclude_dirs:
                return True
                
        return False
    
    def detect_bom(self, file_path):
        """Détecte la présence de BOM dans un fichier"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read(10)  # Lire seulement les premiers bytes
                
            # Types de BOM
            bom_patterns = [
                (b'\xef\xbb\xbf', 'UTF-8'),
                (b'\xff\xfe', 'UTF-16 LE'),
                (b'\xfe\xff', 'UTF-16 BE'),
                (b'\x00\x00\xfe\xff', 'UTF-32 BE'),
                (b'\xff\xfe\x00\x00', 'UTF-32 LE'),
            ]
            
            for bom_bytes, bom_name in bom_patterns:
                if content.startswith(bom_bytes):
                    return bom_name, len(bom_bytes)
                    
            return None, 0
            
        except Exception as e:
            self.errors.append(f"Erreur lecture {file_path}: {e}")
            return None, 0
    
    def remove_bom_from_file(self, file_path):
        """Supprime le BOM d'un fichier"""
        try:
            # Lecture du fichier en binaire
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Détection et suppression de BOM
            bom_removed = False
            original_size = len(content)
            
            bom_patterns = [
                b'\xef\xbb\xbf',      # UTF-8 BOM
                b'\xff\xfe',          # UTF-16 LE BOM
                b'\xfe\xff',          # UTF-16 BE BOM
                b'\x00\x00\xfe\xff', # UTF-32 BE BOM
                b'\xff\xfe\x00\x00', # UTF-32 LE BOM
            ]
            
            for bom_pattern in bom_patterns:
                if content.startswith(bom_pattern):
                    # Supprimer le BOM
                    content = content[len(bom_pattern):]
                    bom_removed = True
                    break
            
            if bom_removed:
                # Sauvegarde du fichier original
                backup_path = str(file_path) + '.bom_backup'
                with open(file_path, 'rb') as original:
                    with open(backup_path, 'wb') as backup:
                        backup.write(original.read())
                
                # Réécriture du fichier nettoyé
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                print(f"✅ BOM supprimé de: {file_path}")
                print(f"   Taille: {original_size} → {len(content)} bytes")
                print(f"   Sauvegarde: {backup_path}")
                
                return True
            
            return False
            
        except Exception as e:
            self.errors.append(f"Erreur nettoyage {file_path}: {e}")
            return False
    
    def validate_python_syntax(self, file_path):
        """Valide la syntaxe Python d'un fichier après nettoyage"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            compile(content, str(file_path), 'exec')
            return True, None
            
        except SyntaxError as e:
            return False, f"Syntaxe: {e}"
        except Exception as e:
            return False, f"Erreur: {e}"
    
    def scan_and_clean_directory(self):
        """Scanne et nettoie tous les fichiers Python du projet"""
        print(f"🔍 SCAN GLOBAL DU PROJET: {self.project_root.absolute()}")
        print("=" * 60)
        
        # Collecte des fichiers à traiter
        python_files = []
        
        for file_path in self.project_root.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in self.target_extensions and
                not self.should_skip_path(file_path)):
                python_files.append(file_path)
        
        print(f"📊 Fichiers Python trouvés: {len(python_files)}")
        
        if not python_files:
            print("❌ Aucun fichier Python trouvé !")
            return False
        
        # Traitement des fichiers
        for file_path in python_files:
            self.files_processed += 1
            
            try:
                bom_type, bom_length = self.detect_bom(file_path)
                
                if bom_type:
                    print(f"🚨 BOM {bom_type} détecté: {file_path}")
                    self.files_with_bom.append((file_path, bom_type))
                    
                    if self.remove_bom_from_file(file_path):
                        self.files_cleaned += 1
                        
                        # Validation de la syntaxe après nettoyage
                        is_valid, error = self.validate_python_syntax(file_path)
                        if not is_valid:
                            print(f"⚠️  Problème syntaxe après nettoyage: {error}")
                        else:
                            print(f"✅ Syntaxe validée: {file_path}")
                else:
                    # Validation de la syntaxe même sans BOM
                    is_valid, error = self.validate_python_syntax(file_path)
                    if not is_valid and "invalid non-printable character" in str(error):
                        print(f"🔍 Caractères invisibles détectés: {file_path}")
                        # Tentative de nettoyage des caractères invisibles
                        self.clean_invisible_characters(file_path)
                
            except Exception as e:
                self.errors.append(f"Erreur traitement {file_path}: {e}")
        
        return True
    
    def clean_invisible_characters(self, file_path):
        """Nettoie les caractères invisibles autres que BOM"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Caractères invisibles problématiques (encodés en UTF-8)
            invisible_chars = {
                '\ufeff': '',        # ZERO WIDTH NO-BREAK SPACE
                '\u200b': '',        # ZERO WIDTH SPACE  
                '\u200c': '',        # ZERO WIDTH NON-JOINER
                '\u200d': '',        # ZERO WIDTH JOINER
                '\u2060': '',        # WORD JOINER
            }
            
            original_content = content
            for char, replacement in invisible_chars.items():
                content = content.replace(char, replacement)
            
            if content != original_content:
                # Sauvegarde
                backup_path = str(file_path) + '.invisible_backup'
                with open(backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(original_content)
                
                # Réécriture nettoyée
                with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(content)
                
                print(f"🧹 Caractères invisibles supprimés: {file_path}")
                self.files_cleaned += 1
                return True
            
            return False
            
        except Exception as e:
            self.errors.append(f"Erreur nettoyage invisibles {file_path}: {e}")
            return False
    
    def show_summary(self):
        """Affiche le résumé des opérations"""
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DU NETTOYAGE GLOBAL")
        print("=" * 60)
        
        print(f"📁 Fichiers traités: {self.files_processed}")
        print(f"🧹 Fichiers nettoyés: {self.files_cleaned}")
        print(f"🚨 Fichiers avec BOM: {len(self.files_with_bom)}")
        print(f"❌ Erreurs: {len(self.errors)}")
        
        if self.files_with_bom:
            print(f"\n🔍 FICHIERS AVEC BOM DÉTECTÉ:")
            for file_path, bom_type in self.files_with_bom:
                print(f"   • {bom_type}: {file_path}")
        
        if self.errors:
            print(f"\n❌ ERREURS RENCONTRÉES:")
            for error in self.errors[:10]:  # Afficher max 10 erreurs
                print(f"   • {error}")
            if len(self.errors) > 10:
                print(f"   ... et {len(self.errors) - 10} autres erreurs")
    
    def run_final_django_test(self):
        """Lance un test Django pour vérifier que tout fonctionne"""
        print(f"\n🧪 TEST DJANGO FINAL")
        print("=" * 30)
        
        try:
            result = subprocess.run([
                sys.executable, 'manage.py', 'check'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Django check: SUCCÈS !")
                return True
            else:
                print("❌ Django check: ÉCHEC")
                print("STDOUT:", result.stdout[-500:])  # Dernières 500 chars
                print("STDERR:", result.stderr[-500:])
                return False
                
        except subprocess.TimeoutExpired:
            print("⏱️  Timeout lors du test Django")
            return False
        except Exception as e:
            print(f"❌ Erreur test Django: {e}")
            return False

def main():
    """Fonction principale"""
    print("🧹 NETTOYEUR GLOBAL DE BOM - MARTIALCOMP")
    print("=" * 60)
    
    cleaner = GlobalBOMCleaner()
    
    if cleaner.scan_and_clean_directory():
        cleaner.show_summary()
        
        if cleaner.files_cleaned > 0:
            print(f"\n💡 RECOMMANDATIONS:")
            print(f"1. Testez Django: python manage.py check")
            print(f"2. Configurez votre éditeur pour UTF-8 sans BOM")
            print(f"3. Les sauvegardes sont créées avec extension .bom_backup")
            
            # Test Django automatique
            success = cleaner.run_final_django_test()
            
            if success:
                print(f"\n🎉 SUCCÈS TOTAL ! Projet nettoyé et fonctionnel.")
                print(f"💻 Lancez maintenant: python manage.py runserver")
            else:
                print(f"\n⚠️  Nettoyage terminé mais Django a encore des erreurs.")
        else:
            print(f"\n✅ Aucun nettoyage nécessaire. Projet déjà propre.")
    else:
        print(f"\n❌ Échec du scan global.")

if __name__ == "__main__":
    main()