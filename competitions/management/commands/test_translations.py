#!/usr/bin/env python3
"""
Command to test translations in the project
"""
from django.core.management.base import BaseCommand
from django.utils.translation import activate, get_language, gettext as _
from django.conf import settings
import os
import re

class Command(BaseCommand):
    help = 'Test if translations are working correctly'

    def add_arguments(self, parser):
        parser.add_argument('--language', '-l', type=str, help='Language code to test')

    def handle(self, *args, **options):
        # Save current language
        current_language = get_language()
        
        # Get test language from options or use English
        test_language = options.get('language') or 'en'
        
        self.stdout.write(self.style.SUCCESS(f'Testing translations for language: {test_language}'))
        
        # Activate test language
        activate(test_language)
        
        # Test some common translations
        test_strings = [
            "Accueil",
            "Tableau de bord",
            "Connexion",
            "Déconnexion",
            "Fonctionnalités",
            "Compétitions",
            "La plateforme ultime de gestion des compétitions d'arts martiaux"
        ]
        
        for text in test_strings:
            translation = _(text)
            if translation == text and test_language != 'fr':
                self.stdout.write(self.style.ERROR(f'Translation failed for: "{text}" -> still "{translation}"'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Translation success: "{text}" -> "{translation}"'))
        
        # Test if .mo files exist for all languages
        self.stdout.write("\nChecking .mo files:")
        locale_dir = os.path.join(settings.BASE_DIR, 'locale')
        for lang_code, lang_name in settings.LANGUAGES:
            mo_path = os.path.join(locale_dir, lang_code, 'LC_MESSAGES', 'django.mo')
            if os.path.exists(mo_path):
                self.stdout.write(self.style.SUCCESS(f'{lang_code} ({lang_name}): .mo file exists'))
            else:
                self.stdout.write(self.style.ERROR(f'{lang_code} ({lang_name}): .mo file MISSING'))
        
        # Check templates for inconsistent translation tags
        self.stdout.write("\nChecking templates for inconsistent translation tags:")
        template_dir = os.path.join(settings.BASE_DIR, 'competitions', 'templates')
        self.check_templates_in_dir(template_dir)
        
        # Restore original language
        activate(current_language)
        
    def check_templates_in_dir(self, directory):
        """Check all HTML files in a directory for inconsistent translation tags"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    self.check_template_file(file_path)
        
    def check_template_file(self, file_path):
        """Check a single template file for inconsistent translation tags"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for {% translate %} tags which should be {% trans %}
        translate_tags = re.findall(r'{%\s*translate\s+[^%]+%}', content)
        
        # Look for {% blocktranslate %} tags which should be {% blocktrans %}
        blocktranslate_tags = re.findall(r'{%\s*blocktranslate[^%]*%}', content)
        
        rel_path = os.path.relpath(file_path, settings.BASE_DIR)
        
        if translate_tags:
            self.stdout.write(self.style.WARNING(f'{rel_path}: Found {len(translate_tags)} "{% translate %}" tags (should be "{% trans %}")'))
            
        if blocktranslate_tags:
            self.stdout.write(self.style.WARNING(f'{rel_path}: Found {len(blocktranslate_tags)} "{% blocktranslate %}" tags (should be "{% blocktrans %}")'))
            
        if not translate_tags and not blocktranslate_tags:
            self.stdout.write(self.style.SUCCESS(f'{rel_path}: No inconsistent translation tags found'))