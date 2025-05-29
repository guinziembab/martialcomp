from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import DisallowedHost
from django.db import connection
from django.conf import settings
import threading
import logging

from .models import Tenant, Domain
from .schema_utils import set_schema, get_current_schema


logger = logging.getLogger(__name__)

# Thread-local storage pour le tenant courant
_thread_local = threading.local()


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware pour l'identification et l'isolation des tenants.
    
    Ce middleware:
    1. Identifie le tenant à partir du domaine de la requête
    2. Configure le schéma PostgreSQL approprié
    3. Stocke le tenant dans un contexte thread-local
    """
    
    def process_request(self, request):
        """
        Traite chaque requête pour identifier le tenant.
        """
        # Réinitialiser le contexte tenant
        _thread_local.tenant = None
        
        # Obtenir le hostname depuis la requête
        hostname = request.get_host().split(':')[0].lower()
        
        # Rechercher le tenant par domaine
        tenant = self._get_tenant_by_domain(hostname)
        
        if tenant is None:
            # Vérifier s'il s'agit du domaine principal (non-tenant)
            if hostname in getattr(settings, 'PUBLIC_DOMAINS', ['localhost', '127.0.0.1']):
                # Utiliser le schéma public pour les domaines publics
                set_schema('public')
                request.tenant = None
                return
            
            # Si aucun tenant trouvé et pas un domaine public, lever une exception
            raise DisallowedHost(f"Aucun tenant trouvé pour le domaine: {hostname}")
        
        # Si tenant trouvé, configurer le schéma
        if not tenant.is_active:
            raise DisallowedHost(f"Le tenant {tenant.name} n'est pas actif")
        
        # Configurer le schéma PostgreSQL
        set_schema(tenant.schema_name)
        
        # Stocker le tenant dans la requête et le contexte thread-local
        request.tenant = tenant
        _thread_local.tenant = tenant
        
        logger.debug(f"Tenant configuré: {tenant.name} (schéma: {tenant.schema_name})")
    
    def process_response(self, request, response):
        """
        Réinitialise le schéma après chaque requête.
        """
        # Revenir au schéma public après traitement
        set_schema('public')
        _thread_local.tenant = None
        
        return response
    
    def _get_tenant_by_domain(self, hostname):
        """
        Recherche un tenant par son domaine.
        """
        try:
            # D'abord chercher dans les domaines secondaires
            domain = Domain.objects.filter(domain=hostname).select_related('tenant').first()
            if domain:
                return domain.tenant
            
            # Ensuite chercher dans les domaines principaux des tenants
            tenant = Tenant.objects.filter(domain=hostname).first()
            if tenant:
                return tenant
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche du tenant: {e}")
        
        return None


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
        set_schema(tenant.schema_name)
    else:
        set_schema('public')


class TenantContext:
    """
    Gestionnaire de contexte pour exécuter du code dans le contexte d'un tenant spécifique.
    """
    def __init__(self, tenant):
        self.tenant = tenant
        self.previous_tenant = None
        self.previous_schema = None
    
    def __enter__(self):
        self.previous_tenant = get_current_tenant()
        self.previous_schema = get_current_schema()
        set_current_tenant(self.tenant)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        set_current_tenant(self.previous_tenant)
        if self.previous_schema:
            set_schema(self.previous_schema)