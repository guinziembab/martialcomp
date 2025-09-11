"""
Signaux automatiques pour la création de sites d'organisations.
Créé automatiquement des tenants, sous-domaines et QR codes.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone

from .models import Organization
from multitenant.models import Tenant
from competitions.utils.subdomain_generator import SubdomainGenerator
from competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Organization)
def create_organization_site(sender, instance, created, **kwargs):
    """
    Signal déclenché lors de la création d'une organisation.
    Crée automatiquement :
    - Tenant multi-tenant
    - Sous-domaine
    - QR codes d'organisation
    """
    if created:
        try:
            # 1. Générer le sous-domaine
            generator = SubdomainGenerator()
            subdomain = generator.generate_subdomain(instance)
            
            # 2. Créer le tenant
            tenant = create_organization_tenant(instance, subdomain)
            
            # 3. Générer les QR codes
            qr_codes = generate_organization_qr_codes(instance, tenant)
            
            logger.info(f"Site créé automatiquement pour {instance.name}: {tenant.domain}")
            logger.info(f"QR codes générés: {list(qr_codes.keys())}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création automatique du site pour {instance.name}: {e}")
            # Ne pas empêcher la création de l'organisation

@receiver(post_save, sender=Organization)
def sync_organization_updates(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les mises à jour d'organisation avec le tenant.
    """
    if not created and hasattr(instance, '_tenant_cache'):
        try:
            # Mettre à jour les informations du tenant si nécessaire
            tenant = getattr(instance, '_tenant_cache', None)
            if tenant:
                # Mettre à jour le nom du tenant si le nom de l'organisation a changé
                if tenant.name != instance.name:
                    tenant.name = instance.name
                    tenant.save()
                    logger.info(f"Tenant mis à jour pour {instance.name}")
                    
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation du tenant pour {instance.name}: {e}")

@receiver(post_delete, sender=Organization)
def cleanup_organization_site(sender, instance, **kwargs):
    """
    Signal déclenché lors de la suppression d'une organisation.
    Nettoie les ressources associées (tenant, QR codes).
    """
    try:
        # Trouver et supprimer le tenant associé
        tenant = find_organization_tenant(instance)
        if tenant:
            # Marquer le tenant comme inactif au lieu de le supprimer
            # pour préserver l'historique
            tenant.is_active = False
            tenant.save()
            logger.info(f"Tenant désactivé pour l'organisation supprimée: {instance.name}")
            
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage pour {instance.name}: {e}")

def create_organization_tenant(organization, subdomain):
    """
    Crée un tenant pour une organisation avec le sous-domaine spécifié.
    
    Args:
        organization: Instance d'Organization
        subdomain: Sous-domaine généré
        
    Returns:
        Tenant: Instance du tenant créé
    """
    try:
        # Vérifier si un tenant existe déjà
        existing_tenant = find_organization_tenant(organization)
        if existing_tenant:
            logger.info(f"Tenant existant trouvé pour {organization.name}: {existing_tenant.domain}")
            return existing_tenant
        
        # Générer le domaine complet
        base_domain = getattr(settings, 'TENANT_BASE_DOMAIN', 'martialcomp.com')
        full_domain = f"{subdomain}.{base_domain}"
        
        # Générer un schema_name unique
        schema_name = subdomain.replace('-', '_')[:63]  # PostgreSQL max 63 chars
        
        # S'assurer de l'unicité du schema_name
        counter = 1
        original_schema = schema_name
        while Tenant.objects.filter(schema_name=schema_name).exists():
            schema_name = f"{original_schema}_{counter}"[:63]
            counter += 1
        
        # Créer le tenant avec les vrais champs du modèle
        tenant_data = {
            'name': organization.name,
            'slug': subdomain,
            'schema_name': schema_name,
            'domain': full_domain,
            'continent': get_continent_for_country(organization.country),
            'country': organization.country or 'FR',
            'timezone': 'Europe/Paris',  # Par défaut pour la France
            'currency': 'EUR',
            'language': 'fr',
            'subscription_plan': get_subscription_plan_for_organization(organization),
            'is_active': True,
            'activated_at': timezone.now()
        }
        
        # Créer le tenant d'abord sans l'owner
        tenant = Tenant.objects.create(**tenant_data)
        
        # Assigner l'owner après création pour éviter les problèmes de routeur
        try:
            if organization.created_by:
                tenant.owner = organization.created_by
                tenant.save()
        except Exception as router_error:
            logger.warning(f"Impossible d'assigner l'owner à cause du routeur DB: {router_error}")
            # Le tenant est créé quand même, juste sans owner
        
        # Créer la relation inverse si nécessaire
        if hasattr(organization, 'tenant'):
            organization.tenant = tenant
            organization.save()
        
        # Cache le tenant pour éviter les requêtes répétées
        organization._tenant_cache = tenant
        
        logger.info(f"Tenant créé avec succès: {full_domain} pour {organization.name}")
        return tenant
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du tenant pour {organization.name}: {e}")
        raise

def generate_organization_qr_codes(organization, tenant):
    """
    Génère un ensemble complet de QR codes pour une organisation.
    
    Args:
        organization: Instance d'Organization
        tenant: Instance du Tenant associé
        
    Returns:
        dict: Dictionnaire des QR codes générés
    """
    try:
        # Utiliser l'utilitaire existant pour générer les QR codes
        qr_codes = generate_organization_qr_codes_set(organization)
        
        # Optionnel : Stocker les références aux QR codes
        # pour permettre la gestion depuis l'interface admin
        store_qr_code_references(organization, qr_codes)
        
        return qr_codes
        
    except Exception as e:
        logger.error(f"Erreur lors de la génération des QR codes pour {organization.name}: {e}")
        return {}

