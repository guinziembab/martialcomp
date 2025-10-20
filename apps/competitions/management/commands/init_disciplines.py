"""
Commande Django pour initialiser les disciplines par défaut
Usage: python manage.py init_disciplines
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.competitions.models import Discipline
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize default martial arts disciplines'

    def handle(self, *args, **kwargs):
        default_disciplines = [
            'Karaté', 'Judo', 'Taekwondo', 'Ju-Jitsu', 'Aïkido',
            'Kung Fu', 'Muay Thai', 'Krav Maga', 'Capoeira', 'MMA',
            'Boxe', 'Kickboxing', 'Sambo', 'Hapkido', 'Kendo'
        ]
        
        created = 0
        existing = 0
        
        try:
            with transaction.atomic():
                for name in default_disciplines:
                    discipline, was_created = Discipline.objects.get_or_create(
                        name=name,
                        defaults={'is_active': True}
                    )
                    if was_created:
                        created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Created: {name}')
                        )
                        logger.info(f'Created discipline: {name}')
                    else:
                        existing += 1
                        # Ensure existing disciplines are active
                        if not discipline.is_active:
                            discipline.is_active = True
                            discipline.save()
                            self.stdout.write(
                                self.style.WARNING(f'⚠️  Activated existing discipline: {name}')
                            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n📊 Summary: {created} created, {existing} existing, {created + existing} total active disciplines'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error initializing disciplines: {e}')
            )
            logger.error(f'Error in init_disciplines command: {e}', exc_info=True)
            raise