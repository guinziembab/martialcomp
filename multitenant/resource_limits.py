"""
Système de limites de ressources par plan d'abonnement.
"""
from django.db import models, connection
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.conf import settings
from functools import wraps
import logging

from multitenant.models import Tenant

logger = logging.getLogger('multitenant.resources')


# Définition des limites par plan
RESOURCE_LIMITS = {
    # Plan "Essentials"
    'essentials': {
        # Limites de stockage en octets (1 Go)
        'storage_limit': 1 * 1024 * 1024 * 1024,
        
        # Nombre maximum d'utilisateurs
        'max_users': 5,
        
        # Nombre maximum de pratiquants
        'max_practitioners': 100,
        
        # Nombre maximum de compétitions
        'max_competitions': 3,
        
        # Nombre maximum de catégories
        'max_categories': 15,
        
        # Nombre maximum de clubs
        'max_clubs': 3,
        
        # Nombre maximum d'envois d'emails par mois
        'max_monthly_emails': 1000,
        
        # Nombre maximum de sauvegardes
        'max_backups': 3,
        
        # Taille maximale de fichier upload (MB)
        'max_file_size_mb': 10,
        
        # Sessions concurrentes
        'concurrent_sessions': 5,
        
        # Opérations par minute
        'rate_limit': 60,
        
        # Fonctionnalités disponibles
        'features': [
            'basic_competitions',
            'practitioner_management',
            'basic_reports',
        ],
        
        # Limites spécifiques
        'competition_participants_limit': 50,
        'api_rate_limit': 100,  # Requêtes par heure
        'export_limit': 1000,   # Lignes maximum
        'imports_per_day': 5,
        'custom_fields': 3,
    },
    
    # Plan "Masters"
    'masters': {
        # Limites de stockage (5 Go)
        'storage_limit': 5 * 1024 * 1024 * 1024,
        
        # Nombre maximum d'utilisateurs
        'max_users': 15,
        
        # Nombre maximum de pratiquants
        'max_practitioners': 500,
        
        # Nombre maximum de compétitions
        'max_competitions': 10,
        
        # Nombre maximum de catégories
        'max_categories': 50,
        
        # Nombre maximum de clubs
        'max_clubs': 10,
        
        # Nombre maximum d'envois d'emails par mois
        'max_monthly_emails': 5000,
        
        # Nombre maximum de sauvegardes
        'max_backups': 10,
        
        # Taille maximale de fichier upload (MB)
        'max_file_size_mb': 50,
        
        # Sessions concurrentes
        'concurrent_sessions': 15,
        
        # Opérations par minute
        'rate_limit': 120,
        
        # Fonctionnalités disponibles
        'features': [
            'basic_competitions',
            'advanced_competitions',
            'practitioner_management',
            'grade_management',
            'financial_reports',
            'custom_categories',
            'email_notifications',
            'api_read_access',
        ],
        
        # Limites spécifiques
        'competition_participants_limit': 200,
        'api_rate_limit': 500,   # Requêtes par heure
        'export_limit': 5000,    # Lignes maximum
        'imports_per_day': 20,
        'custom_fields': 10,
    },
    
    # Plan "Champion"
    'champion': {
        # Limites de stockage (20 Go)
        'storage_limit': 20 * 1024 * 1024 * 1024,
        
        # Nombre maximum d'utilisateurs
        'max_users': 50,
        
        # Nombre maximum de pratiquants
        'max_practitioners': 2000,
        
        # Nombre maximum de compétitions
        'max_competitions': 30,
        
        # Nombre maximum de catégories
        'max_categories': 100,
        
        # Nombre maximum de clubs
        'max_clubs': 30,
        
        # Nombre maximum d'envois d'emails par mois
        'max_monthly_emails': 20000,
        
        # Nombre maximum de sauvegardes
        'max_backups': 30,
        
        # Taille maximale de fichier upload (MB)
        'max_file_size_mb': 200,
        
        # Sessions concurrentes
        'concurrent_sessions': 50,
        
        # Opérations par minute
        'rate_limit': 300,
        
        # Fonctionnalités disponibles
        'features': [
            'basic_competitions',
            'advanced_competitions',
            'practitioner_management',
            'grade_management',
            'financial_reports',
            'custom_categories',
            'api_access',
            'white_label',
            'advanced_analytics',
            'multiple_languages',
            'custom_workflows',
            'email_notifications',
            'mobile_app',
            'sms_notifications',
        ],
        
        # Limites spécifiques
        'competition_participants_limit': 1000,
        'api_rate_limit': 2000,  # Requêtes par heure
        'export_limit': None,    # Illimité
        'imports_per_day': None,  # Illimité
        'custom_fields': 50,
    },
    
    # Plan "Enterprise"
    'enterprise': {
        # Limites de stockage (100 Go)
        'storage_limit': 100 * 1024 * 1024 * 1024,
        
        # Nombre maximum d'utilisateurs
        'max_users': None,  # Illimité
        
        # Nombre maximum de pratiquants
        'max_practitioners': None,  # Illimité
        
        # Nombre maximum de compétitions
        'max_competitions': None,  # Illimité
        
        # Nombre maximum de catégories
        'max_categories': None,  # Illimité
        
        # Nombre maximum de clubs
        'max_clubs': None,  # Illimité
        
        # Nombre maximum d'envois d'emails par mois
        'max_monthly_emails': None,  # Illimité
        
        # Nombre maximum de sauvegardes
        'max_backups': None,  # Illimité
        
        # Taille maximale de fichier upload (MB)
        'max_file_size_mb': 1000,
        
        # Sessions concurrentes
        'concurrent_sessions': None,  # Illimité
        
        # Opérations par minute
        'rate_limit': 1000,
        
        # Fonctionnalités disponibles
        'features': [
            'basic_competitions',
            'advanced_competitions',
            'practitioner_management',
            'grade_management',
            'financial_reports',
            'custom_categories',
            'api_access',
            'white_label',
            'advanced_analytics',
            'multiple_languages',
            'custom_workflows',
            'email_notifications',
            'mobile_app',
            'sms_notifications',
            'priority_support',
            'custom_integrations',
            'sla_guarantee',
            'dedicated_server',
        ],
        
        # Limites spécifiques
        'competition_participants_limit': None,  # Illimité
        'api_rate_limit': 10000,  # Requêtes par heure
        'export_limit': None,    # Illimité
        'imports_per_day': None,  # Illimité
        'custom_fields': None,  # Illimité
    }
}


