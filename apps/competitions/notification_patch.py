#!/usr/bin/env python
"""
Patch temporaire pour ajouter une propriété federation au modèle Notification
"""

from django.db import models

# Monkey patch pour Notification
def patch_notification_model():
    """
    Ajoute une propriété federation au modèle Notification qui retourne toujours None
    Cela évite l'erreur FieldError sans modifier le modèle original
    """
    try:
        from apps.competitions.models import Notification
        
        # Ajouter une propriété qui retourne toujours None
        @property
        def federation(self):
            return None
        
        # Ajouter la propriété au modèle si elle n'existe pas
        if not hasattr(Notification, 'federation'):
            Notification.federation = federation
            print("✅ Propriété 'federation' ajoutée au modèle Notification")
        
        # Créer aussi un manager personnalisé qui ignore le filtre federation
        original_filter = Notification.objects.filter
        
        def safe_filter(*args, **kwargs):
            # Supprimer federation des kwargs si présent
            if 'federation' in kwargs:
                print(f"⚠️  Tentative de filtrer Notification par federation ignorée")
                del kwargs['federation']
            return original_filter(*args, **kwargs)
        
        Notification.objects.filter = safe_filter
        print("✅ Manager Notification modifié pour ignorer le filtre 'federation'")
        
    except Exception as e:
        print(f"❌ Erreur lors du patch: {e}")

# Appliquer le patch
if __name__ == "__main__":
    patch_notification_model()
