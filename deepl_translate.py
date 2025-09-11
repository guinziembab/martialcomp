#!/usr/bin/env python3
"""
Script de traduction avec DeepL API pour des traductions plus précises
Nécessite une clé API DeepL (gratuite avec limitations)
"""

import polib
import requests
import time
import json
import os
from pathlib import Path

class DeepLTranslator:
    """Classe pour traduire avec DeepL API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('DEEPL_API_KEY')
        self.base_url = "https://api-free.deepl.com/v2/translate"
        
        if not self.api_key:
            print("⚠️ Clé API DeepL non trouvée")
            print("💡 Définissez la variable d'environnement DEEPL_API_KEY")
            print("💡 Ou obtenez une clé gratuite sur: https://www.deepl.com/pro-api")
    
    def translate_texts(self, texts, target_lang, source_lang="FR"):
        """Traduit une liste de textes"""
        
        if not self.api_key:
            print("❌ Clé API DeepL manquante")
            return texts
        
        headers = {
            'Authorization': f'DeepL-Auth-Key {self.api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Préparer les données
        data = {
            'text': texts,
            'source_lang': source_lang,
            'target_lang': target_lang.upper(),
            'preserve_formatting': '1'
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, data=data)
            
            if response.status_code == 200:
                result = response.json()
                return [translation['text'] for translation in result['translations']]
            else:
                print(f"⚠️ Erreur DeepL API: {response.status_code} - {response.text}")
                return texts
                
        except Exception as e:
            print(f"⚠️ Erreur de connexion: {e}")
            return texts
    
    def translate_po_file(self, source_po_path, target_lang, batch_size=50):
        """Traduit un fichier PO complet"""
        
        print(f"🌐 Traduction DeepL vers {target_lang}...")
        
        # Charger le fichier PO
        po = polib.pofile(source_po_path)
        
        # Préparer les textes à traduire
        texts_to_translate = []
        entries_to_update = []
        
        for entry in po:
            if entry.msgstr == entry.msgid:  # Si pas encore traduit
                texts_to_translate.append(entry.msgid)
                entries_to_update.append(entry)
        
        print(f"📊 {len(texts_to_translate)} chaînes à traduire sur {len(po)}")
        
        # Traduire par lots
        translated_count = 0
        
        for i in range(0, len(texts_to_translate), batch_size):
            batch_texts = texts_to_translate[i:i + batch_size]
            batch_entries = entries_to_update[i:i + batch_size]
            
            print(f"🔄 Traduction du lot {i//batch_size + 1}/{(len(texts_to_translate) + batch_size - 1)//batch_size}")
            
            # Traduire le lot
            translations = self.translate_texts(batch_texts, target_lang)
            
            # Mettre à jour les entrées
            for entry, translation in zip(batch_entries, translations):
                entry.msgstr = translation
                translated_count += 1
            
            # Pause pour respecter les limites de l'API
            time.sleep(1)
        
        print(f"✅ {translated_count} chaînes traduites")
        return po

def main():
    """Fonction principale"""
    
    # Initialiser le traducteur
    translator = DeepLTranslator()
    
    source_po = "locale/fr/LC_MESSAGES/django.po"
    
    # Langues cibles DeepL
    target_languages = {
        'EN': 'English',
        'ES': 'Spanish',
        'DE': 'German', 
        'IT': 'Italian',
        'PT': 'Portuguese',
        'RU': 'Russian',
        'JA': 'Japanese',
        'ZH-HANS': 'Chinese (Simplified)'
    }
    
    print("🚀 TRADUCTION AVEC DEEPL")
    print("=" * 40)
    
    for lang_code, lang_name in target_languages.items():
        print(f"\n🌍 Traduction vers {lang_name} ({lang_code})...")
        
        # Créer le dossier de langue
        lang_dir = Path(f"locale/{lang_code.lower()}/LC_MESSAGES")
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Traduire le fichier
        translated_po = translator.translate_po_file(source_po, lang_code)
        
        # Sauvegarder
        output_path = lang_dir / "django.po"
        translated_po.save(str(output_path))
        
        print(f"✅ Fichier PO sauvegardé: {output_path}")
        
        # Compiler le fichier MO
        os.system(f"python manage.py compilemessages --locale={lang_code.lower()}")
        print(f"✅ Fichier MO compilé pour {lang_code.lower()}")

if __name__ == "__main__":
    main() 