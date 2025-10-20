#!/usr/bin/env python3
"""
Supprime les doublons d'un fichier .po en conservant la première occurrence
"""

import sys
from collections import OrderedDict

def remove_duplicates_po(input_file, output_file=None):
    """
    Supprime les msgid en double du fichier .po
    """
    if output_file is None:
        output_file = input_file
    
    print(f"Lecture de {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Dictionnaire pour stocker les entrées (msgid -> lignes complètes)
    entries = OrderedDict()
    current_entry = []
    current_msgid = None
    in_entry = False
    header_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Détecter le début d'une entrée
        if line.startswith('msgid '):
            # Sauvegarder l'entrée précédente si elle existe
            if current_msgid is not None and current_entry:
                if current_msgid not in entries:
                    entries[current_msgid] = ''.join(current_entry)
                else:
                    print(f"  ⚠️  Doublon ignoré: {current_msgid[:60]}...")
            
            # Commencer une nouvelle entrée
            current_entry = []
            current_msgid = line.strip()
            in_entry = True
        
        # Ajouter la ligne à l'entrée courante
        if in_entry:
            current_entry.append(line)
        else:
            # Lignes d'en-tête (avant la première msgid)
            header_lines.append(line)
        
        i += 1
    
    # Ajouter la dernière entrée
    if current_msgid is not None and current_entry:
        if current_msgid not in entries:
            entries[current_msgid] = ''.join(current_entry)
    
    print(f"  Entrées uniques: {len(entries)}")
    print(f"  En-tête: {len(header_lines)} lignes")
    
    # Écrire le fichier nettoyé
    print(f"\nÉcriture de {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        # Écrire l'en-tête
        f.writelines(header_lines)
        
        # Écrire toutes les entrées uniques
        for entry_text in entries.values():
            f.write(entry_text)
    
    print("✅ Doublons supprimés!")
    return len(entries)

if __name__ == '__main__':
    input_file = 'locale/en/LC_MESSAGES/django.po'
    
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  SUPPRESSION DES DOUBLONS - FICHIER .PO ANGLAIS              ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Backup déjà créé par le script précédent
    
    try:
        count = remove_duplicates_po(input_file)
        print()
        print(f"✅ Fichier nettoyé: {count} entrées uniques")
        print()
        print("Compilation...")
        
        import subprocess
        result = subprocess.run(
            ['msgfmt', '-o', 'locale/en/LC_MESSAGES/django.mo', input_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Compilation réussie!")
        else:
            print("❌ Erreur de compilation:")
            print(result.stderr[:500])
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)
