# -*- coding: utf-8 -*-
"""
Vues de configuration pour Super Admin.
"""

from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse
from django.core.cache import cache
from django.conf import settings
import json

from apps.superadmin.decorators import SuperAdminRequiredMixin
from apps.superadmin.services.audit import AuditService


class ConfigView(SuperAdminRequiredMixin, TemplateView):
    """
    Vue principale de configuration.
    """

    template_name = 'superadmin/config/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Configuration')
        context['active_tab'] = 'config'

        # Configuration actuelle
        context['config_sections'] = [
            {
                'id': 'general',
                'name': _('Général'),
                'icon': 'cog',
                'description': _('Paramètres généraux de la plateforme'),
                'url': reverse('superadmin:config_general'),
            },
            {
                'id': 'features',
                'name': _('Feature Flags'),
                'icon': 'toggle-on',
                'description': _('Activation/désactivation des fonctionnalités'),
                'url': reverse('superadmin:config_features'),
            },
            {
                'id': 'regions',
                'name': _('Régions & Prix'),
                'icon': 'globe',
                'description': _('Configuration des régions et tarification'),
                'url': reverse('superadmin:config_regions'),
            },
            {
                'id': 'email',
                'name': _('Email'),
                'icon': 'envelope',
                'description': _('Configuration SMTP et templates'),
                'url': reverse('superadmin:config_email'),
            },
            {
                'id': 'security',
                'name': _('Sécurité'),
                'icon': 'shield-alt',
                'description': _('Paramètres de sécurité et accès'),
                'url': reverse('superadmin:config_security'),
            },
        ]

        return context


class GeneralConfigView(SuperAdminRequiredMixin, TemplateView):
    """
    Configuration générale.
    """

    template_name = 'superadmin/config/general.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Configuration Générale')
        context['active_tab'] = 'config'

        # Récupérer la configuration depuis le cache ou les settings
        context['config'] = {
            'site_name': getattr(settings, 'SITE_NAME', 'MartialComp'),
            'site_url': getattr(settings, 'SITE_URL', 'https://martialcomp.com'),
            'admin_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
            'support_email': getattr(settings, 'SUPPORT_EMAIL', ''),
            'debug_mode': settings.DEBUG,
            'timezone': settings.TIME_ZONE,
            'language_code': settings.LANGUAGE_CODE,
            'maintenance_mode': cache.get('maintenance_mode', False),
        }

        return context

    def post(self, request):
        # Sauvegarder la configuration
        config_updates = {
            'site_name': request.POST.get('site_name'),
            'support_email': request.POST.get('support_email'),
        }

        # Log l'action
        AuditService.log_action(
            user=request.user,
            action_type='config_change',
            request=request,
            description=f"Modification configuration générale: {json.dumps(config_updates)}"
        )

        # Stocker dans le cache (en production, utiliser une vraie persistence)
        for key, value in config_updates.items():
            if value:
                cache.set(f'config:{key}', value, timeout=None)

        messages.success(request, _('Configuration mise à jour avec succès.'))
        return redirect(reverse('superadmin:config_general'))


