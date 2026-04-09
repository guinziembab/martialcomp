# -*- coding: utf-8 -*-
"""
Vue carte du monde pour Super Admin.
"""

import json
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.utils import timezone

from apps.superadmin.decorators import SuperAdminRequiredMixin
from apps.superadmin.services.geo_stats import GeoStatsService


class MapView(SuperAdminRequiredMixin, TemplateView):
    """
    Vue de la carte du monde avec visualisation des adhésions.
    """

    template_name = 'superadmin/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Carte du Monde'
        context['active_tab'] = 'map'

        # Récupérer la période demandée
        period = self.request.GET.get('period', '24h')
        context['current_period'] = period

        # Récupérer les données géographiques
        geo_service = GeoStatsService()

        # Stats par pays
        countries_stats = geo_service.get_countries_stats(period=period)
        context['countries_stats'] = countries_stats
        context['countries_stats_json'] = json.dumps(countries_stats)

        # Inscriptions récentes
        recent_signups = geo_service.get_recent_signups(limit=15)
        context['recent_signups'] = recent_signups
        # Pour le JSON, convertir les datetime en string
        recent_signups_for_json = [
            {**signup, 'created_at': signup['created_at'].isoformat() if hasattr(signup.get('created_at'), 'isoformat') else str(signup.get('created_at', ''))}
            for signup in recent_signups
        ]
        context['recent_signups_json'] = json.dumps(recent_signups_for_json)

        # Heatmap data
        heatmap_data = geo_service.get_heatmap_data(period='7d')
        context['heatmap_data'] = json.dumps(heatmap_data)

        # Totaux
        context['total_countries'] = len(countries_stats)
        context['total_signups'] = sum(c.get('count', 0) for c in countries_stats)

        # Top 5 pays
        context['top_countries'] = countries_stats[:5]

        return context


class MapDataView(SuperAdminRequiredMixin, TemplateView):
    """
    Endpoint AJAX pour les données de la carte.
    """

    def get(self, request, *args, **kwargs):
        period = request.GET.get('period', '24h')
        data_type = request.GET.get('type', 'countries')

        geo_service = GeoStatsService()

        if data_type == 'countries':
            data = geo_service.get_countries_stats(period=period)
        elif data_type == 'recent':
            limit = int(request.GET.get('limit', 10))
            country_code = request.GET.get('country')
            signups = geo_service.get_recent_signups(limit=limit, country_code=country_code)
            # Convertir les datetime en string pour JSON
            data = [
                {**s, 'created_at': s['created_at'].isoformat() if hasattr(s.get('created_at'), 'isoformat') else str(s.get('created_at', ''))}
                for s in signups
            ]
        elif data_type == 'heatmap':
            data = geo_service.get_heatmap_data(period=period)
        elif data_type == 'country':
            country_code = request.GET.get('code', '')
            data = geo_service.get_country_detail(country_code)
        else:
            data = {'error': 'Type de données inconnu'}

        return JsonResponse({
            'data': data,
            'timestamp': timezone.now().isoformat(),
            'period': period,
        })
