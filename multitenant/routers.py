"""
Database router for multi-tenant architecture
"""
from django.db import connection
from .utils import get_tenant_for_request


class TenantDatabaseRouter:
    """
    A router to control database operations on models for multi-tenancy.
    """
    
    # Models that should always use the public schema
    PUBLIC_SCHEMA_MODELS = [
        'contenttypes',
        'sessions',
        'admin',
        'multitenant',
        # Add other app labels that should remain in public schema
    ]
    
    def db_for_read(self, model, **hints):
        """
        Suggest the database to read from.
        Returns None to use the default database.
        """
        return self._get_db(model, **hints)
    
    def db_for_write(self, model, **hints):
        """
        Suggest the database for writes.
        Returns None to use the default database.
        """
        return self._get_db(model, **hints)
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if they are in the same schema.
        """
        # If both models are in the public schema, allow relation
        if (self._is_public_model(obj1) and self._is_public_model(obj2)):
            return True
        
        # If both models are tenant-specific and in the same tenant, allow
        if (not self._is_public_model(obj1) and not self._is_public_model(obj2)):
            return True
        
        # Don't allow relations between public and tenant-specific models
        return False
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure that migrations run in the correct schema.
        """
        # Public schema models always migrate
        if app_label in self.PUBLIC_SCHEMA_MODELS:
            return getattr(connection, 'schema_name', 'public') == 'public'
        
        # Tenant models only migrate in tenant schemas
        return getattr(connection, 'schema_name', 'public') != 'public'
    
    def _get_db(self, model, **hints):
        """
        Determine which database/schema to use.
        Returns None to use the default database with schema routing.
        """
        # For now, we're using a single database with schema separation
        return None
    
    def _is_public_model(self, obj):
        """
        Check if a model should use the public schema.
        """
        if hasattr(obj, '_meta'):
            return obj._meta.app_label in self.PUBLIC_SCHEMA_MODELS
        return False