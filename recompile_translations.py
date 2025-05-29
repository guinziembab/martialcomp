#!/usr/bin/env python3
"""
Script robuste pour compiler les fichiers .po en fichiers .mo
"""
import os
import subprocess
import sys
from pathlib import Path

# Répertoire de base du projet
BASE_DIR = Path(__file__).resolve().parent

def find_po_files():
    """Trouver tous les fichiers .po dans le répertoire locale."""
    po_files = []
    locale_dir = BASE_DIR / 'locale'
    
    if not locale_dir.exists():
        print(f"Erreur: Le répertoire {locale_dir} n'existe pas.")
        return []
    
    for root, dirs, files in os.walk(locale_dir):
        for file in files:
            if file.endswith('.po'):
                po_files.append(os.path.join(root, file))
    
    return po_files

def compile_po_file(po_file_path):
    """Compiler un fichier .po en .mo en utilisant msgfmt."""
    mo_file_path = po_file_path.replace('.po', '.mo')
    
    try:
        # Méthode 1: Utiliser msgfmt si disponible
        try:
            result = subprocess.run(
                ['msgfmt', po_file_path, '-o', mo_file_path],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Compilé avec succès: {po_file_path} -> {mo_file_path}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Impossible d'utiliser msgfmt: {str(e)}")
            
            # Méthode 2: Utiliser la méthode par compilation Python
            try:
                # Première tentative avec polib si disponible
                import polib
                po = polib.pofile(po_file_path)
                po.save_as_mofile(mo_file_path)
                print(f"✓ Compilé avec polib: {po_file_path} -> {mo_file_path}")
                return True
            except ImportError:
                print("polib n'est pas installé. Tentative avec méthode manuelle...")
                
                # Suggestion d'installer polib
                print("CONSEIL: Vous pouvez installer polib pour une meilleure compilation:")
                print("  python3 install_polib.py")
                
                # Méthode 3: Compilation manuelle (basique, mais fonctionnelle)
                try:
                    # Utiliser notre classe msgfmt interne définie dans ce script
                    msgfmt.make(po_file_path, mo_file_path)
                    print(f"✓ Compilé manuellement: {po_file_path} -> {mo_file_path}")
                    return True
                except Exception as e:
                    print(f"Échec de la compilation manuelle: {str(e)}")
                    return False
    except Exception as e:
        print(f"Erreur lors de la compilation de {po_file_path}: {str(e)}")
        return False

# Module de compilation de fichiers .mo amélioré pour usage interne
# Basé sur le format .mo standard (https://www.gnu.org/software/gettext/manual/html_node/MO-Files.html)
class msgfmt:
    """
    Compilateur de fichier .po vers .mo
    Implémentation plus conforme au format .mo standard
    """
    @staticmethod
    def make(infile, outfile):
        try:
            with open(infile, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extraire les paires msgid/msgstr
            translations = []
            msgid = ""
            msgstr = ""
            in_msgid = False
            in_msgstr = False
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('msgid '):
                    if in_msgstr and msgid:
                        translations.append((msgid, msgstr))
                    in_msgid = True
                    in_msgstr = False
                    msgid = line[6:].strip('"')
                elif line.startswith('msgstr '):
                    in_msgid = False
                    in_msgstr = True
                    msgstr = line[7:].strip('"')
                elif in_msgid and line.startswith('"') and line.endswith('"'):
                    msgid += line.strip('"')
                elif in_msgstr and line.startswith('"') and line.endswith('"'):
                    msgstr += line.strip('"')
            
            # Ajouter la dernière entrée
            if in_msgstr and msgid:
                translations.append((msgid, msgstr))
            
            # Trier les entrées pour assurer un format cohérent
            translations.sort()
            
            # Préparer les données pour le fichier .mo
            original_strings = []
            translated_strings = []
            
            for orig, trans in translations:
                if orig:  # Ignorer les entrées vides
                    original_strings.append(orig)
                    translated_strings.append(trans)
            
            # Compiler selon le format .mo standard
            with open(outfile, 'wb') as f:
                # Écrire l'en-tête .mo
                count = len(original_strings)
                
                # Magic number (0x950412de en little endian)
                f.write(bytes((0xde, 0x12, 0x04, 0x95)))
                
                # Version MO (0)
                f.write(bytes((0, 0, 0, 0)))
                
                # Nombre d'entrées
                f.write(count.to_bytes(4, byteorder='little'))
                
                # Offset de la table originale (juste après l'en-tête)
                original_table_offset = 28  # 7 mots de 4 octets (28 octets)
                f.write(original_table_offset.to_bytes(4, byteorder='little'))
                
                # Offset de la table traduite (après la table originale)
                translated_table_offset = original_table_offset + count * 8
                f.write(translated_table_offset.to_bytes(4, byteorder='little'))
                
                # Taille de la table de hachage (non utilisée, 0)
                f.write(bytes((0, 0, 0, 0)))
                
                # Offset de la table de hachage (non utilisée, juste après la table traduite)
                hash_table_offset = translated_table_offset + count * 8
                f.write(hash_table_offset.to_bytes(4, byteorder='little'))
                
                # Calculer les positions des chaînes
                strings_offset = hash_table_offset
                
                # Tables de référence (original et traduction)
                offsets = []
                strings_data = []
                
                for i in range(count):
                    orig = original_strings[i]
                    trans = translated_strings[i]
                    
                    # Ajouter les données originales
                    orig_encoded = orig.encode('utf-8') + b'\0'
                    orig_len = len(orig_encoded)
                    offsets.append((orig_len, strings_offset))
                    strings_data.append(orig_encoded)
                    strings_offset += orig_len
                    
                    # Ajouter les données traduites
                    trans_encoded = trans.encode('utf-8') + b'\0'
                    trans_len = len(trans_encoded)
                    offsets.append((trans_len, strings_offset))
                    strings_data.append(trans_encoded)
                    strings_offset += trans_len
                
                # Écrire les tables de référence
                for i in range(count):
                    # Table originale
                    f.write(offsets[i*2][0].to_bytes(4, byteorder='little'))
                    f.write(offsets[i*2][1].to_bytes(4, byteorder='little'))
                
                for i in range(count):
                    # Table traduite
                    f.write(offsets[i*2+1][0].to_bytes(4, byteorder='little'))
                    f.write(offsets[i*2+1][1].to_bytes(4, byteorder='little'))
                
                # Écrire les chaînes
                for data in strings_data:
                    f.write(data)
            
            return True
        except Exception as e:
            print(f"Erreur dans msgfmt.make: {str(e)}")
            return False

def main():
    """Fonction principale."""
    print("Compilation des fichiers de traduction .po -> .mo")
    print("=" * 60)
    
    # Trouver tous les fichiers .po
    po_files = find_po_files()
    if not po_files:
        print("Aucun fichier .po trouvé.")
        return 1
    
    print(f"Fichiers trouvés: {len(po_files)}")
    
    # Compiler tous les fichiers
    success_count = 0
    for po_file in po_files:
        if compile_po_file(po_file):
            success_count += 1
    
    # Afficher le résumé
    print("\nRésumé de la compilation:")
    print(f"- Fichiers traités: {len(po_files)}")
    print(f"- Succès: {success_count}")
    print(f"- Échecs: {len(po_files) - success_count}")
    
    # Afficher les chemins des répertoires pour faciliter la vérification
    print("\nRépertoires de traduction:")
    locale_path = BASE_DIR / 'locale'
    if locale_path.exists():
        print(f"✓ Répertoire principale: {locale_path}")
        for lang_dir in locale_path.iterdir():
            if lang_dir.is_dir():
                lc_messages = lang_dir / 'LC_MESSAGES'
                if lc_messages.exists():
                    mo_files = list(lc_messages.glob('*.mo'))
                    status = f"✓ {len(mo_files)} fichiers .mo" if mo_files else "✗ Aucun fichier .mo"
                    print(f"  - {lang_dir.name}: {status}")
    
    return 0 if success_count == len(po_files) else 1

if __name__ == '__main__':
    sys.exit(main())