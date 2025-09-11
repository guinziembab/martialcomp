# -*- coding: utf-8 -*-
"""
Configuration de l'application Membership pour MartialComp v2.0
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MembershipConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.membership'
    verbose_name = _('Système d\'Adhésion')
    
    def ready(self):
        """Initialisation de l'application"""
        try:
            # Import des signaux pour l'activation des workflows
            from . import signals
        except ImportError:
            pass