from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.organizations'
    
    def ready(self):
        """Importer les signaux lors du démarrage de l'application."""
        import apps.organizations.signals


