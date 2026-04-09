# -*- coding: utf-8 -*-
"""
Service de statistiques géographiques pour Super Admin.
"""

import logging
from datetime import timedelta
from typing import Dict, List, Any, Optional

from django.db.models import Count, Q
from django.utils import timezone
from django.core.cache import cache

logger = logging.getLogger(__name__)


class GeoStatsService:
    """
    Service pour les statistiques géographiques.
    Utilisé pour la carte du monde dans le dashboard Super Admin.
    """

    CACHE_TTL = 300  # 5 minutes

    # Coordonnées par défaut des pays (capitales)
    # Inclut les codes ISO 2 lettres et les noms courants
    COUNTRY_COORDINATES = {
        # Europe
        'BE': {'lat': 50.85, 'lng': 4.35, 'name': 'Belgique', 'flag': '🇧🇪'},
        'BELGIQUE': {'lat': 50.85, 'lng': 4.35, 'name': 'Belgique', 'flag': '🇧🇪'},
        'FR': {'lat': 48.86, 'lng': 2.35, 'name': 'France', 'flag': '🇫🇷'},
        'FRANCE': {'lat': 48.86, 'lng': 2.35, 'name': 'France', 'flag': '🇫🇷'},
        'DE': {'lat': 52.52, 'lng': 13.40, 'name': 'Allemagne', 'flag': '🇩🇪'},
        'NL': {'lat': 52.37, 'lng': 4.89, 'name': 'Pays-Bas', 'flag': '🇳🇱'},
        'LU': {'lat': 49.61, 'lng': 6.13, 'name': 'Luxembourg', 'flag': '🇱🇺'},
        'CH': {'lat': 46.95, 'lng': 7.45, 'name': 'Suisse', 'flag': '🇨🇭'},
        'IT': {'lat': 41.90, 'lng': 12.50, 'name': 'Italie', 'flag': '🇮🇹'},
        'ES': {'lat': 40.42, 'lng': -3.70, 'name': 'Espagne', 'flag': '🇪🇸'},
        'PT': {'lat': 38.72, 'lng': -9.13, 'name': 'Portugal', 'flag': '🇵🇹'},
        'GB': {'lat': 51.51, 'lng': -0.13, 'name': 'Royaume-Uni', 'flag': '🇬🇧'},
        'UK': {'lat': 51.51, 'lng': -0.13, 'name': 'Royaume-Uni', 'flag': '🇬🇧'},
        'AT': {'lat': 48.21, 'lng': 16.37, 'name': 'Autriche', 'flag': '🇦🇹'},
        'PL': {'lat': 52.23, 'lng': 21.01, 'name': 'Pologne', 'flag': '🇵🇱'},
        'CZ': {'lat': 50.08, 'lng': 14.44, 'name': 'République tchèque', 'flag': '🇨🇿'},
        'GR': {'lat': 37.98, 'lng': 23.73, 'name': 'Grèce', 'flag': '🇬🇷'},
        'SE': {'lat': 59.33, 'lng': 18.07, 'name': 'Suède', 'flag': '🇸🇪'},
        'NO': {'lat': 59.91, 'lng': 10.75, 'name': 'Norvège', 'flag': '🇳🇴'},
        'DK': {'lat': 55.68, 'lng': 12.57, 'name': 'Danemark', 'flag': '🇩🇰'},
        'FI': {'lat': 60.17, 'lng': 24.94, 'name': 'Finlande', 'flag': '🇫🇮'},
        'IE': {'lat': 53.35, 'lng': -6.26, 'name': 'Irlande', 'flag': '🇮🇪'},
        'RO': {'lat': 44.43, 'lng': 26.10, 'name': 'Roumanie', 'flag': '🇷🇴'},
        'HU': {'lat': 47.50, 'lng': 19.04, 'name': 'Hongrie', 'flag': '🇭🇺'},
        # Amériques
        'US': {'lat': 38.90, 'lng': -77.04, 'name': 'États-Unis', 'flag': '🇺🇸'},
        'USA': {'lat': 38.90, 'lng': -77.04, 'name': 'États-Unis', 'flag': '🇺🇸'},
        'CA': {'lat': 45.42, 'lng': -75.70, 'name': 'Canada', 'flag': '🇨🇦'},
        'BR': {'lat': -15.79, 'lng': -47.88, 'name': 'Brésil', 'flag': '🇧🇷'},
        'MX': {'lat': 19.43, 'lng': -99.13, 'name': 'Mexique', 'flag': '🇲🇽'},
        'AR': {'lat': -34.61, 'lng': -58.38, 'name': 'Argentine', 'flag': '🇦🇷'},
        'CO': {'lat': 4.71, 'lng': -74.07, 'name': 'Colombie', 'flag': '🇨🇴'},
        # Asie
        'JP': {'lat': 35.68, 'lng': 139.69, 'name': 'Japon', 'flag': '🇯🇵'},
        'KR': {'lat': 37.57, 'lng': 126.98, 'name': 'Corée du Sud', 'flag': '🇰🇷'},
        'CN': {'lat': 39.90, 'lng': 116.41, 'name': 'Chine', 'flag': '🇨🇳'},
        'IN': {'lat': 28.61, 'lng': 77.21, 'name': 'Inde', 'flag': '🇮🇳'},
        'TH': {'lat': 13.76, 'lng': 100.50, 'name': 'Thaïlande', 'flag': '🇹🇭'},
        'VN': {'lat': 21.03, 'lng': 105.85, 'name': 'Vietnam', 'flag': '🇻🇳'},
        'ID': {'lat': -6.21, 'lng': 106.85, 'name': 'Indonésie', 'flag': '🇮🇩'},
        'MY': {'lat': 3.14, 'lng': 101.69, 'name': 'Malaisie', 'flag': '🇲🇾'},
        'SG': {'lat': 1.35, 'lng': 103.82, 'name': 'Singapour', 'flag': '🇸🇬'},
        'PH': {'lat': 14.60, 'lng': 120.98, 'name': 'Philippines', 'flag': '🇵🇭'},
        # Océanie
        'AU': {'lat': -35.28, 'lng': 149.13, 'name': 'Australie', 'flag': '🇦🇺'},
        'NZ': {'lat': -41.29, 'lng': 174.78, 'name': 'Nouvelle-Zélande', 'flag': '🇳🇿'},
        # Afrique
        'MA': {'lat': 34.02, 'lng': -6.83, 'name': 'Maroc', 'flag': '🇲🇦'},
        'DZ': {'lat': 36.75, 'lng': 3.06, 'name': 'Algérie', 'flag': '🇩🇿'},
        'TN': {'lat': 36.81, 'lng': 10.17, 'name': 'Tunisie', 'flag': '🇹🇳'},
        'EG': {'lat': 30.04, 'lng': 31.24, 'name': 'Égypte', 'flag': '🇪🇬'},
        'SN': {'lat': 14.69, 'lng': -17.44, 'name': 'Sénégal', 'flag': '🇸🇳'},
        'CI': {'lat': 5.32, 'lng': -4.03, 'name': "Côte d'Ivoire", 'flag': '🇨🇮'},
        'GA': {'lat': -0.39, 'lng': 9.45, 'name': 'Gabon', 'flag': '🇬🇦'},
        'CM': {'lat': 3.87, 'lng': 11.52, 'name': 'Cameroun', 'flag': '🇨🇲'},
        'ZA': {'lat': -25.75, 'lng': 28.19, 'name': 'Afrique du Sud', 'flag': '🇿🇦'},
        'NG': {'lat': 9.08, 'lng': 7.40, 'name': 'Nigeria', 'flag': '🇳🇬'},
        'KE': {'lat': -1.29, 'lng': 36.82, 'name': 'Kenya', 'flag': '🇰🇪'},
        'GH': {'lat': 5.56, 'lng': -0.19, 'name': 'Ghana', 'flag': '🇬🇭'},
        'CD': {'lat': -4.44, 'lng': 15.27, 'name': 'RD Congo', 'flag': '🇨🇩'},
        'CG': {'lat': -4.27, 'lng': 15.28, 'name': 'Congo', 'flag': '🇨🇬'},
        # Moyen-Orient
        'AE': {'lat': 24.47, 'lng': 54.37, 'name': 'Émirats arabes unis', 'flag': '🇦🇪'},
        'SA': {'lat': 24.71, 'lng': 46.68, 'name': 'Arabie saoudite', 'flag': '🇸🇦'},
        'TR': {'lat': 39.93, 'lng': 32.85, 'name': 'Turquie', 'flag': '🇹🇷'},
        'IL': {'lat': 31.77, 'lng': 35.22, 'name': 'Israël', 'flag': '🇮🇱'},
        'QA': {'lat': 25.29, 'lng': 51.53, 'name': 'Qatar', 'flag': '🇶🇦'},
        'RU': {'lat': 55.76, 'lng': 37.62, 'name': 'Russie', 'flag': '🇷🇺'},
    }

    def get_countries_stats(self, period: str = '24h') -> List[Dict[str, Any]]:
        """
        Retourne les statistiques par pays.

        Args:
            period: '24h', '7d', '30d'

        Returns:
            list: [{
                'country_code': str,
                'country_name': str,
                'new_memberships': int,
                'total_organizations': int,
                'active_competitions': int,
                'coordinates': {'lat': float, 'lng': float}
            }]
        """
        cache_key = f'superadmin:geo_countries:{period}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        try:
            from apps.organizations.models import Organization
            from apps.competitions.models import Competition

            # Calculer la date de début
            now = timezone.now()
            if period == '24h':
                start_date = now - timedelta(hours=24)
            elif period == '7d':
                start_date = now - timedelta(days=7)
            else:
                start_date = now - timedelta(days=30)

            # Agrégation par pays
            org_stats = Organization.objects.filter(
                is_active=True
            ).exclude(
                country__isnull=True
            ).exclude(
                country=''
            ).values('country').annotate(
                total=Count('id'),
                new=Count('id', filter=Q(created_at__gte=start_date))
            )

            # Compétitions actives par pays
            comp_stats = Competition.objects.filter(
                status__in=['open', 'ongoing']
            ).exclude(
                organizing_organization__country__isnull=True
            ).values('organizing_organization__country').annotate(
                active=Count('id')
            )

            # Construire le dictionnaire des compétitions
            comp_by_country = {
                item['organizing_organization__country']: item['active']
                for item in comp_stats
            }

            # Construire le résultat
            result = []
            total_count = sum(item['total'] for item in org_stats)

            for item in org_stats:
                country_code = item['country'].upper() if item['country'] else ''
                if not country_code:
                    continue

                coords = self.COUNTRY_COORDINATES.get(country_code, {})
                count = item['total']

                result.append({
                    'country_code': country_code,
                    'country_name': coords.get('name', country_code),
                    'flag': coords.get('flag', '🌍'),
                    'new_memberships': item['new'],
                    'total_organizations': count,
                    'active_competitions': comp_by_country.get(country_code, 0),
                    # Champs attendus par le JavaScript de la carte
                    'count': count,
                    'delta_24h': item['new'],
                    'percent': (count / total_count * 100) if total_count > 0 else 0,
                    # Coordonnées à plat (attendu par Leaflet)
                    'lat': coords.get('lat', 0),
                    'lng': coords.get('lng', 0),
                    # Garder aussi le format imbriqué pour compatibilité
                    'coordinates': {
                        'lat': coords.get('lat', 0),
                        'lng': coords.get('lng', 0)
                    }
                })

            # Trier par total décroissant
            result.sort(key=lambda x: -x['count'])

            cache.set(cache_key, result, self.CACHE_TTL)
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats pays: {e}")
            return []

    def get_country_detail(self, country_code: str) -> Dict[str, Any]:
        """
        Retourne les statistiques détaillées d'un pays.

        Args:
            country_code: Code ISO du pays (ex: 'BE')

        Returns:
            dict: Statistiques détaillées
        """
        try:
            from apps.organizations.models import Organization
            from apps.competitions.models import Competition

            country_code = country_code.upper()
            coords = self.COUNTRY_COORDINATES.get(country_code, {})

            # Organisations du pays
            organizations = Organization.objects.filter(
                country__iexact=country_code,
                is_active=True
            ).order_by('-created_at')[:10]

            # Compétitions actives
            active_competitions = Competition.objects.filter(
                organizing_organization__country__iexact=country_code,
                status__in=['open', 'ongoing']
            ).count()

            # Stats 24h
            day_ago = timezone.now() - timedelta(hours=24)
            new_24h = organizations.filter(created_at__gte=day_ago).count()

            return {
                'country_code': country_code,
                'country_name': coords.get('name', country_code),
                'coordinates': {
                    'lat': coords.get('lat', 0),
                    'lng': coords.get('lng', 0)
                },
                'total_organizations': organizations.count(),
                'new_24h': new_24h,
                'active_competitions': active_competitions,
                'recent_organizations': [
                    {
                        'id': org.id,
                        'name': org.name,
                        'city': getattr(org, 'city', ''),
                        'created_at': org.created_at.isoformat()
                    }
                    for org in organizations[:5]
                ]
            }

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du détail pays {country_code}: {e}")
            return {}

    def get_recent_signups(
        self,
        limit: int = 10,
        country_code: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retourne les dernières inscriptions.

        Args:
            limit: Nombre maximum de résultats
            country_code: Filtrer par pays (optionnel)

        Returns:
            list: Dernières inscriptions avec localisation
        """
        try:
            from apps.organizations.models import Organization

            qs = Organization.objects.filter(
                is_active=True
            ).order_by('-created_at')

            if country_code:
                qs = qs.filter(country__iexact=country_code)

            organizations = qs[:limit]

            result = []
            for org in organizations:
                country = getattr(org, 'country', '') or ''
                coords = self.COUNTRY_COORDINATES.get(country.upper(), {})

                result.append({
                    'id': org.id,
                    'name': org.name,
                    'city': getattr(org, 'city', ''),
                    'country_code': country.upper(),
                    'country_name': coords.get('name', country),
                    'created_at': org.created_at,  # Garder l'objet datetime pour le template
                    # Coordonnées à plat (attendu par le template)
                    'lat': coords.get('lat', 0),
                    'lng': coords.get('lng', 0),
                    'coordinates': {
                        'lat': coords.get('lat', 0),
                        'lng': coords.get('lng', 0)
                    }
                })

            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des inscriptions récentes: {e}")
            return []

    def get_heatmap_data(self, period: str = '7d') -> List[Dict[str, Any]]:
        """
        Retourne les données pour une heatmap.

        Args:
            period: '24h', '7d', '30d'

        Returns:
            list: [{'lat': float, 'lng': float, 'intensity': int}]
        """
        try:
            countries = self.get_countries_stats(period)

            result = []
            for country in countries:
                if country['coordinates']['lat'] and country['coordinates']['lng']:
                    result.append({
                        'lat': country['coordinates']['lat'],
                        'lng': country['coordinates']['lng'],
                        'intensity': country['new_memberships'] + country['total_organizations']
                    })

            return result

        except Exception as e:
            logger.error(f"Erreur lors de la génération des données heatmap: {e}")
            return []