class FeatureFlagsView(SuperAdminRequiredMixin, TemplateView):
    """
    Gestion des feature flags.
    """

    template_name = 'superadmin/config/features.html'

    # Liste des features disponibles
    FEATURES = [
        {
            'id': 'competition_creation',
            'name': _('Création de compétitions'),
            'description': _('Permet aux organisations de créer des compétitions'),
            'category': 'competitions',
        },
        {
            'id': 'advanced_scoring',
            'name': _('Scoring avancé'),
            'description': _('Système de notation avancé avec critères multiples'),
            'category': 'competitions',
        },
        {
            'id': 'real_time_combat',
            'name': _('Combat temps réel'),
            'description': _('Gestion des combats en temps réel avec WebSocket'),
            'category': 'competitions',
        },
        {
            'id': 'mobile_app',
            'name': _('Application mobile'),
            'description': _('Accès via l\'application mobile'),
            'category': 'access',
        },
        {
            'id': 'api_access',
            'name': _('Accès API'),
            'description': _('Accès à l\'API REST pour intégrations'),
            'category': 'access',
        },
        {
            'id': 'export_data',
            'name': _('Export de données'),
            'description': _('Export des données en CSV/Excel'),
            'category': 'data',
        },
        {
            'id': 'ai_recommendations',
            'name': _('Recommandations IA'),
            'description': _('Suggestions basées sur l\'intelligence artificielle'),
            'category': 'premium',
        },
        {
            'id': 'white_label',
            'name': _('Marque blanche'),
            'description': _('Personnalisation complète de l\'interface'),
            'category': 'premium',
        },
        {
            'id': 'priority_support',
            'name': _('Support prioritaire'),
            'description': _('Accès au support prioritaire'),
            'category': 'premium',
        },
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Feature Flags')
        context['active_tab'] = 'config'

        # Récupérer l'état des features
        features = []
        for feature in self.FEATURES:
            feature_data = feature.copy()
            feature_data['enabled'] = cache.get(f'feature:{feature["id"]}', True)
            features.append(feature_data)

        context['features'] = features

        # Grouper par catégorie
        categories = {}
        for feature in features:
            cat = feature['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(feature)

        context['categories'] = {
            'competitions': {'name': _('Compétitions'), 'features': categories.get('competitions', [])},
            'access': {'name': _('Accès'), 'features': categories.get('access', [])},
            'data': {'name': _('Données'), 'features': categories.get('data', [])},
            'premium': {'name': _('Premium'), 'features': categories.get('premium', [])},
        }

        return context

    def post(self, request):
        feature_id = request.POST.get('feature_id')
        enabled = request.POST.get('enabled', 'false').lower() == 'true'

        if feature_id:
            cache.set(f'feature:{feature_id}', enabled, timeout=None)

            AuditService.log_action(
                user=request.user,
                action_type='feature_toggle',
                request=request,
                description=f"Feature {feature_id} {'activée' if enabled else 'désactivée'}"
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'enabled': enabled})

            messages.success(request, _('Feature mise à jour.'))

        return redirect(reverse('superadmin:config_features'))


class RegionPricingView(SuperAdminRequiredMixin, TemplateView):
    """
    Configuration des régions et tarification.
    """

    template_name = 'superadmin/config/regions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Régions & Tarification')
        context['active_tab'] = 'config'

        # Régions configurées
        context['regions'] = cache.get('config:regions', [
            {
                'code': 'EU',
                'name': _('Europe'),
                'currency': 'EUR',
                'price_multiplier': 1.0,
                'tax_rate': 20.0,
                'countries': ['FR', 'DE', 'IT', 'ES', 'BE', 'NL', 'CH', 'AT'],
            },
            {
                'code': 'NA',
                'name': _('Amérique du Nord'),
                'currency': 'USD',
                'price_multiplier': 1.1,
                'tax_rate': 0.0,
                'countries': ['US', 'CA'],
            },
            {
                'code': 'ASIA',
                'name': _('Asie'),
                'currency': 'USD',
                'price_multiplier': 0.8,
                'tax_rate': 0.0,
                'countries': ['JP', 'KR', 'CN', 'TH', 'VN'],
            },
            {
                'code': 'AFRICA',
                'name': _('Afrique'),
                'currency': 'EUR',
                'price_multiplier': 0.6,
                'tax_rate': 0.0,
                'countries': ['SN', 'CI', 'MA', 'TN', 'ZA'],
            },
        ])

        context['currencies'] = ['EUR', 'USD', 'GBP', 'CHF', 'CAD', 'JPY']

        return context

    def post(self, request):
        # Traiter la mise à jour des régions
        action = request.POST.get('action')

        if action == 'update_region':
            region_code = request.POST.get('region_code')
            # Mise à jour de la région...
            messages.success(request, _('Région mise à jour.'))

        elif action == 'add_region':
            # Ajout d'une nouvelle région...
            messages.success(request, _('Région ajoutée.'))

        return redirect(reverse('superadmin:config_regions'))


