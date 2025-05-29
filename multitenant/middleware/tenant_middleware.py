"""
Middleware principal pour l'isolation des tenants.
"""
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import DisallowedHost
from django.conf import settings
import logging

from multitenant.models import Tenant, Domain
from multitenant.schema_utils import set_schema
from multitenant.middleware import _thread_local

logger = logging.getLogger(__name__)


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
        # Sauvegarder le token CSRF avant de modifier quoi que ce soit
        # Sauvegarder le token CSRF et la méthode
        csrf_token = getattr(request, '_cached_csrf_token', None)
        csrf_cookie = request.COOKIES.get('csrftoken', None)
        
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
        
        # Restaurer le token CSRF si nécessaire
        # Restaurer le token CSRF
        if csrf_token:
            request._cached_csrf_token = csrf_token
        if csrf_cookie and 'csrftoken' not in request.COOKIES:
            request.COOKIES['csrftoken'] = csrf_cookie
        
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


class TenantContext:
    """
    Gestionnaire de contexte pour exécuter du code dans le contexte d'un tenant spécifique.
    """
    def __init__(self, tenant):
        self.tenant = tenant
        self.previous_tenant = None
        self.previous_schema = None
    
    def __enter__(self):
        from multitenant.middleware import get_current_tenant
        from multitenant.schema_utils import get_current_schema, set_schema
        
        self.previous_tenant = get_current_tenant()
        self.previous_schema = get_current_schema()
        
        # Utiliser set_current_tenant via une importation tardive pour éviter les cycles
        if self.tenant:
            _thread_local.tenant = self.tenant
            set_schema(self.tenant.schema_name)
        else:
            _thread_local.tenant = None
            set_schema('public')
            
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from multitenant.schema_utils import set_schema
        
        # Restaurer le tenant précédent
        _thread_local.tenant = self.previous_tenant
        
        # Restaurer le schéma précédent
        if self.previous_schema:
            set_schema(self.previous_schema)
        else:
            set_schema('public')

# Alias pour la compatibilité avec l'ancien code
tenant_context = TenantContext