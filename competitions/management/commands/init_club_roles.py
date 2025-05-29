# competitions/management/commands/init_club_roles.py
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from competitions.models.base import Club
from competitions.models.permissions import ClubRole

class Command(BaseCommand):
    help = 'Initialise les rôles par défaut pour tous les clubs'

    def handle(self, *args, **options):
        clubs = Club.objects.all()
        roles_created = 0
        
        for club in clubs:
            # Vérifier si le club a déjà des rôles
            existing_roles = ClubRole.objects.filter(club=club).count()
            if existing_roles > 0:
                self.stdout.write(f"Le club '{club.name}' a déjà des rôles définis. Ignoré.")
                continue
                
            # Créer les rôles par défaut
            roles = [
                {
                    'name': _('Administrateur'),
                    'description': _('Accès complet à toutes les fonctionnalités du club'),
                    'is_default': False,
                    'can_manage_practitioners': True,
                    'can_manage_registrations': True,
                    'can_manage_competitions': True,
                    'can_manage_judges': True,
                    'can_manage_grades': True,
                    'can_manage_roles': True,
                },
                {
                    'name': _('Coach'),
                    'description': _('Gestion des pratiquants et des inscriptions'),
                    'is_default': True,
                    'can_manage_practitioners': True,
                    'can_manage_registrations': True,
                    'can_manage_competitions': False,
                    'can_manage_judges': False,
                    'can_manage_grades': True,
                    'can_manage_roles': False,
                },
                {
                    'name': _('Secrétaire'),
                    'description': _('Gestion administrative du club'),
                    'is_default': False,
                    'can_manage_practitioners': True,
                    'can_manage_registrations': True,
                    'can_manage_competitions': True,
                    'can_manage_judges': False,
                    'can_manage_grades': False,
                    'can_manage_roles': False,
                },
            ]
            
            for role_data in roles:
                ClubRole.objects.create(club=club, **role_data)
                roles_created += 1
                
            self.stdout.write(self.style.SUCCESS(f"Rôles créés pour le club '{club.name}'"))
        
        self.stdout.write(self.style.SUCCESS(f"{roles_created} rôles créés au total pour {clubs.count()} clubs"))