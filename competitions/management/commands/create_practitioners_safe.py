from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from competitions.models.practitioners import Practitioner
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models.signals import post_save
import importlib


class Command(BaseCommand):
    help = 'Crée des profils pratiquants pour les utilisateurs sans désactiver temporairement les signaux'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Traiter uniquement cet utilisateur spécifique',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            users = User.objects.filter(username=username, practitioners__isnull=True)
        else:
            users = User.objects.filter(practitioners__isnull=True)
        
        if not users:
            self.stdout.write(self.style.SUCCESS("Aucun utilisateur à traiter"))
            return
        
        self.stdout.write(f"Traitement de {users.count()} utilisateur(s)")
        
        # Désactiver temporairement les signaux pour éviter la création automatique de QR codes
        self.stdout.write("Désactivation temporaire des signaux...")
        
        # Trouver et désactiver le signal qui crée les QR codes
        try:
            # Importer le module de signaux s'il existe
            try:
                signals_module = importlib.import_module('competitions.signals')
                # Déconnecter temporairement les signaux post_save pour Practitioner
                post_save.disconnect(sender=Practitioner)
                self.stdout.write(self.style.WARNING("Signaux déconnectés temporairement"))
            except ImportError:
                pass
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Impossible de déconnecter les signaux: {e}"))
        
        created_count = 0
        errors_count = 0
        
        for user in users:
            try:
                with transaction.atomic():
                    # Créer un nouveau pratiquant sans déclencher les signaux
                    practitioner = Practitioner(
                        user=user,
                        first_name=user.first_name or user.username.split('.')[0].capitalize(),
                        last_name=user.last_name or user.username.split('.')[-1].capitalize(),
                        email=user.email or f"{user.username}@example.com",
                        birth_date=timezone.now().date() - timedelta(days=365*25),
                        gender='M',
                        nationality='FR'
                    )
                    practitioner.save_base(raw=True)  # Sauvegarder sans déclencher les signaux
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Créé: Pratiquant pour {user.username} (ID: {practitioner.id})"
                        )
                    )
                    
            except Exception as e:
                errors_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Erreur pour {user.username}: {str(e)}"
                    )
                )
        
        # Reconnecter les signaux
        try:
            try:
                signals_module = importlib.import_module('competitions.signals')
                # Reconnecter les signaux si on les a déconnectés
                post_save.connect(sender=Practitioner)
                self.stdout.write(self.style.WARNING("Signaux reconnectés"))
            except ImportError:
                pass
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la reconnexion des signaux: {e}"))
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RÉSUMÉ:")
        self.stdout.write(f"  - Utilisateurs traités: {users.count()}")
        self.stdout.write(f"  - Pratiquants créés: {created_count}")
        self.stdout.write(f"  - Erreurs: {errors_count}")
        
        if created_count > 0:
            self.stdout.write(self.style.WARNING(
                "\nNote: Les QR codes n'ont pas été créés automatiquement. "
                "Utilisez la commande manage.py create_qr_codes si nécessaire."
            ))