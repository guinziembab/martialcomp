from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from competitions.models import UserProfile

class Command(BaseCommand):
    help = 'Corrige les profils des administrateurs de fédération'

    def handle(self, *args, **kwargs):
        # Trouver les utilisateurs avec le rôle de Federation Admin
        federation_admins = User.objects.filter(username__in=['FEDEMAN', 'FEDEMAN2'])
        
        for admin in federation_admins:
            try:
                # Vérifier si l'utilisateur a un profil
                try:
                    profile = UserProfile.objects.get(user=admin)
                    self.stdout.write(f"Profil trouvé pour {admin.username}")
                    
                    # Mettre à jour le rôle
                    profile.role = 'federation_admin'
                    profile.save()
                    self.stdout.write(self.style.SUCCESS(f"Rôle mis à jour pour {admin.username}"))
                    
                except UserProfile.DoesNotExist:
                    # Créer un nouveau profil
                    profile = UserProfile.objects.create(
                        user=admin,
                        role='federation_admin'
                    )
                    self.stdout.write(self.style.SUCCESS(f"Nouveau profil créé pour {admin.username}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur pour {admin.username}: {str(e)}"))