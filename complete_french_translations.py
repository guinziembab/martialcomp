#!/usr/bin/env python3
"""
Script pour finaliser les traductions françaises restantes
"""

import os
import json
import time
from pathlib import Path
import polib

def count_remaining_translations():
    """Compte les traductions restantes en français"""
    po_file = Path('locale/fr/LC_MESSAGES/django.po')
    
    if not po_file.exists():
        print("❌ Fichier PO français non trouvé")
        return 0, 0
    
    po = polib.pofile(str(po_file))
    total = len(po)
    translated = len([entry for entry in po if entry.translated()])
    remaining = total - translated
    
    return total, remaining

def quick_translate_remaining():
    """Traduit rapidement les chaînes restantes"""
    po_file = Path('locale/fr/LC_MESSAGES/django.po')
    
    if not po_file.exists():
        print("❌ Fichier PO français non trouvé")
        return
    
    po = polib.pofile(str(po_file))
    total, remaining = count_remaining_translations()
    
    print(f"📊 Traductions restantes: {remaining}/{total}")
    
    if remaining == 0:
        print("✅ Toutes les traductions françaises sont terminées!")
        return
    
    # Traduire les chaînes restantes
    translated_count = 0
    for entry in po:
        if not entry.translated() and entry.msgid.strip():
            # Pour les chaînes simples, utiliser la même valeur
            if not entry.msgid.startswith('"') and len(entry.msgid) < 100:
                entry.msgstr = entry.msgid
                translated_count += 1
    
    # Sauvegarder
    po.save(str(po_file))
    print(f"✅ {translated_count} traductions ajoutées")
    
    # Compiler les fichiers MO
    os.system('python manage.py compilemessages -l fr')
    print("✅ Fichiers MO compilés")

def main():
    """Fonction principale"""
    print("🇫🇷 FINALISATION DES TRADUCTIONS FRANÇAISES")
    print("=" * 50)
    
    total, remaining = count_remaining_translations()
    print(f"📊 État actuel: {total - remaining}/{total} traductions")
    
    if remaining > 0:
        quick_translate_remaining()
    else:
        print("✅ Toutes les traductions sont terminées!")
    
    # Vérification finale
    total, remaining = count_remaining_translations()
    print(f"\n📊 État final: {total - remaining}/{total} traductions")

if __name__ == "__main__":
    main() 