"""
Django management command to automatically translate missing translations using DeepL
"""
import os
import polib
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.translation import activate
from config.translation_service import deepl_service

class Command(BaseCommand):
    help = 'Automatically translate missing translations using DeepL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--target-language',
            type=str,
            help='Target language code (e.g., fr, es, de)',
            required=True
        )
        parser.add_argument(
            '--source-language',
            type=str,
            default='en',
            help='Source language code (default: en)'
        )
        parser.add_argument(
            '--app',
            type=str,
            help='Specific app to translate (e.g., competitions, grades)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be translated without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Retranslate existing translations'
        )

    def handle(self, *args, **options):
        target_language = options['target_language']
        source_language = options['source_language']
        app_name = options.get('app')
        dry_run = options['dry_run']
        force = options['force']

        # Check if DeepL service is available
        if not deepl_service.is_available():
            raise CommandError(
                "DeepL service is not available. Please check your DEEPL_API_KEY in settings."
            )

        # Get supported languages
        supported_languages = deepl_service.get_supported_languages()
        if target_language.lower() not in supported_languages:
            self.stdout.write(
                self.style.WARNING(
                    f"Target language '{target_language}' might not be supported by DeepL"
                )
            )

        # Find PO files
        po_files = self._find_po_files(target_language, app_name)
        
        if not po_files:
            self.stdout.write(
                self.style.WARNING(
                    f"No PO files found for language '{target_language}'"
                )
            )
            return

        total_translated = 0
        total_files = len(po_files)

        for po_file_path in po_files:
            translated_count = self._translate_po_file(
                po_file_path, 
                target_language, 
                source_language, 
                dry_run, 
                force
            )
            total_translated += translated_count

        # Show summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Dry run completed. Would translate {total_translated} entries across {total_files} files."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Translation completed. Translated {total_translated} entries across {total_files} files."
                )
            )

        # Show usage info
        usage_info = deepl_service.get_usage_info()
        if usage_info:
            self.stdout.write(
                self.style.SUCCESS(
                    f"DeepL usage: {usage_info['character_count']:,} / {usage_info['character_limit']:,} characters "
                    f"({usage_info['usage_percentage']:.1f}%)"
                )
            )

    def _find_po_files(self, target_language, app_name=None):
        """Find PO files for the target language"""
        po_files = []
        
        # Look in the main locale directory
        main_locale_dir = os.path.join(settings.BASE_DIR, 'locale')
        if os.path.exists(main_locale_dir):
            lang_dir = os.path.join(main_locale_dir, target_language, 'LC_MESSAGES')
            if os.path.exists(lang_dir):
                for filename in os.listdir(lang_dir):
                    if filename.endswith('.po'):
                        po_files.append(os.path.join(lang_dir, filename))

        # Look in app-specific locale directories
        if app_name:
            # Specific app
            app_locale_dir = os.path.join(settings.BASE_DIR, app_name, 'locale')
            if os.path.exists(app_locale_dir):
                lang_dir = os.path.join(app_locale_dir, target_language, 'LC_MESSAGES')
                if os.path.exists(lang_dir):
                    for filename in os.listdir(lang_dir):
                        if filename.endswith('.po'):
                            po_files.append(os.path.join(lang_dir, filename))
        else:
            # All apps
            for app in settings.INSTALLED_APPS:
                if app.startswith('django.') or app.startswith('debug_toolbar'):
                    continue
                    
                app_path = os.path.join(settings.BASE_DIR, app.split('.')[-1])
                if os.path.exists(app_path):
                    app_locale_dir = os.path.join(app_path, 'locale')
                    if os.path.exists(app_locale_dir):
                        lang_dir = os.path.join(app_locale_dir, target_language, 'LC_MESSAGES')
                        if os.path.exists(lang_dir):
                            for filename in os.listdir(lang_dir):
                                if filename.endswith('.po'):
                                    po_files.append(os.path.join(lang_dir, filename))

        return po_files

    def _translate_po_file(self, po_file_path, target_language, source_language, dry_run, force):
        """Translate a single PO file"""
        try:
            po = polib.pofile(po_file_path)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to load PO file {po_file_path}: {e}")
            )
            return 0

        entries_to_translate = []
        
        for entry in po:
            # Skip obsolete entries
            if entry.obsolete:
                continue
                
            # Skip entries with no msgid
            if not entry.msgid:
                continue
                
            # Skip if already translated and not forcing
            if entry.msgstr and entry.msgstr.strip() and not force:
                continue
                
            # Skip fuzzy entries unless forcing
            if 'fuzzy' in entry.flags and not force:
                continue

            entries_to_translate.append(entry)

        if not entries_to_translate:
            self.stdout.write(f"No entries to translate in {po_file_path}")
            return 0

        self.stdout.write(
            f"Processing {po_file_path}: {len(entries_to_translate)} entries to translate"
        )

        if dry_run:
            return len(entries_to_translate)

        # Translate entries in batches
        batch_size = 50  # DeepL API limit
        translated_count = 0
        
        for i in range(0, len(entries_to_translate), batch_size):
            batch = entries_to_translate[i:i + batch_size]
            
            # Prepare texts for translation
            texts_to_translate = [entry.msgid for entry in batch]
            
            # Translate batch
            translated_texts = deepl_service.translate_multiple(
                texts_to_translate, 
                target_language, 
                source_language
            )
            
            # Apply translations
            for entry, translated_text in zip(batch, translated_texts):
                if translated_text and translated_text != entry.msgid:
                    entry.msgstr = translated_text
                    # Remove fuzzy flag if present
                    if 'fuzzy' in entry.flags:
                        entry.flags.remove('fuzzy')
                    translated_count += 1

        # Save the PO file
        try:
            po.save(po_file_path)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Saved {translated_count} translations to {po_file_path}"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to save PO file {po_file_path}: {e}")
            )

        return translated_count