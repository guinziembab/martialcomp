from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

# Les signaux seront ajoutés ici Ã  mesure que nous développerons les modèles
