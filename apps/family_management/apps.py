from django.apps import AppConfig


class FamilyManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.family_management'
    verbose_name = 'Gestion Familiale'
    
    def ready(self):
        """Import des signaux pour l'application family_management"""
        try:
            import apps.family_management.signals
        except ImportError:
            pass
