from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ChatConfig(AppConfig):
    """
    PROMPT 11 - Configuration de l'application Chat.
    Système de messagerie interne pour MartialComp.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'
    verbose_name = _("Messagerie")

    def ready(self):
        # Import des signaux si nécessaire
        try:
            import apps.chat.signals  # noqa
        except ImportError:
            pass
