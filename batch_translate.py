#!/usr/bin/env python3
"""
Script de traduction par lots avec gestion des erreurs et reprise automatique
"""

import polib
import requests
import time
import json
import os
from pathlib import Path

def translate_batch_with_resume(source_po_path, target_lang, batch_size=50):
    """Traduit par lots avec possibilité de reprise"""
    
    print(f"🔄 Traduction par lots vers {target_lang}")
    
    # Charger le fichier PO source
    po = polib.pofile(source_po_path)
    
    # Créer le fichier de progression
    progress_file = f"translation_progress_{target_lang}.json"
    
    # Charger la progression existante
    progress = {}
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        print(f"📋 Reprise depuis la progression existante: {len(progress)} chaînes déjà traduites")
    
    translated_count = len(progress)
    total_count = len(po)
    
    print(f"📊 {translated_count}/{total_count} chaînes déjà traduites")
    
    # Traduire par lots
    batch = []
    for i, entry in enumerate(po):
        if entry.msgid not in progress:  # Si pas encore traduit
            batch.append((i, entry))
            
            if len(batch) >= batch_size:
                # Traduire le lot
                translated_batch = translate_batch(batch, target_lang)
                
                # Mettre à jour les entrées et la progression
                for (idx, entry), translated_text in zip(batch, translated_batch):
                    entry.msgstr = translated_text
                    progress[entry.msgid] = translated_text
                
                translated_count += len(batch)
                print(f"📊 Progrès: {translated_count}/{total_count} ({translated_count/total_count*100:.1f}%)")
                
                # Sauvegarder la progression
                with open(progress_file, 'w') as f:
                    json.dump(progress, f, indent=2)
                
                batch = []
                time.sleep(1)  # Pause entre les lots
    
    # Traduire le dernier lot
    if batch:
        translated_batch = translate_batch(batch, target_lang)
        for (idx, entry), translated_text in zip(batch, translated_batch):
            entry.msgstr = translated_text
    
    return po

def translate_batch(batch, target_lang):
    """Traduit un lot de textes"""
    
    texts = [entry.msgid for _, entry in batch]
    
    # Utiliser Google Translate API gratuite
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        'client': 'gtx',
        'sl': 'fr',
        'tl': target_lang,
        'dt': 't',
        'q': texts
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            translations = []
            
            # Extraire les traductions
            for i, text in enumerate(texts):
                if i < len(result[0]):
                    translation = result[0][i][0]
                    translations.append(translation)
                else:
                    translations.append(text)  # Garder l'original en cas d'erreur
            
            return translations
        else:
            print(f"⚠️ Erreur API: {response.status_code}")
            return [entry.msgid for _, entry in batch]  # Retourner les originaux
    
    except Exception as e:
        print(f"⚠️ Erreur de traduction: {e}")
        return [entry.msgid for _, entry in batch]  # Retourner les originaux

def main():
    """Fonction principale"""
    
    source_po = "locale/fr/LC_MESSAGES/django.po"
    
    # Langues prioritaires
    priority_languages = ['en', 'es', 'de', 'it']
    
    print("🚀 TRADUCTION PAR LOTS")
    print("=" * 40)
    
    for lang in priority_languages:
        print(f"\n🌍 Traduction vers {lang}...")
        
        # Créer le dossier de langue
        lang_dir = Path(f"locale/{lang}/LC_MESSAGES")
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Traduire le fichier
        translated_po = translate_batch_with_resume(source_po, lang, batch_size=50)
        
        # Sauvegarder
        output_path = lang_dir / "django.po"
        translated_po.save(str(output_path))
        
        print(f"✅ Fichier PO sauvegardé: {output_path}")
        
        # Compiler le fichier MO
        os.system(f"python manage.py compilemessages --locale={lang}")
        print(f"✅ Fichier MO compilé pour {lang}")

if __name__ == "__main__":
    main() 