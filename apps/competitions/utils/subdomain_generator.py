#!/usr/bin/env python3
"""
Générateur de sous-domaines automatiques pour les organisations MartialComp.
Intégration avec le système multi-tenant existant.
"""

import re
import unicodedata
from django.utils.text import slugify
from django.conf import settings
try:
    from apps.multitenant.models import Tenant
except Exception:
    class Tenant:
        # Fallback minimal pour permettre l'import quand le module est indisponible
        @staticmethod
        def objects():
            class _Q:
                @staticmethod
                def filter(**kwargs):
                    class _F:
                        @staticmethod
                        def exists():
                            return False
                        @staticmethod
                        def first():
                            return None
                    return _F()
            return _Q()
from apps.competitions.models import Club, Federation
from apps.organizations.models import Organization
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

class SubdomainGenerator:
    """Générateur de sous-domaines pour les organisations."""
    
    RESERVED_SUBDOMAINS = {
        'www', 'api', 'admin', 'mail', 'ftp', 'blog', 'shop',
        'app', 'mobile', 'beta', 'test', 'dev', 'staging',
        'cdn', 'media', 'static', 'assets', 'docs', 'help',
        'support', 'status', 'monitoring', 'metrics'
    }
    
    ORG_TYPE_PREFIXES = {
        'federation': 'fed',
        'club': 'club',
        'coach': 'coach',
        'event': 'event'
    }
    
    def __init__(self):
        self.base_domain = getattr(settings, 'TENANT_BASE_DOMAIN', 'martialcomp.com')
    
    def generate_subdomain(self, organization, force_prefix=False):
        """
        Génère un sous-domaine unique pour une organisation.
        
        Args:
            organization: Instance de Organization, Club ou Federation
            force_prefix: Force l'ajout du préfixe de type d'organisation
            
        Returns:
            str: Sous-domaine généré (ex: 'club-karate-paris')
        """
        # Déterminer le nom et le type de l'organisation
        org_name = self._extract_organization_name(organization)
        org_type = self._extract_organization_type(organization)
        
        # Générer le slug de base
        base_slug = self._create_slug(org_name)
        
        # Ajouter le préfixe si nécessaire
        if force_prefix or self._needs_prefix(base_slug):
            prefix = self.ORG_TYPE_PREFIXES.get(org_type, 'org')
            base_slug = f"{prefix}-{base_slug}"
        
        # Assurer l'unicité
        subdomain = self._ensure_uniqueness(base_slug)
        
        # Valider le sous-domaine généré
        if not self._validate_subdomain(subdomain):
            # Fallback avec ID si validation échoue
            subdomain = f"{org_type}-{organization.id}"
        
        logger.info(f"Sous-domaine généré pour {org_name}: {subdomain}")
        return subdomain
    
    def _extract_organization_name(self, organization):
        """Extrait le nom de l'organisation selon son type."""
        if hasattr(organization, 'name'):
            return organization.name
        elif hasattr(organization, 'nom'):
            return organization.nom
        elif hasattr(organization, 'title'):
            return organization.title
        else:
            return f"Organisation {organization.id}"
    
    def _extract_organization_type(self, organization):
        """Détermine le type d'organisation."""
        if isinstance(organization, Club):
            return 'club'
        elif isinstance(organization, Federation):
            return 'federation'
        elif hasattr(organization, 'organization_type'):
            return organization.organization_type
        elif hasattr(organization, 'type'):
            return organization.type
        else:
            # Essayer de déduire du nom du modèle
            model_name = organization._meta.model_name.lower()
            if 'coach' in model_name:
                return 'coach'
            elif 'event' in model_name:
                return 'event'
            else:
                return 'organization'
    
    def _create_slug(self, name):
        """Crée un slug propre Ã  partir du nom."""
        # Normaliser les caractères unicode
        name = unicodedata.normalize('NFKD', str(name))
        
        # Convertir en slug Django standard
        slug = slugify(name)
        
        # Nettoyer et raccourcir si nécessaire
        slug = re.sub(r'-+', '-', slug)  # Ã‰liminer les tirets multiples
        slug = slug.strip('-')  # Enlever les tirets en début/fin
        
        # Limiter la longueur (sous-domaines max 63 caractères)
        if len(slug) > 50:
            words = slug.split('-')
            # Garder les premiers mots jusqu'Ã  50 caractères
            truncated = []
            current_length = 0
            for word in words:
                if current_length + len(word) + 1 <= 50:
                    truncated.append(word)
                    current_length += len(word) + 1
                else:
                    break
            slug = '-'.join(truncated)
        
        return slug
    
    def _needs_prefix(self, slug):
        """Détermine si un préfixe de type est nécessaire."""
        # Ajouter un préfixe si le slug est dans les domaines réservés
        if slug in self.RESERVED_SUBDOMAINS:
            return True
        
        # Ajouter un préfixe si le slug est trop générique
        generic_terms = {
            'martial', 'arts', 'karate', 'judo', 'taekwondo',
            'aikido', 'boxe', 'mma', 'sport', 'dojo', 'association'
        }
        if slug in generic_terms:
            return True
        
        return False
    
    def _ensure_uniqueness(self, base_slug):
        """Assure l'unicité du sous-domaine en ajoutant un suffixe si nécessaire."""
        subdomain = base_slug
        counter = 1
        
        while self._subdomain_exists(subdomain):
            subdomain = f"{base_slug}-{counter}"
            counter += 1
            
            # Ã‰viter les boucles infinies
            if counter > 999:
                # Fallback avec timestamp
                import time
                subdomain = f"{base_slug}-{int(time.time())}"
                break
        
        return subdomain
    
    def _subdomain_exists(self, subdomain):
        """Vérifie si un sous-domaine existe déjÃ ."""
        full_domain = f"{subdomain}.{self.base_domain}"
        return Tenant.objects.filter(domain=full_domain).exists()
    
    def _validate_subdomain(self, subdomain):
        """Valide la conformité RFC du sous-domaine."""
        # Vérifications RFC 1123
        if not subdomain:
            return False
        
        if len(subdomain) > 63:
            return False
        
        if subdomain.startswith('-') or subdomain.endswith('-'):
            return False
        
        # Caractères autorisés : lettres, chiffres, tirets
        if not re.match(r'^[a-z0-9-]+$', subdomain):
            return False
        
        # Ne peut pas Ãªtre entièrement numérique
        if subdomain.isdigit():
            return False
        
        return True
    
    def create_tenant_for_organization(self, organization, subdomain=None):
        """
        Crée un tenant pour une organisation avec son sous-domaine.
        
        Args:
            organization: Instance de l'organisation
            subdomain: Sous-domaine spécifique (optionnel)
            
        Returns:
            Tenant: Instance du tenant créé
        """
        if not subdomain:
            subdomain = self.generate_subdomain(organization)
        
        full_domain = f"{subdomain}.{self.base_domain}"
        
        # Déterminer le plan d'abonnement par défaut selon le type
        org_type = self._extract_organization_type(organization)
        default_plan = self._get_default_plan(org_type)
        
        # Créer le tenant
        tenant = Tenant.objects.create(
            domain=full_domain,
            name=self._extract_organization_name(organization),
            slug=subdomain,
            schema_name=subdomain.replace('-', '_')[:63],
            continent=getattr(organization, 'continent', 'europe_west'),
            country=getattr(organization, 'country', 'FR'),
            timezone=getattr(organization, 'timezone', 'Europe/Paris'),
            currency=getattr(organization, 'currency', 'EUR'),
            language=getattr(organization, 'language', 'fr'),
            subscription_plan=default_plan,
            is_active=True,
            max_users=self._get_plan_limits(default_plan)['max_users'],
            max_disciplines=self._get_plan_limits(default_plan)['max_disciplines'],
            activated_at=timezone.now()
        )
        
        # Associer l'organisation au tenant
        self._link_organization_to_tenant(organization, tenant)
        
        logger.info(f"Tenant créé pour {organization}: {full_domain}")
        return tenant
    
    def _get_default_plan(self, org_type):
        """Détermine le plan par défaut selon le type d'organisation."""
        plan_mapping = {
            'federation': 'champion',  # Plan le plus complet pour les fédérations
            'club': 'masters',         # Plan intermédiaire pour les clubs
            'coach': 'essentials',     # Plan de base pour les coachs
            'event': 'masters'         # Plan intermédiaire pour les événements
        }
        return plan_mapping.get(org_type, 'essentials')
    
    def _get_plan_limits(self, plan):
        """Récupère les limites du plan d'abonnement."""
        from django.conf import settings
        
        plans = getattr(settings, 'SUBSCRIPTION_PLANS', {})
        plan_config = plans.get(plan, plans.get('essentials', {}))
        
        return {
            'max_users': plan_config.get('max_users', 100),
            'max_disciplines': plan_config.get('max_disciplines', 2),
            'features': plan_config.get('features', [])
        }
    
    def _link_organization_to_tenant(self, organization, tenant):
        """Lie une organisation Ã  son tenant."""
        # Si c'est un modèle Organization moderne
        if hasattr(organization, 'tenant'):
            organization.tenant = tenant
            organization.save()
        
        # Si c'est un modèle legacy (Club, Federation)
        elif hasattr(organization, 'organization'):
            if organization.organization:
                organization.organization.tenant = tenant
                organization.organization.save()
        
        # Créer un lien dans la table de métadonnées du tenant si elle existe
        if hasattr(tenant, 'primary_organization_id'):
            tenant.primary_organization_id = organization.id
            tenant.primary_organization_type = organization._meta.label
            tenant.save()

    def get_organization_subdomain_url(self, organization, path=''):
        """
        Génère l'URL complète du sous-domaine pour une organisation.
        
        Args:
            organization: Instance de l'organisation
            path: Chemin relatif (optionnel)
            
        Returns:
            str: URL complète du sous-domaine
        """
        # Si le middleware tenant est désactivé, fallback URL par slug
        from django.conf import settings as dj_settings
        middleware = getattr(dj_settings, 'MIDDLEWARE', [])
        tenant_mw = 'apps.multitenant.middleware.TenantMiddleware'
        if tenant_mw not in middleware:
            # Utiliser SITE_URL (production) ou BASE_URL ou fallback
            base = getattr(dj_settings, 'SITE_URL', None) or getattr(dj_settings, 'BASE_URL', 'http://localhost:8000')
            base = base.rstrip('/')
            url = f"{base}/org/{getattr(organization, 'slug', None) or organization.id}"
            if path:
                path = path.lstrip('/')
                url = f"{url}/{path}"
            return url
        
        # Chercher le tenant existant (mode multi-tenant)
        tenant = self._get_organization_tenant(organization)
        
        if not tenant:
            # Créer un tenant si il n'existe pas
            tenant = self.create_tenant_for_organization(organization)
        
        # Utiliser HTTP en développement, HTTPS en production
        if getattr(settings, 'DEBUG', False):
            protocol = 'http'
        else:
            protocol = 'https' if getattr(settings, 'USE_TLS', True) else 'http'
        
        url = f"{protocol}://{tenant.domain}"
        
        if path:
            path = path.lstrip('/')
            url = f"{url}/{path}"
        
        return url
    
    def _get_organization_tenant(self, organization):
        """Récupère le tenant associé Ã  une organisation."""
        # Vérifier via l'organisation moderne
        if hasattr(organization, 'tenant') and organization.tenant:
            return organization.tenant
        
        # Vérifier via l'organisation legacy
        if hasattr(organization, 'organization') and organization.organization:
            return getattr(organization.organization, 'tenant', None)
        
        # Recherche par métadonnées
        org_id = str(organization.id)
        org_type = organization._meta.label
        
        return Tenant.objects.filter(
            primary_organization_id=org_id,
            primary_organization_type=org_type
        ).first()


# Fonctions utilitaires globales
def generate_organization_subdomain(organization, force_prefix=False):
    """Fonction utilitaire pour générer un sous-domaine."""
    generator = SubdomainGenerator()
    return generator.generate_subdomain(organization, force_prefix)

def create_organization_tenant(organization, subdomain=None):
    """Fonction utilitaire pour créer un tenant."""
    generator = SubdomainGenerator()
    return generator.create_tenant_for_organization(organization, subdomain)

def get_organization_url(organization, path=''):
    """Fonction utilitaire pour obtenir l'URL d'une organisation."""
    generator = SubdomainGenerator()
    return generator.get_organization_subdomain_url(organization, path)

