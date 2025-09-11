from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils.translation import activate, gettext as _
import os

class Command(BaseCommand):
    """Commande pour gérer la traduction complète du site."""
    
    help = 'Traduit le site MartialComp en anglais et autres langues'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--compile-only',
            action='store_true',
            help='Compile seulement les messages existants'
        )
        
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help='Langue cible (par défaut: en)'
        )
        
        parser.add_argument(
            '--test',
            action='store_true',
            help='Teste les traductions après compilation'
        )
    
    def handle(self, *args, **options):
        language = options['language']
        compile_only = options['compile_only']
        test_translations = options['test']
        
        self.stdout.write(
            self.style.SUCCESS(f'ðŸŒ Traduction du site MartialComp en {language.upper()}')
        )
        
        if not compile_only:
            # Générer les messages de traduction
            self.stdout.write('ðŸ“ Génération des messages de traduction...')
            try:
                call_command('makemessages', locale=[language], verbosity=0)
                self.stdout.write(self.style.SUCCESS('âœ… Messages générés'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'âš ï¸  Erreur génération: {e}'))
        
        # Compiler les messages
        self.stdout.write('ðŸ”¨ Compilation des messages...')
        try:
            # Utiliser msgfmt directement car compilemessages peut Ãªtre lent
            locale_dir = f'locale/{language}/LC_MESSAGES'
            po_file = f'{locale_dir}/django.po'
            mo_file = f'{locale_dir}/django.mo'
            
            if os.path.exists(po_file):
                os.system(f'msgfmt -o {mo_file} {po_file}')
                self.stdout.write(self.style.SUCCESS('âœ… Messages compilés'))
            else:
                self.stdout.write(self.style.ERROR(f'âŒ Fichier {po_file} non trouvé'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'âŒ Erreur compilation: {e}'))
        
        if test_translations:
            self._test_translations(language)
        
        self.stdout.write(
            self.style.SUCCESS(f'ðŸŽ‰ Traduction en {language.upper()} terminée !')
        )
        
        # Afficher les statistiques
        self._show_translation_stats(language)
    
    def _test_translations(self, language):
        """Teste quelques traductions clés."""
        self.stdout.write('\nðŸ§ª Test des traductions:')
        
        test_strings = [
            'Tableau de bord',
            'Se connecter', 
            'Fonctionnalités',
            'Coach Multi-Disciplines',
            'Commencer maintenant'
        ]
        
        activate(language)
        
        for test_string in test_strings:
            translated = _(test_string)
            if translated != test_string:
                self.stdout.write(f'  âœ… {test_string} â†’ {translated}')
            else:
                self.stdout.write(f'  âš ï¸  {test_string} â†’ (non traduit)')
    
    def _show_translation_stats(self, language):
        """Affiche les statistiques de traduction."""
        try:
            po_file = f'locale/{language}/LC_MESSAGES/django.po'
            if os.path.exists(po_file):
                with open(po_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                total_strings = content.count('msgid "') - 1  # -1 pour l'en-tÃªte
                translated_strings = content.count('msgstr "') - content.count('msgstr ""') - 1
                
                percentage = (translated_strings / total_strings * 100) if total_strings > 0 else 0
                
                self.stdout.write(f'\nðŸ“Š Statistiques de traduction ({language.upper()}):')
                self.stdout.write(f'  â€¢ ChaÃ®nes totales: {total_strings}')
                self.stdout.write(f'  â€¢ ChaÃ®nes traduites: {translated_strings}')
                self.stdout.write(f'  â€¢ Pourcentage: {percentage:.1f}%')
                
                if percentage < 100:
                    missing = total_strings - translated_strings
                    self.stdout.write(f'  â€¢ Manquantes: {missing}')
                    
        except Exception as e:
            self.stdout.write(f'âš ï¸  Impossible de calculer les statistiques: {e}')
