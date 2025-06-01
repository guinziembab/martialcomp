from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from competitions.models.practitioners import Practitioner
from django.db import models
from django.db.models import Q, Count


class Command(BaseCommand):
    help = 'Vérifie l\'état des utilisateurs et pratiquants dans la base de données'

    def handle(self, *args, **options):
        # Compter les utilisateurs et pratiquants
        total_users = User.objects.count()
        total_practitioners = Practitioner.objects.count()
        
        self.stdout.write(f"Total des utilisateurs: {total_users}")
        self.stdout.write(f"Total des pratiquants: {total_practitioners}")
        self.stdout.write("-" * 50)
        
        # Utilisateurs sans pratiquants
        users_without_practitioners = User.objects.filter(practitioners__isnull=True)
        self.stdout.write(f"\nUtilisateurs sans pratiquant associé: {users_without_practitioners.count()}")
        for user in users_without_practitioners[:10]:  # Limiter à 10 pour l'affichage
            self.stdout.write(f"  - {user.username} ({user.email})")
        
        # Pratiquants sans utilisateur
        practitioners_without_users = Practitioner.objects.filter(user__isnull=True)
        self.stdout.write(f"\nPratiquants sans utilisateur associé: {practitioners_without_users.count()}")
        for practitioner in practitioners_without_users[:10]:
            self.stdout.write(f"  - {practitioner.full_name} ({practitioner.email})")
        
        # Recherche de correspondances potentielles par email
        self.stdout.write("\nCorrespondances potentielles (même email):")
        for user in users_without_practitioners[:10]:
            if user.email:
                matching_practitioner = Practitioner.objects.filter(
                    email=user.email,
                    user__isnull=True
                ).first()
                if matching_practitioner:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  Utilisateur {user.username} ({user.email}) pourrait être associé à "
                            f"Pratiquant {matching_practitioner.full_name}"
                        )
                    )
        
        # Vérifier les doublons
        self.stdout.write("\nVérification des doublons:")
        duplicate_emails = Practitioner.objects.values('email').annotate(
            count=models.Count('email')
        ).filter(count__gt=1, email__isnull=False).exclude(email='')
        
        if duplicate_emails:
            self.stdout.write(self.style.WARNING("Emails en double trouvés:"))
            for item in duplicate_emails:
                self.stdout.write(f"  - {item['email']} ({item['count']} fois)")
        else:
            self.stdout.write(self.style.SUCCESS("Aucun email en double"))