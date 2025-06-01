from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from competitions.models import UserProfile

class Command(BaseCommand):
    help = 'Crée des profils utilisateurs pour les utilisateurs qui n\'en ont pas'

    def handle(self, *args, **kwargs):
        count = 0
        # Récupérer les ID des utilisateurs qui ont déjà un profil
        existing_profiles = set(UserProfile.objects.values_list('user_id', flat=True))
        
        # Pour chaque utilisateur qui n'a pas encore de profil, en créer un
        for user in User.objects.all():
            if user.id not in existing_profiles:
                UserProfile.objects.create(user=user)
                count += 1
                self.stdout.write(self.style.SUCCESS(f"Profil créé pour {user.username}"))
            else:
                self.stdout.write(f"Le profil pour {user.username} existe déjà")
        
        # Afficher un résumé
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ {count} profils utilisateurs ont été créés avec succès"))
        else:
            self.stdout.write(self.style.WARNING("Aucun nouveau profil n'a été créé. Tous les utilisateurs ont déjà un profil"))