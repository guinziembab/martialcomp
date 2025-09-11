#!/usr/bin/env python
"""
Script simple pour compiler les fichiers .po en fichiers .mo
sans utiliser polib ou msgfmt.
Cette méthode est basique mais fonctionnelle pour des tests.
"""

import os
import struct
import io
import re
from pathlib import Path

def create_mo_file(po_file_path):
    """
    Crée un fichier .mo basique à partir d'un fichier .po.
    Cette fonction est très simplifiée et ne gère pas tous les aspects des fichiers .mo.
    """
    mo_file_path = po_file_path.replace('.po', '.mo')
    
    try:
        # Lire le fichier .po
        with open(po_file_path, 'r', encoding='utf-8') as po_file:
            content = po_file.read()
        
        # Extraire les paires msgid/msgstr
        translations = []
        msgid_pattern = r'msgid "(.*?)"\nmsgstr "(.*?)"'
        for match in re.finditer(msgid_pattern, content, re.DOTALL):
            msgid = match.group(1).replace('\\n', '\n')
            msgstr = match.group(2).replace('\\n', '\n')
            
            # Ignorer les entrées vides
            if msgid:
                translations.append((msgid, msgstr))
        
        # Écrire un fichier .mo simplifié
        with open(mo_file_path, 'wb') as mo_file:
            # En-tête du fichier .mo (format très simplifié)
            mo_file.write(struct.pack('IIIIII', 
                0x950412de,  # Magic number
                0,           # Version
                len(translations),  # Nombre de chaînes
                28,          # Offset de l'index msgid
                28 + 8 * len(translations),  # Offset de l'index msgstr
                0            # Size of hashing table (0 for now)
            ))
            
            # Calculer les positions
            stringtable_offset = 28 + 16 * len(translations)
            
            # Préparer les données
            msgid_index = []
            msgstr_index = []
            string_data = io.BytesIO()
            
            for msgid, msgstr in translations:
                # Ajouter msgid
                msgid_bytes = msgid.encode('utf-8') + b'\0'
                msgid_index.append((len(msgid_bytes), stringtable_offset + string_data.tell()))
                string_data.write(msgid_bytes)
                
                # Ajouter msgstr
                msgstr_bytes = msgstr.encode('utf-8') + b'\0'
                msgstr_index.append((len(msgstr_bytes), stringtable_offset + string_data.tell()))
                string_data.write(msgstr_bytes)
            
            # Écrire les index
            for length, offset in msgid_index:
                mo_file.write(struct.pack('II', length, offset))
            for length, offset in msgstr_index:
                mo_file.write(struct.pack('II', length, offset))
            
            # Écrire les données de chaînes
            mo_file.write(string_data.getvalue())
        
        print(f"Fichier .mo créé: {mo_file_path}")
        return True
    except Exception as e:
        print(f"Erreur lors de la création de {mo_file_path}: {str(e)}")
        return False

def find_po_files():
    """Trouver tous les fichiers .po dans le répertoire locale."""
    po_files = []
    locale_dir = Path(__file__).resolve().parent / 'locale'
    
    for root, dirs, files in os.walk(locale_dir):
        for file in files:
            if file.endswith('.po'):
                po_files.append(os.path.join(root, file))
    
    return po_files

def main():
    """Fonction principale."""
    po_files = find_po_files()
    if not po_files:
        print("Aucun fichier .po trouvé.")
        return 1
    
    # Compiler tous les fichiers
    success_count = 0
    for po_file in po_files:
        if create_mo_file(po_file):
            success_count += 1
    
    print(f"Compilation terminée. {success_count}/{len(po_files)} fichiers compilés avec succès.")
    return 0

if __name__ == '__main__':
    main()