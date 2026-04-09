#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour aligner tous les fichiers .po avec le fichier de référence (en)
Tous les fichiers doivent avoir les mêmes msgid que le fichier de référence
"""

import re
from pathlib import Path
from collections import OrderedDict

def parse_po_header(lines):
    """Parse l'en-tête d'un fichier .po"""
    header_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        header_lines.append(line)
        
        # Si on trouve un msgid non vide, on a fini l'en-tête
        if line.startswith('msgid ') and not re.match(r'msgid\s+""\s*$', line.strip()):
            header_lines.pop()  # Retirer cette ligne de l'en-tête
            break
        
        i += 1
    
    return header_lines, i

def parse_po_entry(lines, start_idx):
    """Parse une entrée .po complète"""
    entry_lines = []
    i = start_idx
    has_msgid = False
    has_msgstr = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Ligne vide après une entrée complète
        if stripped == '' and has_msgid and has_msgstr:
            entry_lines.append(line)
            break
        
        entry_lines.append(line)
        
        if line.startswith('msgid '):
            has_msgid = True
        elif line.startswith('msgstr '):
            has_msgstr = True
        
        i += 1
        
        if i >= len(lines):
            break
    
    return entry_lines, i + 1

def extract_msgid(entry_lines):
    """Extrait le msgid d'une entrée .po - version améliorée"""
    msgid_parts = []
    in_msgid = False
    in_multiline = False
    
    for line in entry_lines:
        stripped = line.strip()
        
        if line.startswith('msgid '):
            in_msgid = True
            # Cas 1: msgid simple sur une ligne: msgid "texte"
            match = re.match(r'msgid\s+"(.*)"\s*$', line)
            if match:
                msgid_parts.append(match.group(1))
                in_multiline = False
            else:
                # Cas 2: msgid multiligne: msgid ""
                match = re.match(r'msgid\s+""\s*$', stripped)
                if match:
                    msgid_parts.append('')
                    in_multiline = True
                else:
                    # Cas 3: msgid avec guillemets échappés ou autres cas
                    # Essayer d'extraire tout ce qui est entre guillemets
                    match = re.search(r'msgid\s+"(.*)"', line)
                    if match:
                        msgid_parts.append(match.group(1))
                        in_multiline = False
        elif in_msgid and in_multiline and line.startswith('"'):
            # Ligne de continuation du msgid multiligne
            match = re.match(r'"(.*)"\s*$', line)
            if match:
                msgid_parts.append(match.group(1))
        elif in_msgid and not in_multiline and line.startswith('msgstr'):
            # Fin du msgid simple, début du msgstr
            break
        elif in_msgid and in_multiline and line.startswith('msgstr'):
            # Fin du msgid multiligne, début du msgstr
            break
    
    # Reconstruire le msgid
    msgid = ''.join(msgid_parts)
    
    # Décoder les séquences d'échappement
    msgid = msgid.replace('\\n', '\n')
    msgid = msgid.replace('\\t', '\t')
    msgid = msgid.replace('\\"', '"')
    msgid = msgid.replace("\\'", "'")
    msgid = msgid.replace('\\\\', '\\')
    
    return msgid

def load_po_file(po_path):
    """Charge un fichier .po et retourne l'en-tête et les entrées"""
    print(f"   📖 Lecture: {po_path.name}")
    
    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    header_lines, start_idx = parse_po_header(lines)
    
    entries = OrderedDict()
    i = start_idx
    
    while i < len(lines):
        if lines[i].strip() == '':
            i += 1
            continue
        
        if not lines[i].startswith('#') and not lines[i].startswith('msgid'):
            i += 1
            continue
        
        try:
            entry_lines, next_idx = parse_po_entry(lines, i)
            
            has_msgid = any('msgid' in l for l in entry_lines)
            has_msgstr = any('msgstr' in l for l in entry_lines)
            
            if not has_msgid or not has_msgstr:
                i += 1
                continue
            
            msgid = extract_msgid(entry_lines)
            entries[msgid] = entry_lines
            
            i = next_idx
        except Exception:
            i += 1
    
    print(f"      ✅ {len(entries)} entrées chargées")
    return header_lines, entries

