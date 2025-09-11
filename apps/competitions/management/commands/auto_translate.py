from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils.translation import activate, get_language
from apps.competitions.utils.multilingual_ai import MultilingualAI
from apps.competitions.models import Practitioner, Club, Discipline
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """Commande pour la traduction automatique des contenus."""
    
    help = 'Traduit automatiquement les contenus vers les langues supportées'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--target-language',
            type=str,
            help='Langue cible pour la traduction (ex: fr, en, es)',
            required=True
        )
        
        parser.add_argument(
            '--model',
            type=str,
            choices=['practitioner', 'club', 'discipline', 'all'],
            default='all',
            help='Modèle Ã  traduire'
        )
        
        parser.add_argument(
            '--field',
            type=str,
            help='Champ spécifique Ã  traduire (optionnel)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulation sans modification de la base'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Taille des lots pour le traitement'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la traduction mÃªme si le champ existe déjÃ '
        )
    
    def handle(self, *args, **options):
        target_language = options['target_language']
        model_name = options['model']
        field_name = options['field']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        force = options['force']
        
        # Initialiser le service IA
        multilingual_ai = MultilingualAI()
        
        # Vérifier que la langue cible est supportée
        if target_language not in multilingual_ai.supported_languages:
            raise CommandError(f"Langue non supportée: {target_language}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Début de la traduction vers {multilingual_ai.supported_languages[target_language]}"
            )
        )
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode simulation activé"))
        
        total_translated = 0
        
        try:
            if model_name in ['practitioner', 'all']:
                translated = self._translate_practitioners(
                    multilingual_ai, target_language, field_name, dry_run, batch_size, force
                )
                total_translated += translated
            
            if model_name in ['club', 'all']:
                translated = self._translate_clubs(
                    multilingual_ai, target_language, field_name, dry_run, batch_size, force
                )
                total_translated += translated
            
            if model_name in ['discipline', 'all']:
                translated = self._translate_disciplines(
                    multilingual_ai, target_language, field_name, dry_run, batch_size, force
                )
                total_translated += translated
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Traduction terminée: {total_translated} éléments traités"
                )
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la traduction: {e}")
            raise CommandError(f"Erreur: {e}")
    
    def _translate_practitioners(self, ai, target_lang, field_name, dry_run, batch_size, force):
        """Traduit les champs des pratiquants."""
        self.stdout.write("Traduction des pratiquants...")
        
        # Champs traduisibles
        translatable_fields = {
            'bio': f'bio_{target_lang}',
            'teaching_philosophy': f'teaching_philosophy_{target_lang}',
            'specializations': f'specializations_{target_lang}'
        }
        
        if field_name:
            if field_name not in translatable_fields:
                raise CommandError(f"Champ non traduisible: {field_name}")
            translatable_fields = {field_name: translatable_fields[field_name]}
        
        practitioners = Practitioner.objects.all()
        total_count = practitioners.count()
        translated_count = 0
        
        for i in range(0, total_count, batch_size):
            batch = practitioners[i:i + batch_size]
            
            for practitioner in batch:
                updated = False
                
                for source_field, target_field in translatable_fields.items():
                    # Vérifier si le champ source existe et a du contenu
                    source_value = getattr(practitioner, source_field, None)
                    if not source_value or not source_value.strip():
                        continue
                    
                    # Vérifier si le champ cible existe déjÃ 
                    target_value = getattr(practitioner, target_field, None)
                    if target_value and target_value.strip() and not force:
                        continue
                    
                    # Traduire
                    translated_text = ai.auto_translate(source_value, target_lang)
                    
                    if translated_text and translated_text != source_value:
                        if not dry_run:
                            setattr(practitioner, target_field, translated_text)
                            updated = True
                        
                        self.stdout.write(
                            f"Pratiquant {practitioner.id} - {source_field}: "
                            f"{source_value[:50]}... -> {translated_text[:50]}..."
                        )
                
                if updated and not dry_run:
                    practitioner.save()
                    translated_count += 1
            
            # Afficher le progrès
            progress = min(i + batch_size, total_count)
            self.stdout.write(f"Progrès: {progress}/{total_count} pratiquants traités")
        
        return translated_count
    
    def _translate_clubs(self, ai, target_lang, field_name, dry_run, batch_size, force):
        """Traduit les champs des clubs."""
        self.stdout.write("Traduction des clubs...")
        
        translatable_fields = {
            'description': f'description_{target_lang}',
            'history': f'history_{target_lang}',
            'mission': f'mission_{target_lang}'
        }
        
        if field_name:
            if field_name not in translatable_fields:
                raise CommandError(f"Champ non traduisible: {field_name}")
            translatable_fields = {field_name: translatable_fields[field_name]}
        
        clubs = Club.objects.all()
        total_count = clubs.count()
        translated_count = 0
        
        for i in range(0, total_count, batch_size):
            batch = clubs[i:i + batch_size]
            
            for club in batch:
                updated = False
                
                for source_field, target_field in translatable_fields.items():
                    source_value = getattr(club, source_field, None)
                    if not source_value or not source_value.strip():
                        continue
                    
                    target_value = getattr(club, target_field, None)
                    if target_value and target_value.strip() and not force:
                        continue
                    
                    translated_text = ai.auto_translate(source_value, target_lang)
                    
                    if translated_text and translated_text != source_value:
                        if not dry_run:
                            setattr(club, target_field, translated_text)
                            updated = True
                        
                        self.stdout.write(
                            f"Club {club.id} - {source_field}: "
                            f"{source_value[:50]}... -> {translated_text[:50]}..."
                        )
                
                if updated and not dry_run:
                    club.save()
                    translated_count += 1
            
            progress = min(i + batch_size, total_count)
            self.stdout.write(f"Progrès: {progress}/{total_count} clubs traités")
        
        return translated_count
    
    def _translate_disciplines(self, ai, target_lang, field_name, dry_run, batch_size, force):
        """Traduit les champs des disciplines."""
        self.stdout.write("Traduction des disciplines...")
        
        translatable_fields = {
            'description': f'description_{target_lang}',
            'rules': f'rules_{target_lang}',
            'history': f'history_{target_lang}'
        }
        
        if field_name:
            if field_name not in translatable_fields:
                raise CommandError(f"Champ non traduisible: {field_name}")
            translatable_fields = {field_name: translatable_fields[field_name]}
        
        disciplines = Discipline.objects.all()
        total_count = disciplines.count()
        translated_count = 0
        
        for i in range(0, total_count, batch_size):
            batch = disciplines[i:i + batch_size]
            
            for discipline in batch:
                updated = False
                
                for source_field, target_field in translatable_fields.items():
                    source_value = getattr(discipline, source_field, None)
                    if not source_value or not source_value.strip():
                        continue
                    
                    target_value = getattr(discipline, target_field, None)
                    if target_value and target_value.strip() and not force:
                        continue
                    
                    translated_text = ai.auto_translate(source_value, target_lang)
                    
                    if translated_text and translated_text != source_value:
                        if not dry_run:
                            setattr(discipline, target_field, translated_text)
                            updated = True
                        
                        self.stdout.write(
                            f"Discipline {discipline.id} - {source_field}: "
                            f"{source_value[:50]}... -> {translated_text[:50]}..."
                        )
                
                if updated and not dry_run:
                    discipline.save()
                    translated_count += 1
            
            progress = min(i + batch_size, total_count)
            self.stdout.write(f"Progrès: {progress}/{total_count} disciplines traitées")
        
        return translated_count

