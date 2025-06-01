from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from competitions.models.practitioners import Practitioner
from django.db import transaction, connection
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
import importlib


class Command(BaseCommand):
    help = 'Crée des profils pratiquants en gérant correctement les QR codes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Traiter uniquement cet utilisateur spécifique',
        )
        parser.add_argument(
            '--no-qr',
            action='store_true',
            help='Ne pas créer de QR codes',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        no_qr = options.get('no_qr')
        
        if username:
            users = User.objects.filter(username=username, practitioners__isnull=True)
        else:
            users = User.objects.filter(practitioners__isnull=True)
        
        if not users:
            self.stdout.write(self.style.SUCCESS("Aucun utilisateur à traiter"))
            return
        
        self.stdout.write(f"Traitement de {users.count()} utilisateur(s)")
        
        # D'abord, réinitialiser la séquence de l'ID pour PractitionerQRCode
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(pg_get_serial_sequence('competitions_practitionerqrcode', 'id'), 
                       COALESCE((SELECT MAX(id) FROM competitions_practitionerqrcode), 0) + 1, 
                       false);
            """)
            self.stdout.write(self.style.SUCCESS("Séquence ID réinitialisée pour PractitionerQRCode"))
        
        # Désactiver temporairement le signal si demandé
        signal_disconnected = False
        if no_qr:
            try:
                from competitions.signals import create_practitioner_qr_code
                post_save.disconnect(create_practitioner_qr_code, sender=Practitioner)
                signal_disconnected = True
                self.stdout.write(self.style.WARNING("Signal QR code désactivé temporairement"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Impossible de désactiver le signal: {e}"))
        
        created_count = 0
        errors_count = 0
        
        for user in users:
            try:
                with transaction.atomic():
                    # Créer un nouveau pratiquant
                    practitioner = Practitioner.objects.create(
                        user=user,
                        first_name=user.first_name or user.username.split('.')[0].capitalize(),
                        last_name=user.last_name or (user.username.split('.')[-1].capitalize() if '.' in user.username else user.username.capitalize()),
                        email=user.email or f"{user.username}@example.com",
                        birth_date=timezone.now().date() - timedelta(days=365*25),
                        gender='M',
                        nationality='FR'
                    )
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Créé: Pratiquant pour {user.username} (ID: {practitioner.id})"
                        )
                    )
                    
                    # Si le QR code n'a pas été créé automatiquement et qu'on le veut
                    if not no_qr and not hasattr(practitioner, 'qr_code'):
                        try:
                            from competitions.models.qr_code import PractitionerQRCode
                            PractitionerQRCode.objects.create(practitioner=practitioner)
                            self.stdout.write(f"  - QR code créé")
                        except Exception as qr_error:
                            self.stdout.write(self.style.WARNING(
                                f"  - Erreur création QR code: {qr_error}"
                            ))
                    
            except Exception as e:
                errors_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Erreur pour {user.username}: {str(e)}"
                    )
                )
        
        # Reconnecter le signal si on l'a déconnecté
        if signal_disconnected:
            try:
                from competitions.signals import create_practitioner_qr_code
                post_save.connect(create_practitioner_qr_code, sender=Practitioner)
                self.stdout.write(self.style.WARNING("Signal QR code réactivé"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la réactivation du signal: {e}"))
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RÉSUMÉ:")
        self.stdout.write(f"  - Utilisateurs traités: {users.count()}")
        self.stdout.write(f"  - Pratiquants créés: {created_count}")
        self.stdout.write(f"  - Erreurs: {errors_count}")
        
        if created_count > 0 and no_qr:
            self.stdout.write(self.style.WARNING(
                "\nNote: Les QR codes n'ont pas été créés. "
                "Utilisez 'manage.py create_qr_codes' si nécessaire."
            ))