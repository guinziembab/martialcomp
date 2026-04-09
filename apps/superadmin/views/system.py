# -*- coding: utf-8 -*-
"""
Vues de monitoring système pour Super Admin.
"""

from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse

from apps.superadmin.decorators import (
    SuperAdminRequiredMixin,
    CloudflareAjaxMixin
)
from apps.superadmin.models import ServiceStatus, AdminAction, PlatformAlert
from apps.superadmin.services.system_control import SystemControlService
from apps.superadmin.services.metrics import MetricsService


class SystemView(SuperAdminRequiredMixin, TemplateView):
    """
    Vue principale du monitoring système.
    """

    template_name = 'superadmin/system/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Monitoring Système')
        context['active_tab'] = 'system'

        # Récupérer le statut des services
        context['services'] = ServiceStatus.objects.all()

        # Récupérer les métriques système
        metrics_service = MetricsService()
        context['db_stats'] = metrics_service.get_database_stats()
        context['storage_stats'] = metrics_service.get_storage_stats()
        context['platform_status'] = metrics_service.get_platform_status()

        # Mode maintenance
        control_service = SystemControlService(
            user=self.request.user,
            request=self.request
        )
        context['maintenance_mode'] = control_service.is_maintenance_mode()

        # Alertes actives (non résolues)
        context['active_alerts'] = PlatformAlert.objects.filter(
            is_resolved=False
        ).order_by('-created_at')[:10]

        # Actions récentes
        context['recent_actions'] = AdminAction.objects.order_by(
            '-created_at'
        )[:20]

        return context


class RestartServiceView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue pour redémarrer Gunicorn (AJAX).
    """

    def post(self, request):
        service = SystemControlService(user=request.user, request=request)
        result = service.restart_gunicorn()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])

        return redirect(reverse('superadmin:system'))


class MaintenanceModeView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue pour activer/désactiver le mode maintenance (AJAX).
    """

    def post(self, request):
        action = request.POST.get('action', 'enable')
        service = SystemControlService(user=request.user, request=request)

        if action == 'disable':
            result = service.disable_maintenance_mode()
        else:
            result = service.enable_maintenance_mode()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])

        return redirect(reverse('superadmin:system'))


class ClearCacheView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue pour vider le cache (AJAX).
    """

    def post(self, request):
        service = SystemControlService(user=request.user, request=request)
        result = service.clear_cache()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])

        return redirect(reverse('superadmin:system'))


class TriggerBackupView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue pour déclencher un backup (AJAX).
    """

    def post(self, request):
        service = SystemControlService(user=request.user, request=request)
        result = service.trigger_backup()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)

        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])

        return redirect(reverse('superadmin:system'))


class EmergencyStopView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue pour l'arrêt d'urgence.
    """

    def get(self, request):
        """Affiche la page de confirmation."""
        return JsonResponse({
            'error': 'Utilisez POST pour cette action.',
            'confirm_required': True
        }, status=405)

    def post(self, request):
        reason = request.POST.get('reason', '')
        confirm = request.POST.get('confirm', 'false').lower() == 'true'

        if not confirm:
            return JsonResponse({
                'success': False,
                'message': _('Confirmation obligatoire pour l\'arrêt d\'urgence.')
            }, status=400)

        if not reason or len(reason) < 10:
            return JsonResponse({
                'success': False,
                'message': _('Une raison détaillée est obligatoire (min 10 caractères).')
            }, status=400)

        service = SystemControlService(user=request.user, request=request)
        result = service.emergency_stop(reason)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(result)

        if result['success']:
            messages.warning(request, result['message'])
        else:
            messages.error(request, result['message'])

        return redirect(reverse('superadmin:system'))


class RefreshServicesView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue AJAX pour rafraîchir le statut des services.
    """

    def get(self, request):
        service = SystemControlService(user=request.user, request=request)
        results = service.check_all_services()

        return JsonResponse({
            'success': True,
            'services': results,
        })


class AlertAcknowledgeView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue AJAX pour acquitter une alerte (marquer comme résolue).
    """

    def post(self, request, pk):
        from django.utils import timezone

        try:
            alert = PlatformAlert.objects.get(pk=pk)

            if alert.is_resolved:
                return JsonResponse({
                    'success': False,
                    'message': _('Alerte déjà résolue.')
                })

            alert.is_resolved = True
            alert.resolved_by = request.user
            alert.resolved_at = timezone.now()
            alert.save(update_fields=['is_resolved', 'resolved_by', 'resolved_at'])

            return JsonResponse({
                'success': True,
                'message': _('Alerte acquittée.')
            })

        except PlatformAlert.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Alerte non trouvée.')
            }, status=404)


class AlertResolveView(CloudflareAjaxMixin, SuperAdminRequiredMixin, View):
    """
    Vue AJAX pour résoudre une alerte.
    """

    def post(self, request, pk):
        from django.utils import timezone

        try:
            alert = PlatformAlert.objects.get(pk=pk)

            if alert.is_resolved:
                return JsonResponse({
                    'success': False,
                    'message': _('Alerte déjà résolue.')
                })

            alert.is_resolved = True
            alert.resolved_at = timezone.now()
            alert.resolved_by = request.user
            alert.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by'])

            return JsonResponse({
                'success': True,
                'message': _('Alerte résolue.')
            })

        except PlatformAlert.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Alerte non trouvée.')
            }, status=404)
