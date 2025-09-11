#!/usr/bin/env python3
"""
Script automatique de traduction des fichiers PO en arabe
MartialComp - Traduction automatique avec Google Translate
"""

import os
import sys
import polib
import requests
import json
import time
from urllib.parse import quote
from pathlib import Path

class POTranslator:
    def __init__(self, po_file_path, target_language='ar'):
        """
        Initialise le traducteur pour fichiers PO
        
        Args:
            po_file_path (str): Chemin vers le fichier .po
            target_language (str): Code langue cible (ar pour arabe)
        """
        self.po_file_path = Path(po_file_path)
        self.target_language = target_language
        self.source_language = 'fr'  # Français par défaut
        self.po = None
        self.translation_count = 0
        self.skipped_count = 0
        
    def load_po_file(self):
        """Charge le fichier PO"""
        try:
            self.po = polib.pofile(str(self.po_file_path))
            print(f"✅ Fichier PO chargé: {len(self.po)} entrées trouvées")
            return True
        except Exception as e:
            print(f"❌ Erreur lors du chargement du fichier PO: {e}")
            return False
    
    def translate_text(self, text):
        """
        Traduit un texte en utilisant Google Translate (API gratuite)
        
        Args:
            text (str): Texte à traduire
            
        Returns:
            str: Texte traduit ou None si erreur
        """
        if not text or not text.strip():
            return None
            
        # Nettoyer le texte
        text = text.strip()
        
        # Éviter de traduire les variables Django et les balises
        if any(marker in text for marker in ['%(', '{', '</', 'msgid', 'msgstr']):
            print(f"⚠️  Skipping technical text: {text[:50]}...")
            return None
            
        try:
            # URL Google Translate (API publique limitée)
            base_url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': self.source_language,
                'tl': self.target_language,
                'dt': 't',
                'q': text
            }
            
            # Construire l'URL
            url = f"{base_url}?client=gtx&sl={self.source_language}&tl={self.target_language}&dt=t&q={quote(text)}"
            
            # Faire la requête
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parser la réponse JSON
                result = json.loads(response.text)
                
                if result and result[0] and result[0][0] and result[0][0][0]:
                    translated = result[0][0][0]
                    print(f"🔄 '{text}' → '{translated}'")
                    return translated
                else:
                    print(f"❌ Réponse inattendue pour: {text}")
                    return None
            else:
                print(f"❌ Erreur HTTP {response.status_code} pour: {text}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Erreur réseau pour '{text}': {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Erreur JSON pour '{text}': {e}")
            return None
        except Exception as e:
            print(f"❌ Erreur inattendue pour '{text}': {e}")
            return None
    
    def translate_po_file(self, delay=1):
        """
        Traduit toutes les entrées non traduites du fichier PO
        
        Args:
            delay (int): Délai en secondes entre les traductions (pour éviter rate limiting)
        """
        if not self.po:
            print("❌ Fichier PO non chargé")
            return False
            
        print(f"🚀 Début de la traduction vers {self.target_language}")
        print(f"📝 {len(self.po)} entrées à traiter")
        
        for entry in self.po:
            # Skip si déjà traduit
            if entry.msgstr and entry.msgstr.strip():
                print(f"⏭️  Déjà traduit: {entry.msgid[:50]}...")
                self.skipped_count += 1
                continue
            
            # Skip si pas de texte source
            if not entry.msgid or not entry.msgid.strip():
                self.skipped_count += 1
                continue
            
            print(f"\n🔄 Traduction en cours ({self.translation_count + 1}/{len(self.po) - self.skipped_count})...")
            
            # Traduire
            translated = self.translate_text(entry.msgid)
            
            if translated:
                entry.msgstr = translated
                self.translation_count += 1
                print(f"✅ Traduit avec succès")
            else:
                print(f"⚠️  Échec de traduction, entrée ignorée")
                self.skipped_count += 1
            
            # Délai pour éviter rate limiting
            if delay > 0:
                time.sleep(delay)
        
        return True
    
    def save_po_file(self, backup=True):
        """
        Sauvegarde le fichier PO traduit
        
        Args:
            backup (bool): Créer une sauvegarde avant modification
        """
        if backup:
            backup_path = self.po_file_path.with_suffix('.po.backup')
            try:
                backup_path.write_bytes(self.po_file_path.read_bytes())
                print(f"💾 Sauvegarde créée: {backup_path}")
            except Exception as e:
                print(f"⚠️  Impossible de créer la sauvegarde: {e}")
        
        try:
            self.po.save(str(self.po_file_path))
            print(f"✅ Fichier PO sauvegardé: {self.po_file_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            return False
    
    def compile_mo_file(self):
        """Compile le fichier .mo à partir du .po"""
        try:
            mo_file_path = self.po_file_path.with_suffix('.mo')
            self.po.save_as_mofile(str(mo_file_path))
            print(f"✅ Fichier MO compilé: {mo_file_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de la compilation MO: {e}")
            return False
    
    def print_stats(self):
        """Affiche les statistiques de traduction"""
        print(f"\n📊 STATISTIQUES DE TRADUCTION")
        print(f"=" * 40)
        print(f"Entrées traduites: {self.translation_count}")
        print(f"Entrées ignorées: {self.skipped_count}")
        print(f"Total entrées: {len(self.po) if self.po else 0}")
        
        if self.po and len(self.po) > 0:
            percentage = (self.translation_count / len(self.po)) * 100
            print(f"Pourcentage traduit: {percentage:.1f}%")

def install_requirements():
    """Installe les dépendances requises"""
    print("📦 Vérification des dépendances...")
    
    try:
        import polib
        print("✅ polib disponible")
    except ImportError:
        print("❌ polib non installé")
        print("💿 Installation de polib...")
        os.system("pip install polib")
    
    try:
        import requests
        print("✅ requests disponible")
    except ImportError:
        print("❌ requests non installé")
        print("💿 Installation de requests...")
        os.system("pip install requests")

def main():
    """Fonction principale"""
    print("🌍 TRADUCTEUR AUTOMATIQUE PO → ARABE")
    print("=" * 50)
    
    # Vérifier les dépendances
    install_requirements()
    
    # Chemin du fichier PO
    po_file_path = Path("C:/martial_hub_django/martialcomp/locale/ar/LC_MESSAGES/django.po")
    
    # Vérifier si le fichier existe
    if not po_file_path.exists():
        print(f"❌ Fichier PO non trouvé: {po_file_path}")
        
        # Créer le répertoire si nécessaire
        po_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Créer un fichier PO vide
        print("📝 Création d'un fichier PO vide...")
        po_content = '''# Arabic translations for MartialComp
# Copyright (C) 2025 MartialComp
# This file is distributed under the same license as the MartialComp package.
#
msgid ""
msgstr ""
"Project-Id-Version: MartialComp\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-08-10 14:00+0000\\n"
"PO-Revision-Date: 2025-08-10 14:00+0000\\n"
"Last-Translator: Auto Translator\\n"
"Language-Team: Arabic\\n"
"Language: ar\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 ? 4 : 5;\\n"

# Exemples d'entrées à traduire
msgid "Welcome"
msgstr ""

msgid "Home"
msgstr ""

msgid "Login"
msgstr ""

msgid "Register"
msgstr ""

msgid "Competitions"
msgstr ""

msgid "Profile"
msgstr ""
'''
        
        po_file_path.write_text(po_content, encoding='utf-8')
        print(f"✅ Fichier PO créé: {po_file_path}")
    
    # Initialiser le traducteur
    translator = POTranslator(po_file_path, 'ar')
    
    # Charger le fichier PO
    if not translator.load_po_file():
        return 1
    
    # Demander confirmation
    print(f"\n📋 Prêt à traduire {len(translator.po)} entrées")
    choice = input("🚀 Commencer la traduction ? (y/N): ").lower().strip()
    
    if choice != 'y':
        print("❌ Traduction annulée")
        return 0
    
    # Traduire
    print("\n🔄 Traduction en cours...")
    if translator.translate_po_file(delay=0.5):  # 0.5 sec entre chaque traduction
        
        # Sauvegarder
        if translator.save_po_file():
            
            # Compiler le fichier MO
            translator.compile_mo_file()
            
            # Afficher les stats
            translator.print_stats()
            
            print(f"\n🎉 TRADUCTION TERMINÉE AVEC SUCCÈS!")
            print(f"📁 Fichier traduit: {po_file_path}")
            print(f"📁 Fichier MO: {po_file_path.with_suffix('.mo')}")
            
            return 0
        else:
            print("❌ Échec de la sauvegarde")
            return 1
    else:
        print("❌ Échec de la traduction")
        return 1

if __name__ == "__main__":
    sys.exit(main())