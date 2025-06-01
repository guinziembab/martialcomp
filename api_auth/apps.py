from django.apps import AppConfig


class ApiAuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_auth'
    verbose_name = 'API Authentication'

    def ready(self):
        import api_auth.signals  # noqa