from django.core.management.base import BaseCommand
from apps.finances.models.payments import PaymentMethod

DEFAULT_METHODS = [
    {"name": "Espèces", "type": "cash"},
    {"name": "Carte bancaire", "type": "card"},
    {"name": "Virement bancaire", "type": "transfer"},
    {"name": "Chèque", "type": "check"},
    {"name": "Prélèvement automatique", "type": "direct_debit"},
    {"name": "PayPal", "type": "paypal"},
    {"name": "Stripe", "type": "stripe"},
    {"name": "Autre", "type": "other"},
]

class Command(BaseCommand):
    help = "Initialise les méthodes de paiement par défaut actives."

    def handle(self, *args, **options):
        created = 0
        for m in DEFAULT_METHODS:
            obj, was_created = PaymentMethod.objects.get_or_create(
                type=m["type"],
                defaults={
                    "name": m["name"],
                    "description": "",
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Méthodes de paiement initialisées. Nouvelles: {created}"))
