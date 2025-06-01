from django.db import connection
from django.core.exceptions import ImproperlyConfigured
import re

from .models import Tenant


def create_schema_for_tenant(tenant):
    """
    Crée un schéma PostgreSQL pour un tenant.
    
    Args:
        tenant: Instance de Tenant
    """
    if not tenant.schema_name:
        raise ImproperlyConfigured(f"Le tenant {tenant.name} n'a pas de nom de schéma défini")
    
    # Validation du nom de schéma
    if not re.match('^[a-z][a-z0-9_]*$', tenant.schema_name):
        raise ImproperlyConfigured(
            f"Nom de schéma invalide: {tenant.schema_name}. "
            "Doit commencer par une lettre et contenir uniquement lettres minuscules, chiffres et underscores."
        )
    
    with connection.cursor() as cursor:
        # Créer le schéma
        cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{tenant.schema_name}"')
        
        # Donner les permissions appropriées à l'utilisateur de la base
        cursor.execute(f'GRANT ALL ON SCHEMA "{tenant.schema_name}" TO {connection.settings_dict["USER"]}')


def drop_tenant_schema(tenant, cascade=False):
    """
    Supprime un schéma PostgreSQL pour un tenant.
    
    Args:
        tenant: Instance de Tenant
        cascade: Si True, supprime aussi tous les objets dans le schéma
    """
    if not tenant.schema_name:
        return
    
    with connection.cursor() as cursor:
        cascade_clause = 'CASCADE' if cascade else 'RESTRICT'
        cursor.execute(f'DROP SCHEMA IF EXISTS "{tenant.schema_name}" {cascade_clause}')


def tenant_exists(domain=None, slug=None):
    """
    Vérifie si un tenant existe.
    
    Args:
        domain: Domaine à vérifier
        slug: Slug à vérifier
        
    Returns:
        bool: True si le tenant existe
    """
    if domain:
        return Tenant.objects.filter(domain=domain).exists()
    if slug:
        return Tenant.objects.filter(slug=slug).exists()
    return False


def get_tenant_for_request(request):
    """
    Obtient le tenant pour une requête donnée.
    
    Args:
        request: Objet HttpRequest
        
    Returns:
        Tenant ou None
    """
    if hasattr(request, 'tenant'):
        return request.tenant
    
    # Essayer de trouver le tenant depuis le domaine
    hostname = request.get_host().split(':')[0].lower()
    
    try:
        # Chercher par domaine principal
        return Tenant.objects.get(domain=hostname, is_active=True)
    except Tenant.DoesNotExist:
        pass
    
    # Chercher par sous-domaine
    if hostname.endswith('.martialcomp.com'):
        subdomain = hostname.split('.')[0]
        try:
            return Tenant.objects.get(slug=subdomain, is_active=True)
        except Tenant.DoesNotExist:
            pass
    
    return None


def set_tenant_schema(tenant):
    """
    Configure le schéma de base de données pour un tenant.
    
    Args:
        tenant: Instance de Tenant ou nom de schéma
    """
    if isinstance(tenant, Tenant):
        schema_name = tenant.schema_name
    else:
        schema_name = tenant
    
    connection.set_schema(schema_name)


def reset_schema():
    """
    Réinitialise le schéma à 'public'.
    """
    connection.set_schema('public')


class SchemaContext:
    """
    Context manager pour exécuter du code dans un schéma spécifique.
    
    Utilisation:
        with SchemaContext('tenant_abc'):
            # Code exécuté dans le schéma tenant_abc
            pass
    """
    
    def __init__(self, schema_name):
        self.schema_name = schema_name
        self.previous_schema = None
    
    def __enter__(self):
        self.previous_schema = connection.schema_name
        connection.set_schema(self.schema_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        connection.set_schema(self.previous_schema)


def get_tenants_list():
    """
    Obtient la liste de tous les tenants actifs.
    
    Returns:
        QuerySet de Tenant
    """
    return Tenant.objects.filter(is_active=True).order_by('name')


def validate_schema_name(schema_name):
    """
    Valide qu'un nom de schéma est valide pour PostgreSQL.
    
    Args:
        schema_name: Nom à valider
        
    Returns:
        bool: True si valide
        
    Raises:
        ValueError: Si le nom n'est pas valide
    """
    if not schema_name:
        raise ValueError("Le nom de schéma ne peut pas être vide")
    
    if len(schema_name) > 63:
        raise ValueError("Le nom de schéma ne peut pas dépasser 63 caractères")
    
    if not re.match('^[a-z][a-z0-9_]*$', schema_name):
        raise ValueError(
            "Le nom de schéma doit commencer par une lettre minuscule "
            "et contenir uniquement lettres minuscules, chiffres et underscores"
        )
    
    # Vérifier les mots réservés PostgreSQL
    reserved_words = [
        'all', 'analyse', 'analyze', 'and', 'any', 'array', 'as', 'asc',
        'authorization', 'between', 'binary', 'both', 'case', 'cast',
        'check', 'collate', 'column', 'constraint', 'create', 'cross',
        'current', 'default', 'deferrable', 'desc', 'distinct', 'do',
        'else', 'end', 'except', 'false', 'for', 'foreign', 'freeze',
        'from', 'full', 'grant', 'group', 'having', 'in', 'initially',
        'inner', 'intersect', 'into', 'is', 'isnull', 'join', 'leading',
        'left', 'like', 'limit', 'natural', 'not', 'notnull', 'null',
        'offset', 'on', 'only', 'or', 'order', 'outer', 'overlaps',
        'placing', 'primary', 'references', 'right', 'select', 'session_user',
        'similar', 'some', 'table', 'then', 'to', 'trailing', 'true',
        'union', 'unique', 'user', 'using', 'verbose', 'when', 'where',
        'public', 'pg_catalog', 'information_schema'
    ]
    
    if schema_name.lower() in reserved_words:
        raise ValueError(f"'{schema_name}' est un mot réservé PostgreSQL")
    
    return True


