import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Copie le logo depuis le répertoire Images vers static/images'

    def handle(self, *args, **options):
        # Chemins source et destination
        source_path = os.path.join(settings.BASE_DIR, '..', 'Images', 'logo.png')
        dest_dir = os.path.join(settings.BASE_DIR, 'competitions', 'static', 'images')
        dest_path = os.path.join(dest_dir, 'logo.png')
        
        # Créer le répertoire de destination s'il n'existe pas
        os.makedirs(dest_dir, exist_ok=True)
        
        # Copier le fichier
        try:
            if os.path.exists(source_path):
                shutil.copy2(source_path, dest_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Logo copié avec succès de {source_path} vers {dest_path}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'Le fichier source n\'existe pas : {source_path}'
                    )
                )
                
                # Essayer un autre chemin
                alt_source_path = os.path.join(settings.BASE_DIR, 'Images', 'logo.png')
                if os.path.exists(alt_source_path):
                    shutil.copy2(alt_source_path, dest_path)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Logo copié depuis le chemin alternatif : {alt_source_path}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            'Aucun fichier logo.png trouvé. Veuillez le copier manuellement.'
                        )
                    )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Erreur lors de la copie : {str(e)}'
                )
            )
        
        # Vérifier si le fichier est bien copié
        if os.path.exists(dest_path):
            self.stdout.write(
                self.style.SUCCESS(
                    'Le logo est maintenant disponible dans le répertoire static.'
                )
            )
