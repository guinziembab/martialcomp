from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.competitions.models.practitioners import Practitioner
from django.db import transaction
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Associe les utilisateurs aux pratiquants ou crée de nouveaux profils pratiquants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Traiter uniquement cet utilisateur spécifique',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simuler les changements sans les appliquer',
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Créer des profils pratiquants pour les utilisateurs sans correspondance',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        dry_run = options.get('dry_run')
        create_missing = options.get('create_missing')
        
        if username:
            users = User.objects.filter(username=username)
        else:
            users = User.objects.filter(practitioners__isnull=True)
        
        if not users:
            self.stdout.write(self.style.SUCCESS("Aucun utilisateur Ã  traiter"))
            return
        
        self.stdout.write(f"Traitement de {users.count()} utilisateur(s)")
        
        associated_count = 0
        created_count = 0
        errors_count = 0
        
        for user in users:
            try:
                with transaction.atomic():
                    # Chercher un pratiquant existant par email
                    if user.email:
                        existing_practitioner = Practitioner.objects.filter(
                            email=user.email,
                            user__isnull=True
                        ).first()
                        
                        if existing_practitioner:
                            if not dry_run:
                                existing_practitioner.user = user
                                existing_practitioner.save()
                            associated_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"{'[DRY RUN] ' if dry_run else ''}Associé: {user.username} -> {existing_practitioner.full_name}"
                                )
                            )
                            continue
                    
                    # Créer un nouveau pratiquant si demandé
                    if create_missing:
                        if not dry_run:
                            practitioner = Practitioner.objects.create(
                                user=user,
                                first_name=user.first_name or user.username.split('.')[0].capitalize(),
                                last_name=user.last_name or user.username.split('.')[-1].capitalize(),
                                email=user.email or f"{user.username}@example.com",
                                birth_date=timezone.now().date() - timedelta(days=365*25),
                                gender='M',
                                nationality='FR'
                            )
                        created_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"{'[DRY RUN] ' if dry_run else ''}Créé: Pratiquant pour {user.username}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Aucune correspondance pour {user.username} ({user.email})"
                            )
                        )
                        
            except Exception as e:
                errors_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Erreur pour {user.username}: {str(e)}"
                    )
                )
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RÃ‰SUMÃ‰:")
        self.stdout.write(f"  - Utilisateurs traités: {users.count()}")
        self.stdout.write(f"  - Pratiquants associés: {associated_count}")
        self.stdout.write(f"  - Pratiquants créés: {created_count}")
        self.stdout.write(f"  - Erreurs: {errors_count}")
        if dry_run:
            self.stdout.write(self.style.WARNING("\n[MODE DRY RUN - Aucun changement effectué]"))

