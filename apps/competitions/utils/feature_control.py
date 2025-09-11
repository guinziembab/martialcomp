"""
Utilitaires pour le contrÃ´le des fonctionnalités par abonnement.
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.cache import cache
from functools import wraps
import logging

from apps.finances.models.subscription import FeatureFlag, OrganizationSubscription, FeatureUsageLog
from apps.competitions.models import Club

logger = logging.getLogger(__name__)


def get_user_organization(user):
    """
    Récupère l'organisation associée Ã  un utilisateur.
    """
    if not user.is_authenticated:
        return None
    
    # Vérifier via le profil utilisateur
    profile = getattr(user, 'profile', None)
    if profile and profile.organization:
        return profile.organization
    
    # Vérifier via les clubs administrés
    administered_clubs = user.get_administered_clubs()
    if administered_clubs.exists():
        return administered_clubs.first()
    
    # Vérifier via les fédérations administrées
    from apps.competitions.models import Federation
    federations = user.get_administered_federations()
    if federations.exists():
        federation = federations.first()
        # Retourner le premier club de la fédération
        if federation.clubs.exists():
            return federation.clubs.first()
    
    return None


def get_organization_subscription(organization):
    """
    Récupère l'abonnement d'une organisation avec mise en cache.
    """
    if not organization:
        return None
    
    cache_key = f"org_subscription_{organization.id}"
    subscription = cache.get(cache_key)
    
    if subscription is None:
        try:
            subscription = OrganizationSubscription.objects.select_related(
                'subscription_tier'
            ).get(organization=organization)
            cache.set(cache_key, subscription, 300)  # Cache 5 minutes
        except OrganizationSubscription.DoesNotExist:
            # Créer un abonnement par défaut en mode essai
            from apps.finances.models.subscription import SubscriptionTier
            from django.utils import timezone
            from datetime import timedelta
            
            try:
                tier = SubscriptionTier.objects.get(name='dojo_essentials')
                subscription = OrganizationSubscription.objects.create(
                    organization=organization,
                    subscription_tier=tier,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=30),
                    trial_end_date=timezone.now() + timedelta(days=30),
                    status='trial'
                )
                cache.set(cache_key, subscription, 300)
            except SubscriptionTier.DoesNotExist:
                logger.error("Aucun tier d'abonnement par défaut trouvé")
                return None
    
    return subscription


def has_feature(user, feature_name):
    """
    Vérifie si un utilisateur a accès Ã  une fonctionnalité.
    """
    organization = get_user_organization(user)
    if not organization:
        return False
    
    subscription = get_organization_subscription(organization)
    if not subscription:
        return False
    
    return subscription.has_feature(feature_name)


def log_feature_usage(user, feature_name, view_name, url_path, request=None):
    """
    Enregistre l'utilisation d'une fonctionnalité.
    """
    try:
        organization = get_user_organization(user)
        if not organization:
            return
        
        feature = FeatureFlag.objects.get(name=feature_name, is_active=True)
        
        # Préparer les données du log
        log_data = {
            'organization': organization,
            'user': user,
            'feature_flag': feature,
            'view_name': view_name,
            'url_path': url_path,
        }
        
        if request:
            log_data.update({
                'session_key': request.session.session_key,
                'ip_address': request.META.get('REMOTE_ADDR'),
            })
        
        FeatureUsageLog.objects.create(**log_data)
        
    except FeatureFlag.DoesNotExist:
        logger.warning(f"Feature flag '{feature_name}' not found")
    except Exception as e:
        logger.error(f"Error logging feature usage: {e}")


def requires_feature(feature_name, redirect_url='upgrade_required', ajax_response=False):
    """
    Décorateur pour vérifier l'accès Ã  une fonctionnalité.
    
    Args:
        feature_name: Nom de la fonctionnalité requise
        redirect_url: URL de redirection si accès refusé
        ajax_response: Si True, retourne une réponse JSON pour les requÃªtes AJAX
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if ajax_response and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': _('Authentification requise'),
                        'redirect': '/accounts/login/'
                    }, status=401)
                return redirect('account_login')
            
            if not has_feature(request.user, feature_name):
                # Enregistrer la tentative d'accès
                log_feature_usage(
                    request.user, 
                    feature_name, 
                    view_func.__name__, 
                    request.path,
                    request
                )
                
                if ajax_response and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': _('Cette fonctionnalité n\'est pas disponible dans votre package actuel'),
                        'feature': feature_name,
                        'upgrade_required': True
                    }, status=403)
                
                messages.warning(
                    request, 
                    _('Cette fonctionnalité n\'est pas disponible dans votre package actuel. '
                      'Veuillez mettre Ã  niveau votre abonnement.')
                )
                return redirect(redirect_url)
            
            # Enregistrer l'utilisation autorisée
            log_feature_usage(
                request.user, 
                feature_name, 
                view_func.__name__, 
                request.path,
                request
            )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def requires_tier(tier_name, redirect_url='upgrade_required'):
    """
    Décorateur pour vérifier le niveau d'abonnement minimum requis.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            organization = get_user_organization(request.user)
            if not organization:
                messages.error(request, _('Aucune organisation associée'))
                return redirect('dashboard')
            
            subscription = get_organization_subscription(organization)
            if not subscription or subscription.subscription_tier.name != tier_name:
                messages.warning(
                    request,
                    _('Cette fonctionnalité nécessite le package {tier}').format(tier=tier_name)
                )
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def check_usage_limits(organization, limit_type):
    """
    Vérifie si une organisation respecte ses limites d'utilisation.
    
    Args:
        organization: Instance de Club/Organization
        limit_type: Type de limite ('members', 'disciplines', 'clubs', 'storage')
    
    Returns:
        dict: {'allowed': bool, 'current': int, 'limit': int, 'remaining': int}
    """
    subscription = get_organization_subscription(organization)
    if not subscription:
        return {'allowed': False, 'current': 0, 'limit': 0, 'remaining': 0}
    
    # Mettre Ã  jour les compteurs
    subscription.update_usage_counters()
    
    limits_map = {
        'members': (subscription.current_members_count, subscription.subscription_tier.max_members),
        'disciplines': (subscription.current_disciplines_count, subscription.subscription_tier.max_disciplines),
        'clubs': (subscription.current_clubs_count, subscription.subscription_tier.max_clubs),
        'storage': (subscription.current_storage_mb, subscription.subscription_tier.max_storage_mb),
    }
    
    if limit_type not in limits_map:
        return {'allowed': False, 'current': 0, 'limit': 0, 'remaining': 0}
    
    current, limit = limits_map[limit_type]
    
    return {
        'allowed': current < limit,
        'current': current,
        'limit': limit,
        'remaining': max(0, limit - current)
    }


def requires_usage_limit(limit_type, error_message=None):
    """
    Décorateur pour vérifier les limites d'utilisation avant une action.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            
            organization = get_user_organization(request.user)
            if not organization:
                messages.error(request, _('Aucune organisation associée'))
                return redirect('dashboard')
            
            limit_check = check_usage_limits(organization, limit_type)
            if not limit_check['allowed']:
                default_message = _(
                    'Limite atteinte pour {limit_type}: {current}/{limit}. '
                    'Veuillez mettre Ã  niveau votre abonnement.'
                ).format(
                    limit_type=limit_type,
                    current=limit_check['current'],
                    limit=limit_check['limit']
                )
                
                messages.warning(request, error_message or default_message)
                return redirect('upgrade_required')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class FeatureControlMixin:
    """
    Mixin pour les vues basées sur les classes avec contrÃ´le des fonctionnalités.
    """
    required_feature = None
    required_tier = None
    usage_limit_type = None
    
    def dispatch(self, request, *args, **kwargs):
        # Vérifier l'authentification
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        # Vérifier la fonctionnalité requise
        if self.required_feature and not has_feature(request.user, self.required_feature):
            messages.warning(
                request,
                _('Cette fonctionnalité n\'est pas disponible dans votre package actuel.')
            )
            return redirect('upgrade_required')
        
        # Vérifier le tier requis
        if self.required_tier:
            organization = get_user_organization(request.user)
            subscription = get_organization_subscription(organization)
            if not subscription or subscription.subscription_tier.name != self.required_tier:
                messages.warning(
                    request,
                    _('Cette fonctionnalité nécessite le package {tier}').format(tier=self.required_tier)
                )
                return redirect('upgrade_required')
        
        # Vérifier les limites d'utilisation
        if self.usage_limit_type:
            organization = get_user_organization(request.user)
            limit_check = check_usage_limits(organization, self.usage_limit_type)
            if not limit_check['allowed']:
                messages.warning(
                    request,
                    _('Limite atteinte: {current}/{limit}').format(
                        current=limit_check['current'],
                        limit=limit_check['limit']
                    )
                )
                return redirect('upgrade_required')
        
        return super().dispatch(request, *args, **kwargs)


def get_available_features(user):
    """
    Retourne la liste des fonctionnalités disponibles pour un utilisateur.
    """
    organization = get_user_organization(user)
    if not organization:
        return []
    
    subscription = get_organization_subscription(organization)
    if not subscription:
        return []
    
    # Récupérer toutes les fonctionnalités actives du tier
    features = FeatureFlag.objects.filter(
        is_active=True,
        subscription_tiers=subscription.subscription_tier
    ).values_list('name', flat=True)
    
    # Ajouter les fonctionnalités toujours activées
    always_enabled = FeatureFlag.objects.filter(
        is_active=True,
        is_always_enabled=True
    ).values_list('name', flat=True)
    
    return list(set(features) | set(always_enabled))


def clear_subscription_cache(organization_id):
    """
    Vide le cache de l'abonnement d'une organisation.
    """
    cache_key = f"org_subscription_{organization_id}"
    cache.delete(cache_key)