class ResourceUsageTracker:
    """
    Suivi de l'utilisation des ressources par un tenant.
    """
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.limits = RESOURCE_LIMITS.get(
            tenant.subscription_plan,
            RESOURCE_LIMITS['essentials']  # Plan par défaut
        )
        # Gérer les limites custom depuis metadata
        if tenant.subscription_plan == 'custom' and 'custom_limits' in tenant.metadata:
            self.limits = tenant.metadata['custom_limits']
    
    def get_storage_usage(self):
        """
        Mesure l'utilisation actuelle du stockage.
        """
        # Méthode 1: estimation via la taille des fichiers media
        import os
        
        # Chemin des uploads du tenant
        tenant_media_path = os.path.join(settings.MEDIA_ROOT, 'tenants', self.tenant.schema_name)
        
        # Initialiser le compteur
        total_size = 0
        
        # Parcourir récursivement le répertoire
        if os.path.exists(tenant_media_path):
            for dirpath, dirnames, filenames in os.walk(tenant_media_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(file_path)
        
        # Méthode 2: taille approximative de la base de données
        # Cette méthode est approximative et peut varier selon le SGBD
        with connection.cursor() as cursor:
            # Pour PostgreSQL - taille approximative du schéma
            cursor.execute(f"""
                SELECT pg_total_relation_size(c.oid)
                FROM pg_class c
                LEFT JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = %s
            """, [self.tenant.schema_name])
            
            db_sizes = cursor.fetchall()
            db_size = sum(size[0] for size in db_sizes) if db_sizes else 0
        
        # Taille totale: fichiers + base de données
        return total_size + db_size
    
    def get_user_count(self):
        """
        Compte le nombre d'utilisateurs.
        """
        from competitions.models import FederationUser as User
        
        # Méthode simplifiée en utilisant l'ORM Django
        return User.objects.filter(
            clubs__federation__tenant_profile__tenant=self.tenant
        ).distinct().count()
    
    def get_practitioner_count(self):
        """
        Compte le nombre de pratiquants.
        """
        from competitions.models import Practitioner
        
        return Practitioner.objects.filter(
            club__federation__tenant_profile__tenant=self.tenant
        ).count()
    
    def get_competition_count(self):
        """
        Compte le nombre de compétitions.
        """
        from competitions.models import Competition
        
        return Competition.objects.filter(
            federation__tenant_profile__tenant=self.tenant
        ).count()
    
    def get_category_count(self):
        """
        Compte le nombre de catégories.
        """
        from competitions.models import CompetitionCategory
        
        return CompetitionCategory.objects.filter(
            discipline__federation__tenant_profile__tenant=self.tenant
        ).count()
    
    def get_club_count(self):
        """
        Compte le nombre de clubs.
        """
        from competitions.models import Club
        
        return Club.objects.filter(
            federations__tenant_profile__tenant=self.tenant
        ).distinct().count()
    
    def get_monthly_emails_count(self):
        """
        Compte le nombre d'emails envoyés ce mois-ci.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Récupérer du cache ou de la BD selon votre implémentation
        cache_key = f"{self.tenant.id}_monthly_emails_{timezone.now().strftime('%Y%m')}"
        return cache.get(cache_key, 0)
    
    def get_backup_count(self):
        """
        Compte le nombre de sauvegardes.
        """
        # À implémenter selon votre système de sauvegarde
        cache_key = f"{self.tenant.id}_backup_count"
        return cache.get(cache_key, 0)
    
    def get_imports_today(self):
        """
        Compte le nombre d'imports effectués aujourd'hui.
        """
        cache_key = f"{self.tenant.id}_imports_{timezone.now().strftime('%Y%m%d')}"
        return cache.get(cache_key, 0)
    
    def get_custom_fields_count(self):
        """
        Compte le nombre de champs personnalisés.
        """
        # À implémenter selon votre système de champs personnalisés
        return 0
    
    def get_resource_usage(self):
        """
        Obtient l'utilisation actuelle de toutes les ressources.
        """
        # Utiliser le cache pour éviter des calculs fréquents
        cache_key = f'tenant_resource_usage_{self.tenant.id}'
        cached_usage = cache.get(cache_key)
        
        if cached_usage:
            return cached_usage
        
        # Calculer l'utilisation actuelle
        usage = {
            'storage_usage': self.get_storage_usage(),
            'user_count': self.get_user_count(),
            'practitioner_count': self.get_practitioner_count(),
            'competition_count': self.get_competition_count(),
            'category_count': self.get_category_count(),
            'club_count': self.get_club_count(),
            'monthly_emails_count': self.get_monthly_emails_count(),
            'backup_count': self.get_backup_count(),
            'imports_today': self.get_imports_today(),
            'custom_fields_count': self.get_custom_fields_count(),
        }
        
        # Calculer les pourcentages d'utilisation
        metrics = [
            ('storage', 'storage_usage', 'storage_limit'),
            ('user', 'user_count', 'max_users'),
            ('practitioner', 'practitioner_count', 'max_practitioners'),
            ('competition', 'competition_count', 'max_competitions'),
            ('category', 'category_count', 'max_categories'),
            ('club', 'club_count', 'max_clubs'),
            ('monthly_emails', 'monthly_emails_count', 'max_monthly_emails'),
            ('backup', 'backup_count', 'max_backups'),
            ('custom_fields', 'custom_fields_count', 'custom_fields'),
        ]
        
        for metric_name, usage_key, limit_key in metrics:
            limit_value = self.limits.get(limit_key)
            if limit_value is None or limit_value == -1:
                usage[f'{metric_name}_percentage'] = 0
                usage[f'{metric_name}_unlimited'] = True
            else:
                usage[f'{metric_name}_percentage'] = min(
                    100,
                    (usage[usage_key] / limit_value) * 100
                    if limit_value > 0 else 100
                )
                usage[f'{metric_name}_unlimited'] = False
        
        # Ajouter les limites absolues
        usage['limits'] = self.limits
        
        # Mettre en cache pour 5 minutes
        cache.set(cache_key, usage, 300)
        
        return usage
    
    def check_limits(self, resource_type=None):
        """
        Vérifie si les limites sont atteintes.
        """
        usage = self.get_resource_usage()
        limits_reached = {}
        
        resource_mappings = {
            'storage': ('storage_usage', 'storage_limit'),
            'users': ('user_count', 'max_users'),
            'practitioners': ('practitioner_count', 'max_practitioners'),
            'competitions': ('competition_count', 'max_competitions'),
            'categories': ('category_count', 'max_categories'),
            'clubs': ('club_count', 'max_clubs'),
            'monthly_emails': ('monthly_emails_count', 'max_monthly_emails'),
            'backups': ('backup_count', 'max_backups'),
            'imports': ('imports_today', 'imports_per_day'),
            'custom_fields': ('custom_fields_count', 'custom_fields'),
        }
        
        for resource, (usage_key, limit_key) in resource_mappings.items():
            if resource_type == resource or resource_type is None:
                limit_value = self.limits.get(limit_key)
                if limit_value is not None and limit_value != -1:
                    if usage[usage_key] >= limit_value:
                        limits_reached[resource] = True
        
        return limits_reached
    
    def can_add_resource(self, resource_type):
        """
        Vérifie si une ressource peut être ajoutée.
        """
        limits_reached = self.check_limits(resource_type)
        return len(limits_reached) == 0
    
    def has_feature(self, feature_code):
        """
        Vérifie si une fonctionnalité est disponible dans le plan.
        """
        return feature_code in self.limits['features']


class RateLimiter:
    """
    Limiteur de taux pour les opérations.
    """
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.limits = RESOURCE_LIMITS.get(
            tenant.subscription_plan,
            RESOURCE_LIMITS['essentials']
        )
    
    def get_key(self, operation_type):
        """
        Génère une clé de cache pour le suivi des taux.
        """
        return f'rate_limit_{self.tenant.id}_{operation_type}'
    
    def increment(self, operation_type, count=1):
        """
        Incrémente le compteur d'opérations.
        """
        key = self.get_key(operation_type)
        
        # Incrémenter ou initialiser le compteur
        if cache.get(key) is None:
            cache.set(key, count, 60)  # 1 minute
        else:
            cache.incr(key, count)
    
    def check_rate_limit(self, operation_type):
        """
        Vérifie si la limite de taux est atteinte.
        """
        key = self.get_key(operation_type)
        count = cache.get(key) or 0
        
        if operation_type == 'api':
            limit = self.limits['api_rate_limit'] / 60  # Par minute
        else:
            limit = self.limits['rate_limit']
        
        return count < limit
    
    def get_remaining(self, operation_type):
        """
        Obtient le nombre d'opérations restantes.
        """
        key = self.get_key(operation_type)
        count = cache.get(key) or 0
        
        if operation_type == 'api':
            limit = self.limits['api_rate_limit'] / 60  # Par minute
        else:
            limit = self.limits['rate_limit']
        
        return max(0, limit - count)


# Décorateurs et middlewares pour vérifier les limites

def check_resource_limit(resource_type):
    """
    Décorateur pour vérifier les limites de ressources.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si la requête a un tenant
            if not hasattr(request, 'tenant') or not request.tenant:
                return view_func(request, *args, **kwargs)
            
            # Créer un tracker pour ce tenant
            tracker = ResourceUsageTracker(request.tenant)
            
            # Vérifier si la limite est atteinte
            if not tracker.can_add_resource(resource_type):
                error_message = _(
                    "Vous avez atteint la limite de {resource_type} pour votre plan."
                ).format(resource_type=resource_type)
                
                # Journaliser l'événement
                logger.warning(
                    f"Limite de ressources atteinte: {resource_type} "
                    f"pour le tenant {request.tenant.name}"
                )
                
                # Rediriger vers une page d'erreur ou de mise à niveau
                from django.shortcuts import redirect
                return redirect('multitenant:upgrade_plan')
            
            # La limite n'est pas atteinte, continuer
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator


def check_feature_access(feature_code):
    """
    Décorateur pour vérifier l'accès aux fonctionnalités.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si la requête a un tenant
            if not hasattr(request, 'tenant') or not request.tenant:
                return view_func(request, *args, **kwargs)
            
            # Créer un tracker pour ce tenant
            tracker = ResourceUsageTracker(request.tenant)
            
            # Vérifier si la fonctionnalité est disponible
            if not tracker.has_feature(feature_code):
                error_message = _(
                    "La fonctionnalité {feature} n'est pas disponible dans votre plan."
                ).format(feature=feature_code)
                
                # Journaliser l'événement
                logger.warning(
                    f"Accès à une fonctionnalité non disponible: {feature_code} "
                    f"pour le tenant {request.tenant.name}"
                )
                
                # Rediriger vers une page d'erreur ou de mise à niveau
                from django.shortcuts import redirect
                return redirect('multitenant:upgrade_plan')
            
            # La fonctionnalité est disponible, continuer
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    return decorator


def check_rate_limit(operation_type='default'):
    """
    Décorateur pour vérifier les limites de taux.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si la requête a un tenant
            if not hasattr(request, 'tenant') or not request.tenant:
                return view_func(request, *args, **kwargs)
            
            # Créer un limiteur de taux pour ce tenant
            rate_limiter = RateLimiter(request.tenant)
            
            # Vérifier si la limite de taux est atteinte
            if not rate_limiter.check_rate_limit(operation_type):
                error_message = _(
                    "Vous avez atteint la limite de requêtes pour votre plan. "
                    "Veuillez réessayer dans une minute."
                )
                
                # Journaliser l'événement
                logger.warning(
                    f"Limite de taux atteinte: {operation_type} "
                    f"pour le tenant {request.tenant.name}"
                )
                
                # Réponse 429 Too Many Requests
                from django.http import HttpResponse
                response = HttpResponse(error_message, status=429)
                
                # Headers pour indiquer quand réessayer
                response['Retry-After'] = '60'  # En secondes
                
                return response
            
            # Incrémenter le compteur
            rate_limiter.increment(operation_type)
            
            # Ajouter le header X-RateLimit-Remaining
            response = view_func(request, *args, **kwargs)
            response['X-RateLimit-Remaining'] = str(
                rate_limiter.get_remaining(operation_type)
            )
            
            return response
        
        return _wrapped_view
    
    return decorator


# Middleware pour initialiser le tracker de ressources
class ResourceTrackerMiddleware:
    """
    Middleware qui ajoute un tracker de ressources à la requête.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ajouter le tracker de ressources si un tenant est présent
        if hasattr(request, 'tenant') and request.tenant:
            request.resource_tracker = SimpleLazyObject(
                lambda: ResourceUsageTracker(request.tenant)
            )
            
            request.rate_limiter = SimpleLazyObject(
                lambda: RateLimiter(request.tenant)
            )
        
        response = self.get_response(request)
        return response


class ResourceQuotaManager:
    """Gestionnaire de quotas de ressources pour enforcement des limites."""
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.tracker = ResourceUsageTracker(tenant)
    
    def consume_quota(self, resource_type, amount=1):
        """
        Consomme un quota de ressource.
        """
        # Vérifier si on peut consommer
        if not self.can_consume(resource_type, amount):
            raise QuotaExceededError(f"Quota dépassé pour {resource_type}")
        
        # Mettre à jour le compteur
        cache_key = f"{self.tenant.id}_{resource_type}_consumed"
        current = cache.get(cache_key, 0)
        
        # Durée du cache selon le type de ressource
        if resource_type == 'monthly_emails':
            ttl = 30 * 24 * 3600  # 30 jours
        elif resource_type == 'imports':
            ttl = 24 * 3600  # 1 jour
        else:
            ttl = 3600  # 1 heure par défaut
        
        cache.set(cache_key, current + amount, ttl)
        
        # Journaliser l'utilisation
        logger.info(f"Quota consommé: {amount} {resource_type} pour tenant {self.tenant.name}")
    
    def can_consume(self, resource_type, amount=1):
        """
        Vérifie si on peut consommer un quota.
        """
        usage = self.tracker.get_resource_usage()
        
        # Mapping des types de ressources vers les clés de limite
        limit_mappings = {
            'monthly_emails': 'max_monthly_emails',
            'imports': 'imports_per_day',
            'file_size': 'max_file_size_mb',
            'api_calls': 'api_rate_limit',
        }
        
        limit_key = limit_mappings.get(resource_type)
        if not limit_key:
            return True
        
        limit_value = self.tracker.limits.get(limit_key)
        if limit_value is None or limit_value == -1:
            return True
        
        current_usage = usage.get(f"{resource_type}_count", 0)
        return (current_usage + amount) <= limit_value
    
    def get_remaining_quota(self, resource_type):
        """
        Obtient le quota restant pour une ressource.
        """
        usage = self.tracker.get_resource_usage()
        
        limit_mappings = {
            'monthly_emails': ('monthly_emails_count', 'max_monthly_emails'),
            'imports': ('imports_today', 'imports_per_day'),
            'competitions': ('competition_count', 'max_competitions'),
            'practitioners': ('practitioner_count', 'max_practitioners'),
        }
        
        if resource_type not in limit_mappings:
            return None
        
        usage_key, limit_key = limit_mappings[resource_type]
        limit_value = self.tracker.limits.get(limit_key)
        
        if limit_value is None or limit_value == -1:
            return float('inf')
        
        current_usage = usage.get(usage_key, 0)
        return max(0, limit_value - current_usage)


class QuotaExceededError(Exception):
    """Exception levée quand un quota est dépassé."""
    pass


class ResourceMonitor:
    """Moniteur d'alertes pour les ressources."""
    
    def __init__(self, tenant):
        self.tenant = tenant
        self.tracker = ResourceUsageTracker(tenant)
        
        # Seuils d'alerte (% d'utilisation)
        self.warning_threshold = 80
        self.critical_threshold = 95
    
    def check_alerts(self):
        """
        Vérifie les niveaux d'utilisation et génère des alertes.
        """
        usage = self.tracker.get_resource_usage()
        alerts = []
        
        # Vérifier chaque métrique
        metrics = [
            ('storage', 'Storage'),
            ('user', 'Users'),
            ('practitioner', 'Practitioners'),
            ('competition', 'Competitions'),
            ('category', 'Categories'),
            ('club', 'Clubs'),
            ('monthly_emails', 'Monthly Emails'),
        ]
        
        for metric_key, metric_name in metrics:
            percentage_key = f"{metric_key}_percentage"
            if percentage_key in usage:
                percentage = usage[percentage_key]
                
                if percentage >= self.critical_threshold:
                    alerts.append({
                        'level': 'critical',
                        'metric': metric_name,
                        'percentage': percentage,
                        'message': f"{metric_name} at {percentage:.1f}% capacity"
                    })
                elif percentage >= self.warning_threshold:
                    alerts.append({
                        'level': 'warning',
                        'metric': metric_name,
                        'percentage': percentage,
                        'message': f"{metric_name} at {percentage:.1f}% capacity"
                    })
        
        return alerts
    
    def send_alert_notifications(self, alerts):
        """
        Envoie des notifications pour les alertes.
        """
        if not alerts:
            return
        
        # À implémenter: envoi d'emails, notifications dans l'interface, etc.
        from django.core.mail import send_mail
        from django.conf import settings
        
        critical_alerts = [a for a in alerts if a['level'] == 'critical']
        warning_alerts = [a for a in alerts if a['level'] == 'warning']
        
        if critical_alerts:
            subject = f"[CRITICAL] Resource limits for {self.tenant.name}"
            message = "Critical resource limits reached:\n\n"
            for alert in critical_alerts:
                message += f"- {alert['message']}\n"
            
            # Envoyer à l'admin du tenant
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.tenant.admin_email])
            
            logger.critical(f"Critical resource alerts for tenant {self.tenant.name}: {critical_alerts}")
        
        if warning_alerts:
            logger.warning(f"Warning resource alerts for tenant {self.tenant.name}: {warning_alerts}")


# Fonctions utilitaires
def get_resource_summary_for_tenant(tenant):
    """
    Obtient un résumé complet de l'utilisation des ressources pour un tenant.
    """
    tracker = ResourceUsageTracker(tenant)
    usage = tracker.get_resource_usage()
    
    # Ajouter les alertes
    monitor = ResourceMonitor(tenant)
    alerts = monitor.check_alerts()
    
    # Ajouter les quotas
    quota_manager = ResourceQuotaManager(tenant)
    quotas = {}
    for resource_type in ['monthly_emails', 'imports', 'competitions', 'practitioners']:
        quotas[resource_type] = quota_manager.get_remaining_quota(resource_type)
    
    return {
        'tenant': tenant.name,
        'plan': tenant.subscription_plan,
        'usage': usage,
        'alerts': alerts,
        'quotas': quotas,
        'timestamp': timezone.now(),
    }