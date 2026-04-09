# -*- coding: utf-8 -*-
"""
Configuration de l'application Super Admin.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SuperadminConfig(AppConfig):
    """Configuration de l'application superadmin."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.superadmin'
    verbose_name = _('Super Administration')

    def ready(self):
        """
        Actions à exécuter au chargement de l'application.
        Import des signals pour l'audit et les notifications temps réel.
        """
        try:
            import apps.superadmin.signals  # noqa: F401
        except ImportError:
            pass
