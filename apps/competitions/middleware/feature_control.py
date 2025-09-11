"""
Middleware pour le contrÃ´le d'accès aux fonctionnalités par abonnement.
"""
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, resolve
from django.core.cache import cache
import re
import logging

from apps.competitions.utils.feature_control import (
    has_feature, 
    get_user_organization, 
    get_organization_subscription,
    log_feature_usage
)
from apps.finances.models.subscription import FeatureFlag

logger = logging.getLogger(__name__)


class FeatureControlMiddleware:
    """
    Middleware qui vérifie l'accès aux fonctionnalités basé sur l'abonnement.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_patterns = self._load_protected_patterns()
    
    def __call__(self, request):
        # Vérifier l'accès aux fonctionnalités avant de traiter la requÃªte
        if self._should_check_access(request):
            access_result = self._check_feature_access(request)
            if access_result is not None:
                return access_result
        
        response = self.get_response(request)
        return response
    
    def _load_protected_patterns(self):
        """
        Charge les patterns d'URLs protégés depuis la base de données.
        Mise en cache pour éviter les requÃªtes répétées.
        """
        cache_key = "feature_control_patterns"
        patterns = cache.get(cache_key)
        
        if patterns is None:
            patterns = {}
            try:
                features = FeatureFlag.objects.filter(is_active=True).exclude(url_patterns='')
                for feature in features:
                    for pattern in feature.get_url_patterns_list():
                        if pattern:
                            patterns[pattern] = feature.name
                cache.set(cache_key, patterns, 600)  # Cache 10 minutes
            except Exception as e:
                logger.error(f"Error loading protected patterns: {e}")
                patterns = {}
        
        return patterns
    
    def _should_check_access(self, request):
        """
        Détermine si la requÃªte doit Ãªtre vérifiée pour le contrÃ´le d'accès.
        """
        # Ne pas vérifier pour les utilisateurs non authentifiés sur certaines pages
        if not request.user.is_authenticated:
            # Permettre l'accès aux pages publiques
            public_paths = [
                '/accounts/', '/admin/', '/set_language/', '/static/', '/media/',
                '/', '/privacy/', '/terms/'
            ]
            return not any(request.path.startswith(path) for path in public_paths)
        
        # Ne pas vérifier pour les superutilisateurs
        if request.user.is_superuser:
            return False
        
        # Ne pas vérifier pour les pages d'administration
        if request.path.startswith('/admin/'):
            return False
        
        return True
    
    def _check_feature_access(self, request):
        """
        Vérifie l'accès aux fonctionnalités pour la requÃªte courante.
        """
        path = request.path
        feature_name = None
        
        # Vérifier si le path correspond Ã  un pattern protégé
        for pattern, feature in self.protected_patterns.items():
            if re.search(pattern, path):
                feature_name = feature
                break
        
        # Si aucune fonctionnalité n'est requise, autoriser l'accès
        if not feature_name:
            return None
        
        # Vérifier l'accès Ã  la fonctionnalité
        if not has_feature(request.user, feature_name):
            # Enregistrer la tentative d'accès
            log_feature_usage(
                request.user,
                feature_name,
                'middleware_check',
                request.path,
                request
            )
            
            # Retourner une réponse appropriée selon le type de requÃªte
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': _('Cette fonctionnalité n\'est pas disponible dans votre package actuel'),
                    'feature': feature_name,
                    'upgrade_required': True
                }, status=403)
            
            # Redirection avec message d'erreur
            messages.warning(
                request,
                _('Accès refusé: Cette fonctionnalité nécessite un abonnement supérieur.')
            )
            
            # Rediriger vers la page de mise Ã  niveau ou le dashboard
            try:
                return HttpResponseRedirect(reverse('upgrade_required'))
            except:
                return HttpResponseRedirect('/competitions/dashboard/')
        
        # Enregistrer l'utilisation autorisée
        log_feature_usage(
            request.user,
            feature_name,
            'middleware_authorized',
            request.path,
            request
        )
        
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Vérification spécifique aux vues.
        """
        # Récupérer le nom de la vue
        view_name = getattr(view_func, '__name__', str(view_func))
        
        # Vérifier si la vue a des exigences spécifiques
        if hasattr(view_func, 'required_feature'):
            feature_name = view_func.required_feature
            if not has_feature(request.user, feature_name):
                messages.warning(
                    request,
                    _('Cette fonctionnalité n\'est pas disponible dans votre package actuel.')
                )
                return HttpResponseRedirect('/competitions/dashboard/')
        
        return None


