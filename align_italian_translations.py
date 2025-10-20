#!/usr/bin/env python3
"""
Aligne le fichier PO italien avec le fichier PO anglais
Ajoute toutes les chaînes manquantes et préserve les traductions existantes
"""

import polib
import os

def main():
    print("=== Alignement des traductions italiennes ===\n")
    
    # Chemins des fichiers
    en_po_path = 'locale/en/LC_MESSAGES/django.po'
    it_po_path = 'locale/it/LC_MESSAGES/django.po'
    
    # Vérifier l'existence des fichiers
    if not os.path.exists(en_po_path):
        print(f"❌ Erreur: {en_po_path} non trouvé")
        return
    
    if not os.path.exists(it_po_path):
        print(f"❌ Erreur: {it_po_path} non trouvé")
        return
    
    print("Chargement des fichiers PO...")
    
    # Charger les fichiers
    try:
        en_po = polib.pofile(en_po_path)
        print(f"✓ Fichier anglais chargé: {len(en_po)} entrées")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du fichier anglais: {e}")
        return
    
    try:
        it_po = polib.pofile(it_po_path)
        print(f"✓ Fichier italien chargé: {len(it_po)} entrées")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du fichier italien: {e}")
        return
    
    # Créer un dictionnaire des entrées italiennes existantes
    it_dict = {}
    for entry in it_po:
        if not entry.obsolete:
            it_dict[entry.msgid] = entry
    
    print(f"\nEntrées italiennes non obsolètes: {len(it_dict)}")
    
    # Statistiques initiales
    translated_before = sum(1 for entry in it_po if entry.msgstr and not entry.obsolete)
    print(f"Traductions italiennes existantes: {translated_before}")
    
    # Créer un nouveau fichier PO italien aligné
    new_it_po = polib.POFile()
    
    # Copier les métadonnées
    new_it_po.metadata = it_po.metadata.copy()
    
    # Parcourir toutes les entrées anglaises
    added = 0
    preserved = 0
    
    for en_entry in en_po:
        if en_entry.obsolete:
            continue
            
        # Vérifier si cette entrée existe déjà en italien
        if en_entry.msgid in it_dict:
            # Préserver l'entrée italienne existante
            it_entry = it_dict[en_entry.msgid]
            new_it_po.append(it_entry)
            if it_entry.msgstr:
                preserved += 1
        else:
            # Créer une nouvelle entrée
            new_entry = polib.POEntry(
                msgid=en_entry.msgid,
                msgstr='',  # Vide pour l'instant
                msgid_plural=en_entry.msgid_plural,
                msgstr_plural=en_entry.msgstr_plural.copy() if en_entry.msgstr_plural else {},
                comment=en_entry.comment,
                tcomment=en_entry.tcomment,
                occurrences=en_entry.occurrences.copy(),
                flags=en_entry.flags.copy(),
                msgctxt=en_entry.msgctxt
            )
            new_it_po.append(new_entry)
            added += 1
    
    # Ajouter les entrées italiennes qui n'existent pas en anglais (au cas où)
    orphaned = 0
    for msgid, it_entry in it_dict.items():
        found = False
        for entry in new_it_po:
            if entry.msgid == msgid:
                found = True
                break
        
        if not found and it_entry.msgstr:
            # Ajouter avec un commentaire spécial
            it_entry.tcomment = "# ORPHANED: Not in English PO file\n" + (it_entry.tcomment or '')
            new_it_po.append(it_entry)
            orphaned += 1
    
    print(f"\n📊 Résultats de l'alignement:")
    print(f"   - Entrées préservées avec traduction: {preserved}")
    print(f"   - Nouvelles entrées ajoutées: {added}")
    print(f"   - Entrées orphelines conservées: {orphaned}")
    print(f"   - Total des entrées: {len(new_it_po)}")
    
    # Sauvegarder le backup
    backup_path = it_po_path + '.backup_' + os.environ.get('USER', 'user') + '_' + \
                  __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f"\nSauvegarde du fichier original...")
    os.rename(it_po_path, backup_path)
    print(f"✓ Backup créé: {backup_path}")
    
    # Sauvegarder le nouveau fichier
    print(f"\nSauvegarde du fichier aligné...")
    new_it_po.save(it_po_path)
    print(f"✓ Fichier italien mis à jour: {it_po_path}")
    
    # Compiler le fichier MO
    print(f"\nCompilation du fichier MO...")
    mo_path = it_po_path.replace('.po', '.mo')
    new_it_po.save_as_mofile(mo_path)
    print(f"✓ Fichier MO créé: {mo_path}")
    
    # Statistiques finales
    untranslated = sum(1 for entry in new_it_po if not entry.msgstr and not entry.obsolete)
    translated = len(new_it_po) - untranslated
    
    print(f"\n✅ Alignement terminé avec succès!")
    print(f"\n📊 Statistiques finales:")
    print(f"   - Total des entrées: {len(new_it_po)}")
    print(f"   - Traduites: {translated} ({translated/len(new_it_po)*100:.1f}%)")
    print(f"   - À traduire: {untranslated} ({untranslated/len(new_it_po)*100:.1f}%)")
    
    # Afficher quelques exemples de chaînes à traduire
    if untranslated > 0:
        print(f"\n📝 Exemples de chaînes à traduire (10 premières):")
        count = 0
        for entry in new_it_po:
            if not entry.msgstr and not entry.obsolete:
                print(f"   - \"{entry.msgid[:60]}{'...' if len(entry.msgid) > 60 else ''}\"")
                count += 1
                if count >= 10:
                    break

if __name__ == '__main__':
    main()