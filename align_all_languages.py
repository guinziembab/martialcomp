#!/usr/bin/env python3
"""
Aligne tous les fichiers PO de toutes les langues avec le fichier PO anglais
"""

import polib
import os
import glob

def align_language(en_po, lang_code, lang_name):
    """Aligne un fichier PO de langue spécifique avec l'anglais"""
    
    po_path = f'locale/{lang_code}/LC_MESSAGES/django.po'
    
    if not os.path.exists(po_path):
        print(f"   ⚠️  {po_path} non trouvé - ignoré")
        return None
    
    try:
        # Charger le fichier de la langue
        lang_po = polib.pofile(po_path)
        initial_count = len(lang_po)
        
        # Créer un dictionnaire des entrées existantes
        lang_dict = {}
        for entry in lang_po:
            if not entry.obsolete:
                lang_dict[entry.msgid] = entry
        
        # Statistiques initiales
        translated_before = sum(1 for entry in lang_po if entry.msgstr and not entry.obsolete)
        
        # Créer un nouveau fichier PO aligné
        new_po = polib.POFile()
        new_po.metadata = lang_po.metadata.copy()
        
        # Parcourir toutes les entrées anglaises
        added = 0
        preserved = 0
        
        for en_entry in en_po:
            if en_entry.obsolete:
                continue
                
            if en_entry.msgid in lang_dict:
                # Préserver l'entrée existante
                existing_entry = lang_dict[en_entry.msgid]
                new_po.append(existing_entry)
                if existing_entry.msgstr:
                    preserved += 1
            else:
                # Créer une nouvelle entrée
                new_entry = polib.POEntry(
                    msgid=en_entry.msgid,
                    msgstr='',
                    msgid_plural=en_entry.msgid_plural,
                    msgstr_plural=en_entry.msgstr_plural.copy() if en_entry.msgstr_plural else {},
                    comment=en_entry.comment,
                    tcomment=en_entry.tcomment,
                    occurrences=en_entry.occurrences.copy(),
                    flags=en_entry.flags.copy(),
                    msgctxt=en_entry.msgctxt
                )
                new_po.append(new_entry)
                added += 1
        
        # Sauvegarder le backup
        backup_path = po_path + '.backup_align_20251003'
        os.rename(po_path, backup_path)
        
        # Sauvegarder le nouveau fichier
        new_po.save(po_path)
        
        # Compiler le fichier MO
        mo_path = po_path.replace('.po', '.mo')
        new_po.save_as_mofile(mo_path)
        
        # Statistiques finales
        untranslated = sum(1 for entry in new_po if not entry.msgstr and not entry.obsolete)
        translated = len(new_po) - untranslated
        
        return {
            'lang_code': lang_code,
            'lang_name': lang_name,
            'initial_count': initial_count,
            'final_count': len(new_po),
            'added': added,
            'preserved': preserved,
            'translated': translated,
            'untranslated': untranslated,
            'percent': round(translated/len(new_po)*100, 1)
        }
        
    except Exception as e:
        print(f"   ❌ Erreur pour {lang_name}: {e}")
        return None

def main():
    print("=== Alignement de toutes les langues avec l'anglais ===\n")
    
    # Charger le fichier anglais de référence
    en_po_path = 'locale/en/LC_MESSAGES/django.po'
    if not os.path.exists(en_po_path):
        print(f"❌ Erreur: {en_po_path} non trouvé")
        return
    
    print("Chargement du fichier anglais de référence...")
    en_po = polib.pofile(en_po_path)
    print(f"✓ Fichier anglais chargé: {len(en_po)} entrées\n")
    
    # Liste des langues à traiter
    languages = [
        ('fr', 'Français'),
        ('es', 'Español'),
        ('it', 'Italiano'),
        ('de', 'Deutsch'),
        ('pt', 'Português'),
        ('ru', 'Русский'),
        ('vi', 'Tiếng Việt'),
        ('no', 'Norsk'),
        ('ja', '日本語'),
        ('zh-hans', '中文'),
        ('hi', 'हिन्दी'),
        ('ar', 'العربية'),
        ('sw', 'Kiswahili'),
        ('am', 'አማርኛ'),
        ('zu', 'isiZulu'),
        ('yo', 'Yorùbá'),
        ('ha', 'Hausa'),
    ]
    
    results = []
    
    print("Traitement des langues:")
    for lang_code, lang_name in languages:
        if lang_code == 'en':
            continue  # Passer l'anglais
            
        print(f"\n{lang_name} ({lang_code}):")
        result = align_language(en_po, lang_code, lang_name)
        if result:
            results.append(result)
            print(f"   ✓ Aligné: {result['added']} ajoutées, {result['preserved']} préservées")
            print(f"   📊 Traduction: {result['percent']}% ({result['translated']}/{result['final_count']})")
    
    # Rapport final
    print("\n" + "="*70)
    print("📊 RAPPORT FINAL D'ALIGNEMENT")
    print("="*70)
    
    print(f"\nLangues traitées: {len(results)}")
    print(f"Entrées de référence (EN): {len(en_po)}")
    
    print("\nDétails par langue:")
    print(f"{'Langue':<20} {'Initial':<10} {'Final':<10} {'Ajoutées':<10} {'Traduites':<15} {'%':<8}")
    print("-"*80)
    
    for r in sorted(results, key=lambda x: x['percent'], reverse=True):
        print(f"{r['lang_name']:<20} {r['initial_count']:<10} {r['final_count']:<10} "
              f"{r['added']:<10} {r['translated']:<15} {r['percent']:<8}%")
    
    # Moyennes
    avg_percent = sum(r['percent'] for r in results) / len(results) if results else 0
    total_added = sum(r['added'] for r in results)
    
    print(f"\n{'Moyenne':<20} {'':<10} {'':<10} {total_added:<10} {'':<15} {avg_percent:<8.1f}%")
    
    print("\n✅ Alignement terminé pour toutes les langues!")
    print("\nTous les fichiers .po ont été alignés avec l'anglais et les .mo recompilés.")

if __name__ == '__main__':
    main()