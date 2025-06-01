from multitenant.middleware.theme_middleware import TenantThemeMiddleware, TenantTemplateMiddleware
from multitenant.middleware.feature_access import FeatureAccessMiddleware

# Thread-local storage for current tenant
import threading
_thread_local = threading.local()

def get_current_tenant():
    """
    Récupère le tenant actuel depuis le contexte thread-local.
    """
    return getattr(_thread_local, 'tenant', None)

def set_current_tenant(tenant):
    """
    Définit manuellement le tenant dans le contexte thread-local.
    Utile pour les tâches en arrière-plan ou les tests.
    """
    _thread_local.tenant = tenant
    if tenant:
        from multitenant.schema_utils import set_schema
        set_schema(tenant.schema_name)
    else:
        from multitenant.schema_utils import set_schema
        set_schema('public')

# Importer TenantMiddleware après avoir défini get_current_tenant et set_current_tenant
# pour éviter l'importation circulaire
from multitenant.middleware.tenant_middleware import TenantMiddleware, TenantContext

__all__ = [
    'TenantThemeMiddleware',
    'TenantTemplateMiddleware',
    'FeatureAccessMiddleware',
    'TenantMiddleware',
    'TenantContext',
    'get_current_tenant',
    'set_current_tenant',
]