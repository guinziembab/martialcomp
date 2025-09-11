#!/usr/bin/env python3
"""
Script de traduction automatique des fichiers PO avec DeepL API
Conforme aux directives du guide d'implémentation multilingue
"""
import os
import polib
import argparse
import time
import deepl
from django.conf import settings


def translate_po_file(po_file, source_lang, target_lang, api_key):
    """Traduit un fichier PO vers la langue cible."""
    translator = deepl.Translator(api_key)
    po = polib.pofile(po_file)
    
    translated_count = 0
    skipped_count = 0
    
    print(f"Traduction de {po_file} vers {target_lang}...")
    
    for entry in po:
        # Ignorer les entrées déjà traduites ou vides
        if entry.translated() or not entry.msgid:
            skipped_count += 1
            continue
        
        # Ignorer les termes d'arts martiaux qui ne doivent pas être traduits
        if is_martial_arts_term(entry.msgid):
            entry.msgstr = entry.msgid  # Garder le terme original
            translated_count += 1
            continue
        
        try:
            # Traduire le texte
            result = translator.translate_text(
                entry.msgid,
                source_lang=source_lang.upper(),
                target_lang=target_lang.upper()
            )
            entry.msgstr = result.text
            translated_count += 1
            
            # Attendre un peu pour éviter de surcharger l'API
            if translated_count % 10 == 0:
                print(f"  {translated_count} chaînes traduites...")
                time.sleep(1)  # Pause de 1 seconde
                
        except Exception as e:
            print(f"  Erreur lors de la traduction de '{entry.msgid}': {e}")
    
    if translated_count > 0:
        po.save()
        print(f"  Terminé. {translated_count} chaînes traduites, {skipped_count} ignorées.")
    else:
        print(f"  Aucune chaîne à traduire. {skipped_count} déjà traduites.")


def is_martial_arts_term(text):
    """
    Vérifie si un terme est un terme d'arts martiaux qui ne doit pas être traduit
    """
    # Termes d'arts martiaux à ne pas traduire
    untranslatable_terms = {
        # Termes japonais
        'kata', 'kumite', 'dojo', 'sensei', 'kyu', 'dan', 'gi', 'obi',
        'karate', 'judo', 'aikido', 'kendo', 'kyudo', 'sumo',
        'ippon', 'waza-ari', 'yuko', 'shido', 'hansoku-make',
        'hajime', 'matte', 'sono-mama', 'yoshi',
        
        # Termes coréens
        'taekwondo', 'hapkido', 'hwa rang do', 'tang soo do',
        'dobok', 'dojang', 'sabum', 'gup', 'poom',
        'kyorugi', 'poomsae', 'kyopa',
        
        # Termes chinois
        'kung fu', 'wushu', 'tai chi', 'qi gong', 'wing chun',
        'shaolin', 'wudang', 'changquan', 'nanquan',
        
        # Termes thaïlandais
        'muay thai', 'mongkol', 'prajioud', 'ram muay',
        
        # Termes brésiliens
        'capoeira', 'roda', 'berimbau', 'ginga',
        
        # Termes généraux d'arts martiaux
        'makiwara', 'tameshiwari', 'randori', 'shiai'
    }
    
    text_lower = text.lower().strip()
    return any(term in text_lower for term in untranslatable_terms)


def main():
    parser = argparse.ArgumentParser(description='Traduire les fichiers PO avec DeepL')
    parser.add_argument('--api-key', required=True, help='Clé API DeepL')
    parser.add_argument('--source', default='fr', help='Langue source (défaut: fr)')
    parser.add_argument('--target', nargs='+', help='Langue(s) cible(s), ex: en it es')
    parser.add_argument('--dry-run', action='store_true', help='Simulation sans modification des fichiers')
    args = parser.parse_args()
    
    source_lang = args.source
    target_langs = args.target or ['en', 'it', 'es', 'de']
    
    if args.dry_run:
        print("MODE SIMULATION - Aucune modification ne sera apportée")
    
    for lang in target_langs:
        if lang == source_lang:
            continue
        
        po_path = f'locale/{lang}/LC_MESSAGES/django.po'
        if os.path.exists(po_path):
            if not args.dry_run:
                translate_po_file(po_path, source_lang, lang, args.api_key)
            else:
                print(f"[SIMULATION] Traduirait {po_path}")
        else:
            print(f"Fichier non trouvé: {po_path}")
        
        # Traiter également les fichiers JavaScript
        js_po_path = f'locale/{lang}/LC_MESSAGES/djangojs.po'
        if os.path.exists(js_po_path):
            if not args.dry_run:
                translate_po_file(js_po_path, source_lang, lang, args.api_key)
            else:
                print(f"[SIMULATION] Traduirait {js_po_path}")


if __name__ == '__main__':
    main()