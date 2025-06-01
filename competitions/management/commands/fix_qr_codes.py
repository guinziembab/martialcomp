from django.core.management.base import BaseCommand
from django.db import transaction
from competitions.models.qr_code import PractitionerQRCode


class Command(BaseCommand):
    help = 'Corrige les problèmes de contraintes uniques sur la table QR codes'

    def handle(self, *args, **options):
        try:
            # Vérifier s'il y a des problèmes avec les IDs
            qr_codes = PractitionerQRCode.objects.all()
            self.stdout.write(f"Total des QR codes: {qr_codes.count()}")
            
            # Lister les premiers éléments
            for qr in qr_codes[:5]:
                self.stdout.write(f"  ID: {qr.id}, Pratiquant: {qr.practitioner}, Code: {qr.code}")
            
            # Vérifier les doublons
            from django.db.models import Count
            duplicates = PractitionerQRCode.objects.values('practitioner').annotate(
                count=Count('practitioner')
            ).filter(count__gt=1)
            
            if duplicates:
                self.stdout.write(self.style.WARNING("Doublons trouvés:"))
                for dup in duplicates:
                    self.stdout.write(f"  Pratiquant ID {dup['practitioner']} a {dup['count']} QR codes")
            else:
                self.stdout.write(self.style.SUCCESS("Aucun doublon trouvé"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur: {str(e)}"))