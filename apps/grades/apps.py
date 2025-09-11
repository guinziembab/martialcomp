from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GradesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.grades'
    verbose_name = _("Gestion des Grades")
    
    def ready(self):
        """Initialise les signaux et autres tÃ¢ches au démarrage de l'application."""
        # Importer modeltranslation en premier pour éviter les erreurs de registration
        try:
            # S'assurer que Django est complètement chargé
            from django.apps import apps
            if apps.is_installed('grades'):
                import grades.translation  # noqa
                print("âœ… Configuration de traduction grades chargée avec succès")
        except Exception as e:
            print(f"âŒ Erreur lors de l'importation de grades.translation: {e}")
        
        # Importer les signaux après modeltranslation
        try:
            import apps.grades.signals  # noqa
        except Exception as e:
            print(f"âŒ Erreur lors de l'importation de grades.signals: {e}")

