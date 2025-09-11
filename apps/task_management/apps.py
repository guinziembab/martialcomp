from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TaskManagementConfig(AppConfig):
    """Configuration for Task Management module"""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.task_management'
    verbose_name = _('Gestion de Tâches')
    
    def ready(self):
        """Configure the app when ready"""
        try:
            import apps.task_management.signals  # noqa
        except ImportError:
            pass