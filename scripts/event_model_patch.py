
# Patch temporaire pour competitions/models/event.py
# Ajoutez ceci en haut du fichier event.py si nécessaire

from django.db import models

# Patch pour éviter l'erreur EventReminder
class EventReminderDummy(models.Model):
    """Modèle temporaire pour éviter les erreurs"""
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='reminders_dummy')
    send_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'competitions_eventreminder'
        managed = False  # Django ne gère pas cette table
