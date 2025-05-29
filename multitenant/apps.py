"""
App configuration for multi-tenant functionality
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MultitenantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'multitenant'
    verbose_name = _('Multi-tenant')
    
    def ready(self):
        # Import signals and connect them dynamically
        from multitenant.signals import connect_tenant_signals
        connect_tenant_signals()