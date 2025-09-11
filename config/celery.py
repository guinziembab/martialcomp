import os
from celery import Celery
from celery.schedules import crontab

# Définir les paramètres par défaut de Django pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('martialcomp')

# Utiliser une chaîne de caractères ici signifie que le worker n'a pas à sérialiser
# l'objet de configuration vers les processus enfants.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Charger les tâches depuis tous les modules Django enregistrés
app.autodiscover_tasks()

# Configuration des tâches périodiques
app.conf.beat_schedule = {
    'send-payment-reminders': {
        'task': 'utils.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # Tous les jours à 9h00
    },
    'send-competition-reminders': {
        'task': 'utils.tasks.send_competition_reminders',
        'schedule': crontab(hour=10, minute=0),  # Tous les jours à 10h00
    },
    'send-subscription-expiry-reminders': {
        'task': 'utils.tasks.send_subscription_expiry_reminders',
        'schedule': crontab(hour=11, minute=0),  # Tous les jours à 11h00
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 