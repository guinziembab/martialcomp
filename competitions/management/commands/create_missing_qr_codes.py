from django.core.management.base import BaseCommand
from competitions.models.practitioners import Practitioner
from competitions.models.qr_code import PractitionerQRCode
from django.db import connection


class Command(BaseCommand):
    help = 'Crée les QR codes manquants pour les pratiquants'

    def handle(self, *args, **options):
        # D'abord, réinitialiser la séquence de l'ID
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(pg_get_serial_sequence('competitions_practitionerqrcode', 'id'), 
                       COALESCE((SELECT MAX(id) FROM competitions_practitionerqrcode), 0) + 1, 
                       false);
            """)
            self.stdout.write(self.style.SUCCESS("Séquence ID réinitialisée"))
        
        # Trouver les pratiquants sans QR code
        practitioners_without_qr = Practitioner.objects.filter(qr_code__isnull=True)
        
        self.stdout.write(f"Pratiquants sans QR code: {practitioners_without_qr.count()}")
        
        created_count = 0
        errors_count = 0
        
        for practitioner in practitioners_without_qr:
            try:
                qr_code = PractitionerQRCode.objects.create(practitioner=practitioner)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"QR code créé pour {practitioner.full_name} (ID: {qr_code.id})"
                    )
                )
            except Exception as e:
                errors_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Erreur pour {practitioner.full_name}: {str(e)}"
                    )
                )
        
        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RÉSUMÉ:")
        self.stdout.write(f"  - QR codes créés: {created_count}")
        self.stdout.write(f"  - Erreurs: {errors_count}")