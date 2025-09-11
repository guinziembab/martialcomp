#!/usr/bin/env python3
"""
Script intelligent de traduction avec gestion des erreurs et reprise automatique
"""

import polib
import requests
import time
import json
import os
import sys
from pathlib import Path
from datetime import datetime

class SmartTranslator:
    """Traducteur intelligent avec gestion d'erreurs"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def translate_with_fallback(self, text, target_lang, source_lang="fr"):
        """Traduit avec plusieurs APIs en fallback"""
        
        if not text.strip():
            return text
        
        # Essayer Google Translate d'abord
        translation = self._translate_google(text, target_lang, source_lang)
        if translation and translation != text:
            return translation
        
        # Fallback: LibreTranslate
        translation = self._translate_libre(text, target_lang, source_lang)
        if translation and translation != text:
            return translation
        
        # Si tout échoue, retourner le texte original
        return text
    
    def _translate_google(self, text, target_lang, source_lang):
        """Traduction Google Translate"""
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': source_lang,
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result[0][0][0]
        except Exception as e:
            print(f"⚠️ Erreur Google Translate: {e}")
        
        return None
    
    def _translate_libre(self, text, target_lang, source_lang):
        """Traduction LibreTranslate"""
        try:
            url = "https://libretranslate.com/translate"
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang
            }
            
            response = self.session.post(url, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result['translatedText']
        except Exception as e:
            print(f"⚠️ Erreur LibreTranslate: {e}")
        
        return None

def translate_po_with_resume(source_po_path, target_lang, progress_file=None):
    """Traduit un fichier PO avec reprise automatique"""
    
    if progress_file is None:
        progress_file = f"translation_progress_{target_lang}.json"
    
    print(f"🔄 Traduction intelligente vers {target_lang}")
    
    # Charger le fichier PO
    po = polib.pofile(source_po_path)
    
    # Charger la progression existante
    progress = {}
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
        print(f"📋 Reprise: {len(progress)} chaînes déjà traduites")
    
    # Initialiser le traducteur
    translator = SmartTranslator()
    
    # Traduire les chaînes manquantes
    translated_count = len(progress)
    total_count = len(po)
    new_translations = 0
    
    for i, entry in enumerate(po):
        if entry.msgid not in progress:
            # Traduire la chaîne
            translation = translator.translate_with_fallback(
                entry.msgid, 
                target_lang, 
                "fr"
            )
            
            entry.msgstr = translation
            progress[entry.msgid] = translation
            new_translations += 1
            
            # Afficher le progrès
            if (i + 1) % 50 == 0:
                print(f"📊 Progrès: {i + 1}/{total_count} ({((i + 1)/total_count)*100:.1f}%)")
            
            # Sauvegarder la progression régulièrement
            if new_translations % 100 == 0:
                with open(progress_file, 'w', encoding='utf-8') as f:
                    json.dump(progress, f, indent=2, ensure_ascii=False)
                print(f"💾 Progression sauvegardée ({new_translations} nouvelles traductions)")
            
            # Pause pour éviter de surcharger les APIs
            time.sleep(0.2)
    
    # Sauvegarder la progression finale
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {new_translations} nouvelles traductions ajoutées")
    return po

def main():
    """Fonction principale"""
    
    source_po = "locale/fr/LC_MESSAGES/django.po"
    
    if not os.path.exists(source_po):
        print(f"❌ Fichier source introuvable: {source_po}")
        sys.exit(1)
    
    # Langues à traduire
    languages = {
        'en': 'English',
        'es': 'Spanish',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ar': 'Arabic',
        'zh-hans': 'Chinese (Simplified)',
        'ja': 'Japanese',
        'ko': 'Korean',
        'ru': 'Russian'
    }
    
    print("🚀 TRADUCTION INTELLIGENTE AUTOMATISÉE")
    print("=" * 50)
    print(f"📁 Fichier source: {source_po}")
    print(f"🌍 Langues à traduire: {len(languages)}")
    print()
    
    start_time = datetime.now()
    
    for lang_code, lang_name in languages.items():
        print(f"\n🌍 Traduction vers {lang_name} ({lang_code})...")
        
        # Créer le dossier de langue
        lang_dir = Path(f"locale/{lang_code}/LC_MESSAGES")
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Traduire le fichier
        translated_po = translate_po_with_resume(source_po, lang_code)
        
        # Sauvegarder
        output_path = lang_dir / "django.po"
        translated_po.save(str(output_path))
        
        print(f"✅ Fichier PO sauvegardé: {output_path}")
        
        # Compiler le fichier MO
        print(f"🔨 Compilation du fichier MO...")
        os.system(f"python manage.py compilemessages --locale={lang_code}")
        print(f"✅ Fichier MO compilé pour {lang_code}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n🎉 TRADUCTION TERMINÉE!")
    print(f"⏱️ Durée totale: {duration}")
    print(f"📁 Fichiers PO créés pour {len(languages)} langues")
    print(f"💡 Redémarrez le serveur Django pour tester les traductions")

if __name__ == "__main__":
    main() 