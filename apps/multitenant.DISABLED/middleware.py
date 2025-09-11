"""
Ce module est conservé pour compatibilité mais tout le code a été déplacé vers les modules
multitenant.middleware.__init__ et multitenant.middleware.tenant_middleware
pour résoudre les problèmes d'importation circulaire.

Utilisez ces imports Ã  la place:

from apps.multitenant.middleware import get_current_tenant, set_current_tenant
from apps.multitenant.middleware import TenantMiddleware, TenantContext
"""

# Redirige les imports pour compatibilité
from apps.multitenant.middleware import get_current_tenant, set_current_tenant
from apps.multitenant.middleware import TenantMiddleware, TenantContext

# Alias pour la compatibilité avec l'ancien code
tenant_context = TenantContext


