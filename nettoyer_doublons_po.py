#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour nettoyer les doublons dans un fichier .po Django
Garde la première occurrence de chaque msgid unique
"""

import re
from pathlib import Path
from collections import OrderedDict

def parse_po_entry(lines, start_idx):
    """Parse une entrée .po complète (commentaires + msgid + msgstr)"""
    entry_lines = []
    i = start_idx
    
    # Lire jusqu'à la ligne vide ou fin de fichier
    while i < len(lines):
        line = lines[i]
        entry_lines.append(line)
        
        # Si ligne vide après msgstr, on a fini l'entrée
        if line.strip() == '' and i > start_idx:
            # Vérifier qu'on a bien un msgstr avant
            if any('msgstr' in l for l in entry_lines):
                break
        
        i += 1
    
    return entry_lines, i + 1

def extract_msgid(entry_lines):
    """Extrait le msgid d'une entrée .po"""
    msgid_parts = []
    in_msgid = False
    
    for line in entry_lines:
        if line.startswith('msgid '):
            in_msgid = True
            # Extraire la partie après msgid
            match = re.match(r'msgid\s+"(.*)"\s*$', line)
            if match:
                msgid_parts.append(match.group(1))
            else:
                # msgid multiligne
                match = re.match(r'msgid\s+""\s*$', line)
                if match:
                    msgid_parts.append('')
        elif in_msgid and line.startswith('"'):
            # Ligne de continuation du msgid
            match = re.match(r'"(.*)"\s*$', line)
            if match:
                msgid_parts.append(match.group(1))
        elif in_msgid and not line.startswith('"') and line.strip() != '':
            # Fin du msgid
            break
    
    # Décoder les séquences d'échappement
    msgid = ''.join(msgid_parts)
    msgid = msgid.replace('\\n', '\n')
    msgid = msgid.replace('\\t', '\t')
    msgid = msgid.replace('\\"', '"')
    msgid = msgid.replace("\\'", "'")
    msgid = msgid.replace('\\\\', '\\')
    
    return msgid

def clean_po_file(input_path, output_path):
    """Nettoie un fichier .po en supprimant les doublons"""
    print(f"📖 Lecture du fichier: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"   Total de lignes: {len(lines)}")
    
    # Parser toutes les entrées
    entries = OrderedDict()  # Garde l'ordre d'insertion
    i = 0
    
    # Lire l'en-tête (jusqu'au premier msgid non vide)
    header_lines = []
    while i < len(lines):
        line = lines[i]
        header_lines.append(line)
        
        # Si on trouve un msgid non vide, on a fini l'en-tête
        if line.startswith('msgid ') and not line.strip().endswith('""'):
            # C'est le début d'une entrée
            break
        
        i += 1
    
    # Parser les entrées
    duplicate_count = 0
    total_entries = 0
    
    while i < len(lines):
        if lines[i].strip() == '':
            i += 1
            continue
        
        # Parser l'entrée complète
        entry_lines, next_idx = parse_po_entry(lines, i)
        
        # Extraire le msgid
        msgid = extract_msgid(entry_lines)
        
        total_entries += 1
        
        if msgid in entries:
            duplicate_count += 1
            if duplicate_count <= 5:
                print(f"   ⚠️  Doublon trouvé (msgid #{total_entries}): {msgid[:50]}...")
        else:
            entries[msgid] = entry_lines
        
        i = next_idx
    
    print(f"\n📊 Statistiques:")
    print(f"   Entrées totales: {total_entries}")
    print(f"   Entrées uniques: {len(entries)}")
    print(f"   Doublons supprimés: {duplicate_count}")
    
    # Écrire le fichier nettoyé
    print(f"\n💾 Écriture du fichier nettoyé: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Écrire l'en-tête
        f.writelines(header_lines)
        
        # Écrire les entrées uniques
        for msgid, entry_lines in entries.items():
            f.writelines(entry_lines)
            f.write('\n')
    
    print(f"✅ Fichier nettoyé créé avec succès!")
    
    return duplicate_count

if __name__ == '__main__':
    po_file = Path('locale/en/LC_MESSAGES/django.po')
    backup_file = Path('locale/en/LC_MESSAGES/django.po.backup')
    cleaned_file = Path('locale/en/LC_MESSAGES/django.po')
    
    # Créer une sauvegarde
    print("💾 Création d'une sauvegarde...")
    import shutil
    shutil.copy2(po_file, backup_file)
    print(f"   Sauvegarde créée: {backup_file}")
    
    # Nettoyer le fichier
    duplicate_count = clean_po_file(po_file, cleaned_file)
    
    if duplicate_count > 0:
        print(f"\n✨ {duplicate_count} doublon(s) supprimé(s) avec succès!")
    else:
        print("\n✨ Aucun doublon trouvé!")
