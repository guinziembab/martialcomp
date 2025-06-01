from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from competitions.models.practitioners import Practitioner
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Crée ou associe des profils pratiquants pour tous les utilisateurs'

    def handle(self, *args, **options):
        users_without_practitioners = User.objects.filter(practitioners__isnull=True)
        created_count = 0
        associated_count = 0
        
        for user in users_without_practitioners:
            self.stdout.write(f"Traitement de l'utilisateur {user.username}...")
            
            # Chercher un pratiquant existant par email
            existing_practitioner = Practitioner.objects.filter(email=user.email).first()
            
            if existing_practitioner and not existing_practitioner.user:
                # Associer le pratiquant existant à l'utilisateur
                existing_practitioner.user = user
                existing_practitioner.save()
                associated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Pratiquant existant associé: {existing_practitioner.full_name}'
                    )
                )
            elif not existing_practitioner:
                # Créer un nouveau pratiquant
                practitioner = Practitioner.objects.create(
                    user=user,
                    first_name=user.first_name or 'Prénom',
                    last_name=user.last_name or 'Nom',
                    email=user.email,
                    birth_date=timezone.now().date() - timedelta(days=365*25),  # Âge par défaut 25 ans
                    gender='M',  # Par défaut
                    nationality='FR'  # Par défaut
                )
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  Nouveau pratiquant créé: {practitioner.full_name}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nRésumé:\n'
                f'- {created_count} nouveaux pratiquants créés\n'
                f'- {associated_count} pratiquants existants associés\n'
                f'- Total des utilisateurs sans pratiquant traités: {users_without_practitioners.count()}'
            )
        )