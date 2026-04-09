# -*- coding: utf-8 -*-
"""
Vue Dashboard Super Admin.
"""

import json
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from apps.superadmin.decorators import SuperAdminRequiredMixin
from apps.superadmin.services.metrics import MetricsService


class DashboardView(SuperAdminRequiredMixin, TemplateView):
    """
    Dashboard principal du Super Admin.

    Affiche:
    - État de la plateforme (opérationnel/dégradé/down)
    - KPIs temps réel
    - Adhésions par profil
    - Graphique d'évolution
    - Statut des services
    """

    template_name = 'superadmin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service = MetricsService()

        # Données pour le dashboard
        context['page_title'] = _('Dashboard Super Admin')
        context['active_tab'] = 'dashboard'

        # Statut plateforme
        context['platform_status'] = service.get_platform_status()

        # KPIs
        context['kpis'] = service.get_kpis()

        # Adhésions par profil
        context['memberships_by_profile'] = service.get_memberships_by_profile()

        # Données d'évolution (7 jours)
        evolution_data = service.get_evolution_data(days=7)
        context['evolution_data'] = json.dumps(evolution_data)

        # Stats DB et stockage
        context['db_stats'] = service.get_database_stats()
        context['storage_stats'] = service.get_storage_stats()

        # Statut des services
        context['services'] = service.get_services_status()

        # Tabs de navigation
        context['tabs'] = [
            {'id': 'dashboard', 'name': _('Dashboard'), 'icon': 'fas fa-tachometer-alt', 'url': 'superadmin:dashboard'},
            {'id': 'map', 'name': _('Carte'), 'icon': 'fas fa-globe', 'url': 'superadmin:map'},
            {'id': 'memberships', 'name': _('Memberships'), 'icon': 'fas fa-users', 'url': 'superadmin:membership_list'},
            {'id': 'system', 'name': _('Système'), 'icon': 'fas fa-server', 'url': 'superadmin:system'},
            {'id': 'config', 'name': _('Config'), 'icon': 'fas fa-cogs', 'url': 'superadmin:config'},
            {'id': 'logs', 'name': _('Logs'), 'icon': 'fas fa-file-alt', 'url': 'superadmin:logs'},
        ]

        return context
