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
try:
    from apps.multitenant.models import Tenant
except Exception:  # ImportError, SyntaxError si module corrompu
    Tenant = None
from apps.competitions.utils.subdomain_generator import SubdomainGenerator
from apps.competitions.utils.qr_generator_enhanced import generate_organization_qr_codes_set
from apps.competitions.models.organization_qr_code import OrganizationQRCode

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Organization)
def create_organization_site_automatic(sender, instance, created, **kwargs):
    """
    Signal automatique pour créer le site web et QR codes lors de la création d'une organisation.
    Crée automatiquement :
    - Tenant multi-tenant
    - Sous-domaine
    - QR codes d'organisation
    - Notifications utilisateur
    """
    if created:
        try:
            # 1. Générer le sous-domaine
            generator = SubdomainGenerator()
            subdomain = generator.generate_subdomain(instance)
            
            # 2. Créer le tenant
            tenant = create_organization_tenant(instance, subdomain) if Tenant else None
            
            # 3. Générer les QR codes
            qr_codes = generate_organization_qr_codes(instance, tenant) if tenant else {}
            
            # 4. Créer les QR codes en base de données
            create_organization_qr_codes_in_db(instance, qr_codes)
            
            # 5. Notifier l'utilisateur
            if tenant:
                notify_organization_created(instance, tenant, qr_codes)
            
            logger.info(f"Site créé automatiquement pour {instance.name}: {tenant.domain}")
            logger.info(f"QR codes générés: {list(qr_codes.keys())}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création automatique du site pour {instance.name}: {e}")
            # Ne pas empÃªcher la création de l'organisation

@receiver(post_save, sender=Organization)
def sync_organization_updates(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les mises Ã  jour d'organisation avec le tenant.
    """
    if not created and hasattr(instance, '_tenant_cache'):
        try:
            # Mettre Ã  jour les informations du tenant si nécessaire
            tenant = getattr(instance, '_tenant_cache', None)
            if tenant:
                # Mettre Ã  jour le nom du tenant si le nom de l'organisation a changé
                if tenant.name != instance.name:
                    tenant.name = instance.name
                    tenant.save()
                    logger.info(f"Tenant mis Ã  jour pour {instance.name}")
                    
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
        # Vérifier si un tenant existe déjÃ 
        if not Tenant:
            return None
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
            logger.warning(f"Impossible d'assigner l'owner Ã  cause du routeur DB: {router_error}")
            # Le tenant est créé quand mÃªme, juste sans owner
        
        # Créer la relation inverse si nécessaire
        if hasattr(organization, 'tenant'):
            organization.tenant = tenant
            organization.save()
        
        # Cache le tenant pour éviter les requÃªtes répétées
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
    Trouve le tenant associé Ã  une organisation.
    
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
        from apps.competitions.models import OrganizationQRCode
        
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

# @receiver(post_save, sender='competitions.Club')
def sync_club_to_organization_disabled(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les clubs legacy avec le système Organization.
    TEMPORAIREMENT DÃ‰SACTIVÃ‰ pour éviter les conflits de clés dupliquées.
    """
    if created:
        try:
            # Vérifier si une organisation correspondante existe déjÃ 
            organization = getattr(instance, 'organization', None)
            if organization:
                # Déclencher la création automatique du site
                create_organization_site(Organization, organization, True, **kwargs)
                logger.info(f"Site créé automatiquement pour le club legacy: {instance.name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation du club legacy {instance.name}: {e}")

# @receiver(post_save, sender='competitions.Federation')
def sync_federation_to_organization_disabled(sender, instance, created, **kwargs):
    """
    Signal pour synchroniser les fédérations legacy avec le système Organization.
    TEMPORAIREMENT DÃ‰SACTIVÃ‰ pour éviter les conflits de clés dupliquées.
    """
    if created:
        try:
            # Vérifier si une organisation correspondante existe déjÃ 
            organization = getattr(instance, 'organization', None)
            if organization:
                # Déclencher la création automatique du site
                create_organization_site_automatic(Organization, organization, True, **kwargs)
                logger.info(f"Site créé automatiquement pour la fédération legacy: {instance.name}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation de la fédération legacy {instance.name}: {e}")

def create_organization_qr_codes_in_db(organization, qr_codes):
    """
    Crée les QR codes en base de données pour une organisation.
    
    Args:
        organization: Instance de l'organisation
        qr_codes: Dictionnaire des QR codes générés
    """
    try:
        created_qr_codes = []
        
        for qr_type, (url, image_path) in qr_codes.items():
            # Déterminer le type d'entité pour lier le QR code
            qr_code_kwargs = {
                'purpose': qr_type,
                'defaults': {
                    'url': url,
                    'qr_image': image_path,
                    'is_active': True,
                    'custom_title': f"QR Code {qr_type.title()} - {organization.name}",
                    'custom_message': f"Scannez pour accéder au {qr_type} de {organization.name}"
                }
            }
            # Lier au bon champ selon le type d'organisation
            model_name = organization._meta.model_name.lower()
            if model_name == 'club':
                qr_code_kwargs['club'] = organization
            elif model_name == 'federation':
                qr_code_kwargs['federation'] = organization
            elif model_name == 'coachprofile':
                qr_code_kwargs['coach_profile'] = organization
            else:
                continue  # Ne pas créer pour les types non supportés

            qr_code, created = OrganizationQRCode.objects.get_or_create(
                **qr_code_kwargs
            )

            if created:
                created_qr_codes.append(qr_code)
                logger.info(f"QR code {qr_type} créé en base pour {organization.name}")
        
        return created_qr_codes
        
    except Exception as e:
        logger.error(f"Erreur lors de la création des QR codes en base pour {organization.name}: {e}")
        return []

def notify_organization_created(organization, tenant, qr_codes):
    """
    Notifie l'utilisateur de la création réussie de l'organisation.
    
    Args:
        organization: Instance de l'organisation
        tenant: Instance du tenant créé
        qr_codes: Dictionnaire des QR codes générés
    """
    try:
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        from django.conf import settings
        
        context = {
            'organization': organization,
            'tenant': tenant,
            'qr_codes': qr_codes,
            'site_url': f"https://{tenant.domain}",
            'admin_url': f"https://{tenant.domain}/admin/"
        }
        
        # Email de notification
        html_message = render_to_string('organizations/emails/organization_created.html', context)
        text_message = render_to_string('organizations/emails/organization_created.txt', context)
        
        if organization.created_by and organization.created_by.email:
            send_mail(
                subject=f"Votre organisation {organization.name} a été créée avec succès!",
                message=text_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[organization.created_by.email],
                fail_silently=True
            )
            
            logger.info(f"Email de notification envoyé pour {organization.name}")
            
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de la notification pour {organization.name}: {e}")

