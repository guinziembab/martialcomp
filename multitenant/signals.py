"""
Signals for multi-tenant functionality
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.apps import apps
import logging

logger = logging.getLogger(__name__)

# Nous obtiendrons le modèle Tenant de manière dynamique pour éviter les importations circulaires
Tenant = None  # Sera initialisé plus tard


def create_tenant_schema(sender, instance, created, **kwargs):
    """
    Create schema when a new tenant is created
    """
    if created and instance.schema_name:
        try:
            create_schema_for_tenant(instance)
            logger.info(f"Created schema for tenant: {instance.name}")
        except Exception as e:
            logger.error(f"Error creating schema for tenant {instance.name}: {str(e)}")
            # Don't raise the exception - let the tenant be created even if schema fails
            # This can be fixed later with a management command


def delete_tenant_schema(sender, instance, **kwargs):
    """
    Delete schema when a tenant is deleted
    """
    if instance.schema_name:
        try:
            drop_tenant_schema(instance)
            logger.info(f"Deleted schema for tenant: {instance.name}")
        except Exception as e:
            logger.error(f"Error deleting schema for tenant {instance.name}: {str(e)}")
            # Continue with tenant deletion even if schema deletion fails

def create_schema_for_tenant(tenant):
    """Crée le schéma PostgreSQL pour un tenant"""
    from .schema_utils import create_schema
    create_schema(tenant.schema_name)

def drop_tenant_schema(tenant):
    """Supprime le schéma PostgreSQL d'un tenant"""
    from .schema_utils import drop_schema
    drop_schema(tenant.schema_name)


def connect_tenant_signals():
    """
    Connecte les signaux pour le modèle Tenant de manière dynamique
    pour éviter les importations circulaires.
    """
    Tenant = apps.get_model('multitenant', 'Tenant')
    
    # Connecter les signaux
    post_save.connect(create_tenant_schema, sender=Tenant)
    pre_delete.connect(delete_tenant_schema, sender=Tenant)
    
    logger.info("Tenant signals connected successfully")
