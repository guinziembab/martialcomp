from django.apps import AppConfig

class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    verbose_name = 'Sécurité'
    
    def ready(self):
        """
        Initialise l'application de sécurité.
        Peut être utilisé pour configurer des signaux ou effectuer d'autres initialisations.
        """
        # Import des signaux si nécessaire
        # import security.signals
        pass