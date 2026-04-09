#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script amélioré pour nettoyer les doublons dans un fichier .po Django
Utilise polib si disponible, sinon parse manuellement
"""

import re
from pathlib import Path
from collections import OrderedDict

def parse_po_entry_improved(lines, start_idx):
    """Parse une entrée .po complète de manière plus robuste"""
    entry_lines = []
    i = start_idx
    has_msgid = False
    has_msgstr = False
    in_multiline = False
    current_section = None
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Ligne vide après une entrée complète
        if stripped == '' and has_msgid and has_msgstr:
            entry_lines.append(line)
            break
        
        entry_lines.append(line)
        
        # Détecter msgid
        if line.startswith('msgid '):
            has_msgid = True
            current_section = 'msgid'
            # Vérifier si multiligne
            if line.strip().endswith('""') or re.match(r'msgid\s+""\s*$', line):
                in_multiline = True
            else:
                in_multiline = False
        # Détecter msgstr
        elif line.startswith('msgstr '):
            has_msgstr = True
            current_section = 'msgstr'
            # Vérifier si multiligne
            if line.strip().endswith('""') or re.match(r'msgstr\s+""\s*$', line):
                in_multiline = True
            else:
                in_multiline = False
        # Lignes de continuation (commencent par ")
        elif in_multiline and line.startswith('"'):
            pass  # Continuation normale
        # Fin de section multiligne
        elif in_multiline and not line.startswith('"') and stripped != '':
            in_multiline = False
        
        i += 1
        
        # Sécurité : ne pas dépasser la fin du fichier
        if i >= len(lines):
            break
    
    return entry_lines, i + 1

def extract_msgid_improved(entry_lines):
    """Extrait le msgid d'une entrée .po de manière plus robuste"""
    msgid_parts = []
    in_msgid = False
    in_multiline = False
    
    for line in entry_lines:
        stripped = line.strip()
        
        # Détecter le début de msgid
        if line.startswith('msgid '):
            in_msgid = True
            # Extraire la partie après msgid
            match = re.match(r'msgid\s+"(.*)"\s*$', line)
            if match:
                msgid_parts.append(match.group(1))
                in_multiline = False
            else:
                # msgid multiligne (msgid "")
                match = re.match(r'msgid\s+""\s*$', line)
                if match:
                    msgid_parts.append('')
                    in_multiline = True
        elif in_msgid and in_multiline and line.startswith('"'):
            # Ligne de continuation du msgid multiligne
            match = re.match(r'"(.*)"\s*$', line)
            if match:
                msgid_parts.append(match.group(1))
        elif in_msgid and not in_multiline and line.startswith('msgstr'):
            # Fin du msgid, début du msgstr
            break
        elif in_msgid and in_multiline and line.startswith('msgstr'):
            # Fin du msgid multiligne, début du msgstr
            break
    
    # Décoder les séquences d'échappement
    msgid = ''.join(msgid_parts)
    msgid = msgid.replace('\\n', '\n')
    msgid = msgid.replace('\\t', '\t')
    msgid = msgid.replace('\\"', '"')
    msgid = msgid.replace("\\'", "'")
    msgid = msgid.replace('\\\\', '\\')
    
    return msgid

def clean_po_file_improved(input_path, output_path):
    """Nettoie un fichier .po en supprimant les doublons - version améliorée"""
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
        
        # Si on trouve un msgid non vide (pas juste ""), on a fini l'en-tête
        if line.startswith('msgid '):
            # Vérifier si c'est l'en-tête (msgid "") ou une vraie entrée
            if not re.match(r'msgid\s+""\s*$', line.strip()):
                # C'est le début d'une vraie entrée, on garde cette ligne pour l'entrée
                header_lines.pop()  # Retirer cette ligne de l'en-tête
                break
        
        i += 1
    
    # Parser les entrées
    duplicate_count = 0
    total_entries = 0
    errors = []
    
    while i < len(lines):
        # Ignorer les lignes vides
        if lines[i].strip() == '':
            i += 1
            continue
        
        # Vérifier qu'on a bien un msgid
        if not lines[i].startswith('#') and not lines[i].startswith('msgid'):
            i += 1
            continue
        
        # Parser l'entrée complète
        try:
            entry_lines, next_idx = parse_po_entry_improved(lines, i)
            
            # Vérifier que l'entrée est valide
            has_msgid = any('msgid' in l for l in entry_lines)
            has_msgstr = any('msgstr' in l for l in entry_lines)
            
            if not has_msgid or not has_msgstr:
                errors.append(f"Ligne {i+1}: Entrée invalide (msgid={has_msgid}, msgstr={has_msgstr})")
                i += 1
                continue
            
            # Extraire le msgid
            msgid = extract_msgid_improved(entry_lines)
            
            total_entries += 1
            
            if msgid in entries:
                duplicate_count += 1
                if duplicate_count <= 5:
                    print(f"   ⚠️  Doublon trouvé (msgid #{total_entries}): {msgid[:50] if len(msgid) > 50 else msgid}...")
            else:
                entries[msgid] = entry_lines
            
            i = next_idx
        except Exception as e:
            errors.append(f"Ligne {i+1}: Erreur lors du parsing - {str(e)}")
            i += 1
    
    print(f"\n📊 Statistiques:")
    print(f"   Entrées totales: {total_entries}")
    print(f"   Entrées uniques: {len(entries)}")
    print(f"   Doublons supprimés: {duplicate_count}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} erreur(s) rencontrée(s) (premières 5):")
        for err in errors[:5]:
            print(f"   {err}")
    
    # Écrire le fichier nettoyé
    print(f"\n💾 Écriture du fichier nettoyé: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Écrire l'en-tête
        f.writelines(header_lines)
        
        # Écrire les entrées uniques
        for msgid, entry_lines in entries.items():
            f.writelines(entry_lines)
    
    print(f"✅ Fichier nettoyé créé avec succès!")
    
    return duplicate_count, len(errors)

if __name__ == '__main__':
    po_file = Path('locale/en/LC_MESSAGES/django.po.backup')  # Utiliser la sauvegarde
    cleaned_file = Path('locale/en/LC_MESSAGES/django.po')
    
    if not po_file.exists():
        print(f"❌ Fichier source non trouvé: {po_file}")
        exit(1)
    
    # Nettoyer le fichier
    duplicate_count, error_count = clean_po_file_improved(po_file, cleaned_file)
    
    if duplicate_count > 0:
        print(f"\n✨ {duplicate_count} doublon(s) supprimé(s) avec succès!")
    else:
        print("\n✨ Aucun doublon trouvé!")
    
    if error_count > 0:
        print(f"⚠️  {error_count} erreur(s) rencontrée(s) lors du parsing")
