from django.apps import AppConfig


class FamilyManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'family_management'
    verbose_name = 'Gestion Familiale'
    
    def ready(self):
        """Import des signaux pour l'application family_management"""
        try:
            import family_management.signals
        except ImportError:
            pass