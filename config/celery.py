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

    # =========================================================================
    # PROMPT 2: Notifications de Grade
    # =========================================================================

    # Verification quotidienne eligibilite grade (J-30, J-7, J-0)
    'check-grade-eligibility-daily': {
        'task': 'competitions.tasks.check_grade_eligibility_daily',
        'schedule': crontab(hour=8, minute=0),  # Tous les jours a 8h00
    },

    # Verification des deadlines d'inscription aux examens (J-14, J-3)
    'check-exam-deadlines-daily': {
        'task': 'competitions.tasks.check_exam_deadlines_daily',
        'schedule': crontab(hour=9, minute=30),  # Tous les jours a 9h30
    },

    # Rappels J-1 aux inscrits aux examens
    'send-exam-reminders': {
        'task': 'competitions.tasks.send_exam_reminders',
        'schedule': crontab(hour=18, minute=0),  # Tous les jours a 18h00
    },

    # Rappels mensuels aux eligibles non inscrits
    'send-monthly-eligibility-reminders': {
        'task': 'competitions.tasks.send_monthly_eligibility_reminders',
        'schedule': crontab(day_of_month=1, hour=10, minute=0),  # 1er du mois a 10h00
    },

    # =========================================================================
    # Affiliations Saisonnières
    # =========================================================================

    # Vérification quotidienne des renouvellements d'affiliation
    'check-affiliation-renewals': {
        'task': 'organizations.tasks.check_affiliation_renewals',
        'schedule': crontab(hour=7, minute=0),  # Tous les jours à 7h00
    },

    # Mise à jour quotidienne des affiliations expirées
    'update-expired-affiliations': {
        'task': 'organizations.tasks.update_expired_affiliations',
        'schedule': crontab(hour=0, minute=30),  # Tous les jours à 0h30
    },

    # =========================================================================
    # Nettoyage juges ad-hoc
    # =========================================================================

    'cleanup-adhoc-judges': {
        'task': 'competitions.tasks.cleanup_adhoc_judges',
        'schedule': crontab(hour=1, minute=0),  # Tous les jours a 1h00
    },

    # =========================================================================
    # Multi-devise - Mise a jour des taux de change
    # =========================================================================

    # Mise a jour des taux de change (2x par jour)
    'update-exchange-rates-morning': {
        'task': 'finances.tasks.update_exchange_rates',
        'schedule': crontab(hour=6, minute=0),  # Tous les jours a 6h00
    },
    'update-exchange-rates-evening': {
        'task': 'finances.tasks.update_exchange_rates',
        'schedule': crontab(hour=18, minute=0),  # Tous les jours a 18h00
    },

    # Rafraichissement des taux fixes CFA (hebdomadaire)
    'refresh-cfa-fixed-rates': {
        'task': 'finances.tasks.refresh_cfa_fixed_rates',
        'schedule': crontab(day_of_week=0, hour=5, minute=0),  # Dimanche a 5h00
    },

    # Nettoyage des anciens taux (mensuel)
    'cleanup-old-exchange-rates': {
        'task': 'finances.tasks.cleanup_old_exchange_rates',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),  # 1er du mois a 3h00
    },

    # Rapport mensuel des conversions
    'generate-currency-report': {
        'task': 'finances.tasks.generate_monthly_currency_report',
        'schedule': crontab(day_of_month=2, hour=8, minute=0),  # 2 du mois a 8h00
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 