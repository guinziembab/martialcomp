"""
Commande Django pour traduire automatiquement les messages avec DeepL
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import sys
import subprocess
from utils.translate_po import translate_po_file


class Command(BaseCommand):
    help = 'Traduit automatiquement les fichiers de messages avec DeepL'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', required=True, help='Clé API DeepL')
        parser.add_argument('--source', default='fr', help='Langue source (défaut: fr)')
        parser.add_argument('--target', nargs='+', help='Langue(s) cible(s), ex: en it')
        parser.add_argument('--compile', action='store_true', help='Compiler les messages après traduction')
        parser.add_argument('--extract', action='store_true', help='Extraire les nouvelles chaÃ®nes avant traduction')

    def handle(self, *args, **options):
        api_key = options['api_key']
        source_lang = options['source']
        target_langs = options['target'] or [lang[0] for lang in settings.LANGUAGES if lang[0] != source_lang]
        
        # Extraire les nouvelles chaÃ®nes si demandé
        if options['extract']:
            self.stdout.write("Extraction des nouvelles chaÃ®nes...")
            try:
                subprocess.run(['python', 'manage.py', 'makemessages', '-a'], check=True)
                subprocess.run(['python', 'manage.py', 'makemessages', '-d', 'djangojs', '-a'], check=True)
                self.stdout.write(self.style.SUCCESS("Extraction terminée."))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de l'extraction: {e}"))
                return
        
        # Traduire pour chaque langue cible
        for lang in target_langs:
            if lang == source_lang:
                continue
            
            self.stdout.write(f"Traduction vers {lang}...")
            
            # Traduction du fichier principal
            po_path = os.path.join('locale', lang, 'LC_MESSAGES', 'django.po')
            if os.path.exists(po_path):
                try:
                    translate_po_file(po_path, source_lang, lang, api_key)
                    self.stdout.write(self.style.SUCCESS(f"Traduction de {po_path} terminée"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur lors de la traduction de {po_path}: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"Fichier non trouvé: {po_path}"))
            
            # Traduction du fichier JavaScript
            js_po_path = os.path.join('locale', lang, 'LC_MESSAGES', 'djangojs.po')
            if os.path.exists(js_po_path):
                try:
                    translate_po_file(js_po_path, source_lang, lang, api_key)
                    self.stdout.write(self.style.SUCCESS(f"Traduction de {js_po_path} terminée"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erreur lors de la traduction de {js_po_path}: {e}"))
        
        # Compiler les messages si demandé
        if options['compile']:
            self.stdout.write("Compilation des messages...")
            try:
                subprocess.run(['python', 'manage.py', 'compilemessages'], check=True)
                self.stdout.write(self.style.SUCCESS("Compilation terminée."))
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la compilation: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Traduction automatique terminée avec succès!"))
