#!/usr/bin/env python3
"""
Ajoute les traductions manquantes au fichier .po anglais
"""

import os
import polib
import sys

def main():
    print("=== Ajout des traductions manquantes ===\n")
    
    # Charger les traductions manquantes
    missing_file = 'missing_translations_full.txt'
    if not os.path.exists(missing_file):
        print(f"Erreur: {missing_file} non trouvé")
        return
    
    with open(missing_file, 'r', encoding='utf-8') as f:
        missing_strings = [line.strip() for line in f if line.strip()]
    
    print(f"Chaînes manquantes trouvées: {len(missing_strings)}")
    
    # Charger le fichier .po anglais
    po_file = 'locale/en/LC_MESSAGES/django.po'
    if not os.path.exists(po_file):
        print(f"Erreur: {po_file} non trouvé")
        return
    
    print(f"Chargement du fichier .po existant...")
    po = polib.pofile(po_file)
    
    # Créer un set des msgid existants pour éviter les doublons
    existing_msgids = {entry.msgid for entry in po}
    print(f"Entrées existantes: {len(existing_msgids)}")
    
    # Ajouter les traductions manquantes
    added = 0
    for msgid in missing_strings:
        # Ignorer les chaînes trop courtes ou étranges
        if len(msgid) < 2 or msgid in ['%', ';', '&', "';", '        html += \'']:
            continue
            
        # Ignorer si déjà présent
        if msgid in existing_msgids:
            continue
        
        # Créer une nouvelle entrée
        entry = polib.POEntry(
            msgid=msgid,
            msgstr='',  # Vide pour l'instant
            comment='# TODO: Translate this string'
        )
        po.append(entry)
        added += 1
    
    # Sauvegarder
    if added > 0:
        print(f"\nAjout de {added} nouvelles entrées...")
        po.save()
        print(f"✅ Fichier .po mis à jour avec succès!")
        
        # Compiler
        print("\nCompilation du fichier .mo...")
        mo_file = po_file.replace('.po', '.mo')
        po.save_as_mofile(mo_file)
        print(f"✅ Fichier .mo créé: {mo_file}")
    else:
        print("\n⚠️  Aucune nouvelle entrée à ajouter")
    
    print(f"\n📊 Résumé:")
    print(f"   - Entrées existantes: {len(existing_msgids)}")
    print(f"   - Nouvelles entrées: {added}")
    print(f"   - Total: {len(po)}")
    
    # Statistiques des traductions vides
    untranslated = sum(1 for entry in po if not entry.msgstr and not entry.obsolete)
    print(f"\n⚠️  Traductions vides à compléter: {untranslated}")

if __name__ == '__main__':
    main()