def create_empty_msgstr(entry_lines):
    """Crée une version de l'entrée avec msgstr vide"""
    new_lines = []
    in_msgstr = False
    
    for line in entry_lines:
        if line.startswith('msgstr '):
            in_msgstr = True
            # Remplacer par msgstr vide
            new_lines.append('msgstr ""\n')
        elif in_msgstr and line.startswith('"'):
            # Ignorer les lignes de continuation du msgstr
            continue
        elif in_msgstr and not line.startswith('"') and line.strip() != '':
            # Fin du msgstr
            in_msgstr = False
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    return new_lines

def align_po_files(reference_path, target_paths):
    """Aligne tous les fichiers .po avec le fichier de référence"""
    print(f"🔍 Alignement des fichiers .po\n")
    print(f"📌 Fichier de référence: {reference_path}\n")
    
    # Charger le fichier de référence
    ref_header, ref_entries = load_po_file(reference_path)
    print(f"\n📊 Référence: {len(ref_entries)} entrées uniques\n")
    
    # Traiter chaque fichier cible
    results = {}
    
    for target_path in target_paths:
        if not target_path.exists():
            print(f"⚠️  Fichier non trouvé: {target_path}")
            continue
        
        print(f"\n🔄 Traitement: {target_path.name}")
        
        # Charger le fichier cible
        target_header, target_entries = load_po_file(target_path)
        
        # Identifier les différences
        missing_msgids = set(ref_entries.keys()) - set(target_entries.keys())
        extra_msgids = set(target_entries.keys()) - set(ref_entries.keys())
        
        print(f"   📈 Entrées dans la référence: {len(ref_entries)}")
        print(f"   📈 Entrées dans le fichier: {len(target_entries)}")
        print(f"   ➕ Entrées à ajouter: {len(missing_msgids)}")
        print(f"   ➖ Entrées à supprimer: {len(extra_msgids)}")
        
        # Créer le nouveau fichier aligné
        aligned_entries = OrderedDict()
        
        # Ajouter toutes les entrées de la référence dans l'ordre
        for msgid in ref_entries.keys():
            if msgid in target_entries:
                # Garder l'entrée existante (avec sa traduction)
                aligned_entries[msgid] = target_entries[msgid]
            else:
                # Ajouter l'entrée avec msgstr vide
                aligned_entries[msgid] = create_empty_msgstr(ref_entries[msgid])
        
        # Sauvegarder l'ancien fichier
        backup_path = target_path.with_suffix('.po.backup_align')
        import shutil
        shutil.copy2(target_path, backup_path)
        print(f"   💾 Sauvegarde créée: {backup_path.name}")
        
        # Écrire le nouveau fichier
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(target_header)
            
            for msgid, entry_lines in aligned_entries.items():
                f.writelines(entry_lines)
        
        results[target_path.name] = {
            'added': len(missing_msgids),
            'removed': len(extra_msgids),
            'total': len(aligned_entries)
        }
        
        print(f"   ✅ Fichier aligné: {len(aligned_entries)} entrées")
    
    # Résumé
    print(f"\n{'='*60}")
    print(f"📊 RÉSUMÉ DE L'ALIGNEMENT")
    print(f"{'='*60}\n")
    print(f"{'Fichier':<30} {'Ajoutées':<12} {'Supprimées':<12} {'Total':<12}")
    print(f"{'-'*60}")
    
    for filename, stats in results.items():
        print(f"{filename:<30} {stats['added']:<12} {stats['removed']:<12} {stats['total']:<12}")
    
    print(f"\n✨ Tous les fichiers sont maintenant alignés avec {reference_path.name}!")
    print(f"   Tous les fichiers ont maintenant {len(ref_entries)} entrées.")

if __name__ == '__main__':
    locale_dir = Path('locale')
    reference_file = locale_dir / 'en' / 'LC_MESSAGES' / 'django.po'
    
    # Liste des langues à aligner (exclure 'en' qui est la référence)
    languages = ['it', 'pt', 'es', 'ar', 'am', 'de', 'fr', 'hi', 'ja', 'ko', 
                 'no', 'ru', 'sw', 'vi', 'yo', 'zh', 'zu']
    
    target_files = []
    for lang in languages:
        po_file = locale_dir / lang / 'LC_MESSAGES' / 'django.po'
        if po_file.exists():
            target_files.append(po_file)
    
    if not reference_file.exists():
        print(f"❌ Fichier de référence non trouvé: {reference_file}")
        exit(1)
    
    if not target_files:
        print("❌ Aucun fichier cible trouvé!")
        exit(1)
    
    print(f"🎯 {len(target_files)} fichier(s) à aligner\n")
    
    align_po_files(reference_file, target_files)
