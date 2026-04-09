# -*- coding: utf-8 -*-
"""
Vues de logs et audit pour Super Admin.
"""

from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from datetime import timedelta
import csv
import json

from apps.superadmin.decorators import SuperAdminRequiredMixin
from apps.superadmin.models import AdminAction, PlatformAlert
from apps.superadmin.services.audit import AuditService


class LogsView(SuperAdminRequiredMixin, TemplateView):
    """
    Vue principale des logs et audit.
    """

    template_name = 'superadmin/logs/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Logs & Audit')
        context['active_tab'] = 'logs'

        # Filtres
        action_type = self.request.GET.get('action_type', '')
        user_id = self.request.GET.get('user_id', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        search = self.request.GET.get('search', '')

        # Récupérer les logs avec filtres
        logs = AdminAction.objects.select_related('admin_user').order_by('-created_at')

        if action_type:
            logs = logs.filter(action_type=action_type)
        if user_id:
            logs = logs.filter(admin_user_id=user_id)
        if date_from:
            logs = logs.filter(created_at__date__gte=date_from)
        if date_to:
            logs = logs.filter(created_at__date__lte=date_to)
        if search:
            logs = logs.filter(
                Q(description__icontains=search) |
                Q(admin_user__username__icontains=search) |
                Q(ip_address__icontains=search)
            )

        context['logs'] = logs[:500]  # Limiter à 500 entrées
        context['total_logs'] = logs.count()

        # Types d'actions distincts
        context['action_types'] = AdminAction.objects.values_list(
            'action_type', flat=True
        ).distinct()

        # Statistiques
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        context['stats'] = {
            'today': AdminAction.objects.filter(created_at__gte=today_start).count(),
            'week': AdminAction.objects.filter(created_at__gte=week_start).count(),
            'total': AdminAction.objects.count(),
        }

        # Graphique des logs par jour (7 derniers jours)
        logs_by_day = (
            AdminAction.objects
            .filter(created_at__gte=week_start)
            .annotate(date=TruncDate('created_at'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )
        context['logs_chart_data'] = json.dumps([
            {'date': log['date'].isoformat(), 'count': log['count']}
            for log in logs_by_day
        ])

        # Top actions
        context['top_actions'] = (
            AdminAction.objects
            .filter(created_at__gte=week_start)
            .values('action_type')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        # Filtres actifs
        context['filters'] = {
            'action_type': action_type,
            'user_id': user_id,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
        }

        return context


class LogsExportView(SuperAdminRequiredMixin, View):
    """
    Export des logs en CSV.
    """

    def get(self, request):
        format_type = request.GET.get('format', 'csv')
        action_type = request.GET.get('action_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')

        # Récupérer les logs avec filtres
        logs = AdminAction.objects.select_related('admin_user').order_by('-created_at')

        if action_type:
            logs = logs.filter(action_type=action_type)
        if date_from:
            logs = logs.filter(created_at__date__gte=date_from)
        if date_to:
            logs = logs.filter(created_at__date__lte=date_to)

        # Limiter à 10000 entrées pour l'export
        logs = logs[:10000]

        if format_type == 'json':
            return self._export_json(logs)
        else:
            return self._export_csv(logs)

    def _export_csv(self, logs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        )

        writer = csv.writer(response)
        writer.writerow([
            'Date/Heure', 'Utilisateur', 'Type Action', 'Description',
            'Adresse IP', 'User Agent'
        ])

        for log in logs:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.admin_user.username if log.admin_user else '-',
                log.action_type,
                log.description,
                log.ip_address or '-',
                log.user_agent[:100] if log.user_agent else '-',
            ])

        # Log l'export
        AuditService.log_action(
            user=self.request.user,
            action_type='logs_export',
            request=self.request,
            description=f"Export de {logs.count()} logs en CSV"
        )

        return response

    def _export_json(self, logs):
        data = [
            {
                'datetime': log.created_at.isoformat(),
                'user': log.admin_user.username if log.admin_user else None,
                'action_type': log.action_type,
                'description': log.description,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'result_message': log.result_message,
            }
            for log in logs
        ]

        response = HttpResponse(
            json.dumps(data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="logs_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        )

        # Log l'export
        AuditService.log_action(
            user=self.request.user,
            action_type='logs_export',
            request=self.request,
            description=f"Export de {len(data)} logs en JSON"
        )

        return response


class LogDetailView(SuperAdminRequiredMixin, View):
    """
    Détail d'un log (AJAX).
    """

    def get(self, request, pk):
        try:
            log = AdminAction.objects.select_related('admin_user').get(pk=pk)
            return JsonResponse({
                'success': True,
                'log': {
                    'id': log.id,
                    'datetime': log.created_at.isoformat(),
                    'user': log.admin_user.username if log.admin_user else None,
                    'user_email': log.admin_user.email if log.admin_user else None,
                    'action_type': log.action_type,
                    'description': log.description,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'result_message': log.result_message,
                }
            })
        except AdminAction.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': _('Log non trouvé')
            }, status=404)


class AlertsListView(SuperAdminRequiredMixin, TemplateView):
    """
    Liste des alertes.
    """

    template_name = 'superadmin/logs/alerts.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Alertes')
        context['active_tab'] = 'logs'

        # Filtres
        status = self.request.GET.get('status', 'active')
        severity = self.request.GET.get('severity', '')
        alert_type = self.request.GET.get('type', '')

        alerts = PlatformAlert.objects.order_by('-created_at')

        if status == 'active':
            alerts = alerts.filter(is_resolved=False)
        elif status == 'resolved':
            alerts = alerts.filter(is_resolved=True)

        if severity:
            alerts = alerts.filter(severity=severity)
        if alert_type:
            alerts = alerts.filter(alert_type=alert_type)

        context['alerts'] = alerts[:200]

        # Stats
        context['alert_stats'] = {
            'active': PlatformAlert.objects.filter(
                is_resolved=False
            ).count(),
            'resolved_today': PlatformAlert.objects.filter(
                is_resolved=True,
                resolved_at__date=timezone.now().date()
            ).count(),
            'total': PlatformAlert.objects.count(),
        }

        # Filtres actifs
        context['filters'] = {
            'status': status,
            'severity': severity,
            'type': alert_type,
        }

        return context


class ClearLogsView(SuperAdminRequiredMixin, View):
    """
    Purge des anciens logs.
    """

    def post(self, request):
        days = int(request.POST.get('days', 90))
        confirm = request.POST.get('confirm', 'false').lower() == 'true'

        if not confirm:
            return JsonResponse({
                'success': False,
                'message': _('Confirmation requise')
            }, status=400)

        if days < 30:
            return JsonResponse({
                'success': False,
                'message': _('La rétention minimale est de 30 jours')
            }, status=400)

        cutoff_date = timezone.now() - timedelta(days=days)
        count, _ = AdminAction.objects.filter(created_at__lt=cutoff_date).delete()

        AuditService.log_action(
            user=request.user,
            action_type='logs_purge',
            request=request,
            description=f"Purge de {count} logs antérieurs à {days} jours"
        )

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': _('%(count)d logs supprimés') % {'count': count},
                'deleted_count': count,
            })

        messages.success(request, _('%(count)d logs supprimés') % {'count': count})
        return redirect(reverse('superadmin:logs'))