class SubscriptionStatusMiddleware:
    """
    Middleware pour vérifier le statut de l'abonnement et les limites d'utilisation.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Vérifier le statut de l'abonnement pour les utilisateurs authentifiés
        if request.user.is_authenticated and not request.user.is_superuser:
            self._check_subscription_status(request)
        
        response = self.get_response(request)
        return response
    
    def _check_subscription_status(self, request):
        """
        Vérifie le statut de l'abonnement et ajoute des messages d'avertissement si nécessaire.
        """
        organization = get_user_organization(request.user)
        if not organization:
            return
        
        subscription = get_organization_subscription(organization)
        if not subscription:
            return
        
        # Vérifier si l'abonnement est expiré
        if not subscription.is_active:
            # Ã‰viter de spammer les messages sur chaque requÃªte
            session_key = f"subscription_warning_{organization.id}"
            if not request.session.get(session_key):
                if subscription.status == 'expired':
                    messages.error(
                        request,
                        _('Votre abonnement a expiré. Certaines fonctionnalités sont désactivées.')
                    )
                elif subscription.status == 'suspended':
                    messages.warning(
                        request,
                        _('Votre abonnement est suspendu. Contactez le support.')
                    )
                request.session[session_key] = True
        
        # Vérifier les limites d'utilisation
        elif subscription.is_trial:
            session_key = f"trial_warning_{organization.id}"
            if not request.session.get(session_key):
                from django.utils import timezone
                remaining_days = (subscription.trial_end_date - timezone.now()).days
                if remaining_days <= 7:
                    messages.info(
                        request,
                        _('Votre période d\'essai se termine dans {days} jours.').format(
                            days=remaining_days
                        )
                    )
                    request.session[session_key] = True
        
        # Vérifier les dépassements de limites
        limits_exceeded = subscription.check_limits()
        if limits_exceeded:
            session_key = f"limits_warning_{organization.id}"
            if not request.session.get(session_key):
                messages.warning(
                    request,
                    _('Limites dépassées: {limits}. Veuillez mettre Ã  niveau votre abonnement.').format(
                        limits=', '.join(limits_exceeded)
                    )
                )
                request.session[session_key] = True


class FeatureUsageTrackingMiddleware:
    """
    Middleware pour tracker l'utilisation des fonctionnalités Ã  des fins d'analytics.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Tracker l'utilisation après la réponse pour ne pas ralentir la requÃªte
        if (request.user.is_authenticated and 
            not request.user.is_superuser and 
            response.status_code == 200):
            self._track_page_usage(request)
        
        return response
    
    def _track_page_usage(self, request):
        """
        Enregistre l'utilisation de page pour l'analytics.
        """
        try:
            # Résoudre la vue Ã  partir de l'URL
            resolved = resolve(request.path)
            view_name = resolved.view_name
            
            # Chercher s'il y a une fonctionnalité associée Ã  cette vue
            cache_key = f"view_feature_mapping_{view_name}"
            feature_name = cache.get(cache_key)
            
            if feature_name is None:
                try:
                    # Chercher dans les feature flags
                    features = FeatureFlag.objects.filter(
                        is_active=True,
                        view_names__icontains=view_name
                    ).first()
                    
                    if features:
                        feature_name = features.name
                        cache.set(cache_key, feature_name, 3600)  # Cache 1 heure
                    else:
                        cache.set(cache_key, 'none', 3600)
                        return
                except Exception:
                    return
            
            if feature_name and feature_name != 'none':
                log_feature_usage(
                    request.user,
                    feature_name,
                    view_name,
                    request.path,
                    request
                )
                
        except Exception as e:
            logger.debug(f"Error tracking page usage: {e}")


def clear_feature_patterns_cache():
    """
    Utilitaire pour vider le cache des patterns de fonctionnalités.
    """
    cache.delete("feature_control_patterns")

