#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour vérifier l'alignement des fichiers .po
"""

import re
from pathlib import Path
from collections import OrderedDict

def extract_msgid_from_file(po_path):
    """Extrait tous les msgid uniques d'un fichier .po"""
    with open(po_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extraire tous les msgid (y compris multilignes)
    msgids = set()
    
    # Pattern pour msgid simple
    pattern1 = r'msgid\s+"([^"]+)"\s*\n'
    matches1 = re.findall(pattern1, content)
    for match in matches1:
        msgid = match.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
        if msgid:  # Ignorer msgid vide
            msgids.add(msgid)
    
    # Pattern pour msgid multiligne
    pattern2 = r'msgid\s+""\s*\n((?:"[^"]*"\s*\n)+)'
    matches2 = re.finditer(pattern2, content, re.MULTILINE)
    for match in matches2:
        lines = match.group(1).strip().split('\n')
        msgid_parts = []
        for line in lines:
            m = re.match(r'"(.*)"', line)
            if m:
                msgid_parts.append(m.group(1))
        msgid = ''.join(msgid_parts)
        msgid = msgid.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
        if msgid:
            msgids.add(msgid)
    
    return msgids

def verify_alignment():
    """Vérifie l'alignement de tous les fichiers .po"""
    locale_dir = Path('locale')
    reference_file = locale_dir / 'en' / 'LC_MESSAGES' / 'django.po'
    
    languages = ['it', 'pt', 'es', 'ar', 'am', 'de', 'fr', 'hi', 'ja', 'ko', 
                 'no', 'ru', 'sw', 'vi', 'yo', 'zh', 'zu']
    
    print("🔍 Vérification de l'alignement des fichiers .po\n")
    
    # Charger les msgid de référence
    print(f"📌 Chargement de la référence: {reference_file.name}")
    ref_msgids = extract_msgid_from_file(reference_file)
    print(f"   ✅ {len(ref_msgids)} msgid uniques dans la référence\n")
    
    results = {}
    
    for lang in languages:
        po_file = locale_dir / lang / 'LC_MESSAGES' / 'django.po'
        if not po_file.exists():
            continue
        
        print(f"📖 {lang.upper()}: {po_file.name}")
        target_msgids = extract_msgid_from_file(po_file)
        
        missing = ref_msgids - target_msgids
        extra = target_msgids - ref_msgids
        
        results[lang] = {
            'total': len(target_msgids),
            'missing': len(missing),
            'extra': len(extra),
            'aligned': len(missing) == 0 and len(extra) == 0
        }
        
        status = "✅" if results[lang]['aligned'] else "⚠️"
        print(f"   {status} {len(target_msgids)} msgid | Manquants: {len(missing)} | Supplémentaires: {len(extra)}")
        
        if missing:
            print(f"      ➖ Manquants (premiers 5): {list(missing)[:5]}")
        if extra:
            print(f"      ➕ Supplémentaires (premiers 5): {list(extra)[:5]}")
        print()
    
    # Résumé
    print("="*60)
    print("📊 RÉSUMÉ")
    print("="*60)
    print(f"{'Langue':<10} {'Total':<10} {'Manquants':<12} {'Supplémentaires':<15} {'Statut':<10}")
    print("-"*60)
    
    all_aligned = True
    for lang, stats in sorted(results.items()):
        status = "✅ Aligné" if stats['aligned'] else "⚠️ Non aligné"
        if not stats['aligned']:
            all_aligned = False
        print(f"{lang:<10} {stats['total']:<10} {stats['missing']:<12} {stats['extra']:<15} {status:<10}")
    
    print()
    if all_aligned:
        print("✨ Tous les fichiers sont alignés avec la référence!")
    else:
        print("⚠️  Certains fichiers nécessitent un ré-alignement.")
        print("   Exécutez: python3 aligner_fichiers_po.py")

if __name__ == '__main__':
    verify_alignment()
