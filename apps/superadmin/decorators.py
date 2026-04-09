# -*- coding: utf-8 -*-
"""
Décorateurs pour l'application Super Admin.
"""

from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


def superuser_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est un superuser.
    Redirige vers la page de login si non authentifié,
    retourne 403 si authentifié mais non superuser.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Vous devez être connecté pour accéder à cette page."))
            return redirect('account_login')

        if not request.user.is_superuser:
            messages.error(request, _("Accès réservé aux super administrateurs."))
            return HttpResponseForbidden(
                _("Accès refusé. Cette section est réservée aux super administrateurs.")
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def audit_action(action_type):
    """
    Décorateur pour logger automatiquement les actions admin.

    Usage:
        @audit_action('restart_service')
        def restart_gunicorn(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from apps.superadmin.services.audit import AuditService

            # Exécuter la vue
            response = view_func(request, *args, **kwargs)

            # Logger l'action si succès (status code 2xx)
            if hasattr(response, 'status_code') and 200 <= response.status_code < 300:
                AuditService.log_action(
                    user=request.user,
                    action_type=action_type,
                    request=request,
                    status='completed'
                )

            return response

        return _wrapped_view
    return decorator


class SuperAdminRequiredMixin:
    """
    Mixin pour les vues class-based qui requièrent un superuser.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, _("Vous devez être connecté pour accéder à cette page."))
            return redirect('account_login')

        if not request.user.is_superuser:
            messages.error(request, _("Accès réservé aux super administrateurs."))
            return HttpResponseForbidden(
                _("Accès refusé. Cette section est réservée aux super administrateurs.")
            )

        return super().dispatch(request, *args, **kwargs)


class CloudflareAjaxMixin:
    """
    Mixin pour les vues AJAX qui ajoute les headers nécessaires
    pour bypasser le cache Cloudflare et assurer la compatibilité.
    """

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)

        # Ajouter les headers pour bypasser le cache Cloudflare sur les réponses AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            # Header Cloudflare pour désactiver le cache
            response['CF-Cache-Status'] = 'DYNAMIC'

        return response