def find_organization_tenant(organization):
    """
    Trouve le tenant associé à une organisation.
    
    Args:
        organization: Instance d'Organization
        
    Returns:
        Tenant ou None: Le tenant trouvé ou None
    """
    try:
        # Chercher par nom d'organisation d'abord
        tenant = Tenant.objects.filter(
            name=organization.name,
            is_active=True
        ).first()
        
        if not tenant:
            # Chercher par slug généré
            generator = SubdomainGenerator()
            expected_subdomain = generator.generate_subdomain(organization)
            tenant = Tenant.objects.filter(
                slug=expected_subdomain,
                is_active=True
            ).first()
        
        return tenant
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du tenant pour {organization.name}: {e}")
        return None

def get_continent_for_country(country_code):
    """
    Détermine le continent basé sur le code pays.
    
    Args:
        country_code: Code pays ISO (ex: 'FR', 'US')
        
    Returns:
        str: Code continent pour le modèle Tenant
    """
    # Mapping simplifié pays -> continent
    continent_mapping = {
        'FR': 'europe_west',
        'DE': 'europe_west', 
        'ES': 'europe_west',
        'IT': 'europe_west',
        'GB': 'europe_west',
        'CH': 'europe_west',
        'BE': 'europe_west',
        'NL': 'europe_west',
        'AT': 'europe_west',
        'PT': 'europe_west',
        'PL': 'europe_east',
        'CZ': 'europe_east',
        'HU': 'europe_east',
        'RO': 'europe_east',
        'US': 'north_america',
        'CA': 'north_america',
        'MX': 'central_america',
        'BR': 'south_america',
        'AR': 'south_america',
        'CL': 'south_america',
        'CN': 'asia_other',
        'JP': 'asia_other',
        'KR': 'asia_other',
        'IN': 'asia_other',
        'TH': 'asia_se',
        'VN': 'asia_se',
        'ID': 'asia_se',
        'MY': 'asia_se',
        'AU': 'oceania',
        'NZ': 'oceania',
        'ZA': 'africa',
        'EG': 'africa',
        'MA': 'africa',
        'AE': 'middle_east',
        'SA': 'middle_east',
    }
    
    return continent_mapping.get(country_code or 'FR', 'europe_west')

def get_subscription_plan_for_organization(organization):
    """
    Détermine le plan d'abonnement basé sur le type d'organisation.
    
    Args:
        organization: Instance d'Organization
        
    Returns:
        str: Nom du plan d'abonnement (selon les choix du modèle Tenant)
    """
    # Mapper les types d'organisation aux plans d'abonnement réels
    # Plans disponibles: 'essentials', 'masters', 'champion', 'trial'
    plan_mapping = {
        'GLOBAL_BODY': 'champion',
        'INTERNATIONAL_FEDERATION': 'champion', 
        'NATIONAL_FEDERATION': 'masters',
        'REGIONAL_BODY': 'masters',
        'CLUB': 'essentials',
        'ACADEMY': 'essentials',
        'OTHER': 'trial'
    }
    
    return plan_mapping.get(organization.organization_type, 'trial')

def store_qr_code_references(organization, qr_codes):
    """
    Stocke les références aux QR codes pour gestion future.
    
    Args:
        organization: Instance d'Organization
        qr_codes: Dictionnaire des QR codes générés
    """
    try:
        # Importer ici pour éviter les imports circulaires
        from competitions.models import OrganizationQRCode
        
        # Stocker chaque QR code
        for qr_type, (url, image_path) in qr_codes.items():
            qr_code, created = OrganizationQRCode.objects.get_or_create(
                organization=organization,
                qr_type=qr_type,
                defaults={
                    'url': url,
                    'image_path': image_path,
                    'is_active': True,
                    'created_at': timezone.now()
                }
            )
            
            if created:
                logger.info(f"QR code {qr_type} stocké pour {organization.name}")
                
    except Exception as e:
        logger.error(f"Erreur lors du stockage des QR codes pour {organization.name}: {e}")

# Signal pour les modèles legacy (Club, Federation)
# Ces signaux assurent la compatibilité avec l'ancien système

@receiver(post_save, sender='competitions.Club')
def sync_club_to_organization(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les clubs legacy avec le système Organization.
    """
    if created:
        try:
            # Vérifier si une organisation correspondante existe déjà
            organization = getattr(instance, 'organization', None)
            if organization:
                # Déclencher la création automatique du site
                create_organization_site(Organization, organization, True, **kwargs)
                logger.info(f"Site créé automatiquement pour le club legacy: {instance.name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation du club legacy {instance.name}: {e}")

@receiver(post_save, sender='competitions.Federation')
def sync_federation_to_organization(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les fédérations legacy avec le système Organization.
    """
    if created:
        try:
            # Vérifier si une organisation correspondante existe déjà
            organization = getattr(instance, 'organization', None)
            if organization:
                # Déclencher la création automatique du site
                create_organization_site(Organization, organization, True, **kwargs)
                logger.info(f"Site créé automatiquement pour la fédération legacy: {instance.name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de la fédération legacy {instance.name}: {e}")