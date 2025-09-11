from django.core.management.base import BaseCommand
from django.apps import apps

class Command(BaseCommand):
    help = 'Migre les propriétaires vers les nouveaux modèles d\'administrateurs'

    def handle(self, *args, **options):
        # Récupérer les modèles de manière dynamique
        Federation = apps.get_model('competitions', 'Federation')
        Club = apps.get_model('competitions', 'Club')
        FederationAdministrator = apps.get_model('competitions', 'FederationAdministrator')
        ClubAdministrator = apps.get_model('competitions', 'ClubAdministrator')
        
        self.stdout.write("Migration des propriétaires de fédérations...")
        count_fed = 0
        for federation in Federation.objects.all():
            if federation.owner:
                FederationAdministrator.objects.get_or_create(
                    user=federation.owner,
                    federation=federation,
                    defaults={
                        'role': 'owner',
                        'is_primary': True
                    }
                )
                count_fed += 1
        
        self.stdout.write(self.style.SUCCESS(f"Migré {count_fed} propriétaires de fédérations"))
        
        self.stdout.write("Migration des propriétaires de clubs...")
        count_club = 0
        for club in Club.objects.all():
            if hasattr(club, 'owner') and club.owner:
                ClubAdministrator.objects.get_or_create(
                    user=club.owner,
                    club=club,
                    defaults={
                        'role': 'owner',
                        'is_primary': True
                    }
                )
                count_club += 1
        
        self.stdout.write(self.style.SUCCESS(f"Migré {count_club} propriétaires de clubs"))