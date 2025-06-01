from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FinancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'finances'
    verbose_name = _('Finances')
    
    def ready(self):
        # Import signals first
        import finances.signals
        
        # Instead of explicit imports, just import the models module, which will register all models
        import finances.models