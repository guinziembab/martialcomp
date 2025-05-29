from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GradesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grades'
    verbose_name = _("Gestion des Grades")
    
    def ready(self):
        """Initialise les signaux et autres tâches au démarrage de l'application."""
        import grades.signals  # noqa