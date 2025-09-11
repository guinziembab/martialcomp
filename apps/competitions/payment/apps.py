from django.apps import AppConfig


class PaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.competitions.payment'
    verbose_name = 'Paiements'
    
    def ready(self):
        """Appelé quand l'application est prÃªte."""
        import apps.competitions.payment.signals 