class EmailConfigView(SuperAdminRequiredMixin, TemplateView):
    """
    Configuration email.
    """

    template_name = 'superadmin/config/email.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Configuration Email')
        context['active_tab'] = 'config'

        # Configuration SMTP
        context['smtp_config'] = {
            'host': getattr(settings, 'EMAIL_HOST', 'localhost'),
            'port': getattr(settings, 'EMAIL_PORT', 587),
            'use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
            'username': getattr(settings, 'EMAIL_HOST_USER', ''),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', ''),
        }

        # Templates email
        context['email_templates'] = [
            {'id': 'welcome', 'name': _('Bienvenue'), 'subject': _('Bienvenue sur MartialComp')},
            {'id': 'password_reset', 'name': _('Réinitialisation mot de passe'), 'subject': _('Réinitialisez votre mot de passe')},
            {'id': 'competition_invite', 'name': _('Invitation compétition'), 'subject': _('Vous êtes invité à une compétition')},
            {'id': 'results_available', 'name': _('Résultats disponibles'), 'subject': _('Les résultats sont disponibles')},
        ]

        return context

    def post(self, request):
        action = request.POST.get('action')

        if action == 'test_email':
            # Envoyer un email de test
            from django.core.mail import send_mail
            try:
                send_mail(
                    subject='Test email MartialComp',
                    message='Ceci est un email de test.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )
                messages.success(request, _('Email de test envoyé avec succès.'))
            except Exception as e:
                messages.error(request, _('Erreur lors de l\'envoi: {}').format(str(e)))

        return redirect(reverse('superadmin:config_email'))


class SecurityConfigView(SuperAdminRequiredMixin, TemplateView):
    """
    Configuration sécurité.
    """

    template_name = 'superadmin/config/security.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Sécurité')
        context['active_tab'] = 'config'

        # Paramètres de sécurité
        context['security_settings'] = {
            'session_timeout': cache.get('security:session_timeout', 3600),
            'max_login_attempts': cache.get('security:max_login_attempts', 5),
            'lockout_duration': cache.get('security:lockout_duration', 900),
            'require_2fa_admin': cache.get('security:require_2fa_admin', False),
            'password_min_length': cache.get('security:password_min_length', 8),
            'password_require_special': cache.get('security:password_require_special', True),
            'allowed_ips': cache.get('security:allowed_ips', []),
            'blocked_ips': cache.get('security:blocked_ips', []),
        }

        # Sessions actives
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        context['active_sessions_count'] = Session.objects.filter(
            expire_date__gt=timezone.now()
        ).count()

        return context

    def post(self, request):
        action = request.POST.get('action')

        if action == 'update_settings':
            # Mise à jour des paramètres
            updates = {
                'session_timeout': int(request.POST.get('session_timeout', 3600)),
                'max_login_attempts': int(request.POST.get('max_login_attempts', 5)),
                'lockout_duration': int(request.POST.get('lockout_duration', 900)),
                'require_2fa_admin': request.POST.get('require_2fa_admin') == 'on',
                'password_min_length': int(request.POST.get('password_min_length', 8)),
                'password_require_special': request.POST.get('password_require_special') == 'on',
            }

            for key, value in updates.items():
                cache.set(f'security:{key}', value, timeout=None)

            AuditService.log_action(
                user=request.user,
                action_type='security_config',
                request=request,
                description=f"Mise à jour sécurité: {json.dumps(updates)}"
            )

            messages.success(request, _('Paramètres de sécurité mis à jour.'))

        elif action == 'clear_sessions':
            # Supprimer toutes les sessions
            from django.contrib.sessions.models import Session
            count = Session.objects.all().delete()[0]

            AuditService.log_action(
                user=request.user,
                action_type='clear_sessions',
                request=request,
                description=f"Suppression de {count} sessions"
            )

            messages.warning(request, _('Toutes les sessions ont été supprimées.'))

        elif action == 'block_ip':
            ip = request.POST.get('ip')
            if ip:
                blocked = cache.get('security:blocked_ips', [])
                if ip not in blocked:
                    blocked.append(ip)
                    cache.set('security:blocked_ips', blocked, timeout=None)
                    messages.success(request, _('IP bloquée: {}').format(ip))

        elif action == 'unblock_ip':
            ip = request.POST.get('ip')
            if ip:
                blocked = cache.get('security:blocked_ips', [])
                if ip in blocked:
                    blocked.remove(ip)
                    cache.set('security:blocked_ips', blocked, timeout=None)
                    messages.success(request, _('IP débloquée: {}').format(ip))

        return redirect(reverse('superadmin:config_security'))
