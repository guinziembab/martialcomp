from django.apps import AppConfig

class CompetitionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.competitions'
    # Explicit app label to match migration references like 'competitions.Discipline'
    label = 'competitions'
    verbose_name = 'Competitions'
    
    def ready(self):
        import apps.competitions.signals  # Importer les signaux
        import apps.competitions.allauth_signals  # Importer les signaux allauth
        import apps.competitions.translation  # Importer les configurations de traduction
