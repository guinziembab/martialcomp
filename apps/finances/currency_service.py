# -*- coding: utf-8 -*-
"""
Service de gestion des devises pour MartialComp.

Ce module fournit:
- Conversion entre devises avec cache
- Detection automatique de la devise selon l'organisation/utilisateur
- Integration avec les APIs de taux de change externes
- Fallback sur les taux statiques si API indisponible

Mis a jour: Janvier 2025 - Integration avec les modeles Currency et ExchangeRate
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional, Tuple, Union

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


# Configuration des APIs de taux de change
EXCHANGE_RATE_PROVIDERS = {
    'openexchangerates': {
        'url': 'https://openexchangerates.org/api/latest.json',
        'api_key_setting': 'OPENEXCHANGERATES_API_KEY',
        'base_param': 'base',
        'response_path': 'rates',
    },
    'exchangerate-api': {
        'url': 'https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}',
        'api_key_setting': 'EXCHANGERATE_API_KEY',
        'response_path': 'conversion_rates',
    },
    'fixer': {
        'url': 'http://data.fixer.io/api/latest',
        'api_key_setting': 'FIXER_API_KEY',
        'base_param': 'base',
        'response_path': 'rates',
    },
}

# Provider par defaut
DEFAULT_PROVIDER = getattr(settings, 'EXCHANGE_RATE_PROVIDER', 'openexchangerates')


# Cache en memoire pour les taux (backup du cache Django)
@dataclass
class _RatesCache:
    base: str
    rates: Dict[str, float]
    updated_at: datetime


_MEMORY_CACHE: Optional[_RatesCache] = None
_CACHE_TTL = timedelta(hours=1)
_CACHE_KEY_PREFIX = 'exchange_rates'


# Mapping pays -> devise
COUNTRY_TO_CURRENCY: Dict[str, str] = {
    # Europe
    'FR': 'EUR', 'France': 'EUR',
    'DE': 'EUR', 'Germany': 'EUR',
    'ES': 'EUR', 'Spain': 'EUR',
    'IT': 'EUR', 'Italy': 'EUR',
    'PT': 'EUR', 'Portugal': 'EUR',
    'NL': 'EUR', 'Netherlands': 'EUR',
    'BE': 'EUR', 'Belgium': 'EUR',
    'IE': 'EUR', 'Ireland': 'EUR',
    'AT': 'EUR', 'Austria': 'EUR',
    'GR': 'EUR', 'Greece': 'EUR',
    'FI': 'EUR', 'Finland': 'EUR',
    'GB': 'GBP', 'UK': 'GBP', 'United Kingdom': 'GBP',
    'CH': 'CHF', 'Switzerland': 'CHF',
    'NO': 'NOK', 'Norway': 'NOK',
    'SE': 'SEK', 'Sweden': 'SEK',
    'DK': 'DKK', 'Denmark': 'DKK',
    'PL': 'PLN', 'Poland': 'PLN',
    'CZ': 'CZK', 'Czech Republic': 'CZK',
    'HU': 'HUF', 'Hungary': 'HUF',
    'RO': 'RON', 'Romania': 'RON',
    'RU': 'RUB', 'Russia': 'RUB',

    # Americas
    'US': 'USD', 'USA': 'USD', 'United States': 'USD',
    'CA': 'CAD', 'Canada': 'CAD',
    'BR': 'BRL', 'Brazil': 'BRL',
    'MX': 'MXN', 'Mexico': 'MXN',
    'AR': 'ARS', 'Argentina': 'ARS',
    'CL': 'CLP', 'Chile': 'CLP',
    'CO': 'COP', 'Colombia': 'COP',
    'PE': 'PEN', 'Peru': 'PEN',

    # Afrique - Zone CFA UEMOA (XOF)
    'SN': 'XOF', 'Senegal': 'XOF',
    'CI': 'XOF', "Cote d'Ivoire": 'XOF', 'Ivory Coast': 'XOF',
    'ML': 'XOF', 'Mali': 'XOF',
    'BF': 'XOF', 'Burkina Faso': 'XOF',
    'NE': 'XOF', 'Niger': 'XOF',
    'TG': 'XOF', 'Togo': 'XOF',
    'BJ': 'XOF', 'Benin': 'XOF',
    'GW': 'XOF', 'Guinea-Bissau': 'XOF',

    # Afrique - Zone CFA CEMAC (XAF)
    'CM': 'XAF', 'Cameroon': 'XAF',
    'GA': 'XAF', 'Gabon': 'XAF',
    'CG': 'XAF', 'Congo': 'XAF',
    'TD': 'XAF', 'Chad': 'XAF',
    'CF': 'XAF', 'Central African Republic': 'XAF',
    'GQ': 'XAF', 'Equatorial Guinea': 'XAF',

    # Afrique du Nord
    'MA': 'MAD', 'Morocco': 'MAD',
    'DZ': 'DZD', 'Algeria': 'DZD',
    'TN': 'TND', 'Tunisia': 'TND',
    'EG': 'EGP', 'Egypt': 'EGP',

    # Afrique - Autres
    'NG': 'NGN', 'Nigeria': 'NGN',
    'ZA': 'ZAR', 'South Africa': 'ZAR',
    'KE': 'KES', 'Kenya': 'KES',
    'GH': 'GHS', 'Ghana': 'GHS',
    'ET': 'ETB', 'Ethiopia': 'ETB',

    # Asie
    'JP': 'JPY', 'Japan': 'JPY',
    'CN': 'CNY', 'China': 'CNY',
    'IN': 'INR', 'India': 'INR',
    'KR': 'KRW', 'South Korea': 'KRW',
    'TH': 'THB', 'Thailand': 'THB',
    'VN': 'VND', 'Vietnam': 'VND',
    'ID': 'IDR', 'Indonesia': 'IDR',
    'MY': 'MYR', 'Malaysia': 'MYR',
    'SG': 'SGD', 'Singapore': 'SGD',
    'PH': 'PHP', 'Philippines': 'PHP',

    # Moyen-Orient
    'AE': 'AED', 'UAE': 'AED', 'United Arab Emirates': 'AED',
    'SA': 'SAR', 'Saudi Arabia': 'SAR',
    'IL': 'ILS', 'Israel': 'ILS',
    'TR': 'TRY', 'Turkey': 'TRY',

    # Oceanie
    'AU': 'AUD', 'Australia': 'AUD',
    'NZ': 'NZD', 'New Zealand': 'NZD',
}

# Taux de secours (relatifs a EUR) - utilises si base de donnees et API indisponibles
_DEFAULT_BASE = 'EUR'
_FALLBACK_RATES: Dict[str, float] = {
    'EUR': 1.0,
    'USD': 1.10,
    'GBP': 0.85,
    'CHF': 0.94,
    'CAD': 1.47,
    'BRL': 6.00,
    'JPY': 170.0,
    'CNY': 7.90,
    'INR': 92.0,
    'XOF': 655.957,  # Taux fixe CFA
    'XAF': 655.957,  # Taux fixe CFA
    'MAD': 10.80,
    'NGN': 1800.0,
    'KRW': 1500.0,
    'AED': 4.00,
    'SAR': 4.10,
    'AUD': 1.65,
    'NZD': 1.80,
    'ZAR': 20.0,
}


def _now() -> datetime:
    """Retourne l'heure actuelle avec timezone."""
    return timezone.now()


def _get_cache_key(base: str) -> str:
    """Genere une cle de cache pour les taux."""
    return f"{_CACHE_KEY_PREFIX}:{base}"


# =============================================================================
# RECUPERATION DES TAUX DEPUIS LA BASE DE DONNEES
# =============================================================================

def get_rates_from_database(base: str = 'EUR') -> Optional[Dict[str, Decimal]]:
    """
    Recupere les taux de change depuis le modele ExchangeRate.

    Args:
        base: Code devise de base (defaut EUR)

    Returns:
        Dict des taux ou None si erreur
    """
    try:
        from .models import Currency, ExchangeRate

        rates = {base: Decimal('1.0')}

        # Taux directs depuis la base
        direct_rates = ExchangeRate.objects.filter(
            from_currency_id=base,
            is_current=True
        ).select_related('to_currency')

        for rate_obj in direct_rates:
            rates[rate_obj.to_currency_id] = rate_obj.rate

        # Taux inverses
        inverse_rates = ExchangeRate.objects.filter(
            to_currency_id=base,
            is_current=True
        ).select_related('from_currency')

        for rate_obj in inverse_rates:
            if rate_obj.from_currency_id not in rates:
                rates[rate_obj.from_currency_id] = Decimal('1.0') / rate_obj.rate

        if len(rates) > 1:
            logger.debug(f"Recupere {len(rates)} taux depuis la base de donnees")
            return rates

    except Exception as e:
        logger.warning(f"Erreur recuperation taux depuis DB: {e}")

    return None


# =============================================================================
# RECUPERATION DES TAUX DEPUIS API EXTERNE
# =============================================================================

def fetch_rates_from_api(
    base: str = 'EUR',
    provider: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """
    Recupere les taux de change depuis une API externe.

    Args:
        base: Code devise de base
        provider: Nom du provider (openexchangerates, fixer, etc.)

    Returns:
        Dict des taux ou None si erreur
    """
    import requests

    provider = provider or DEFAULT_PROVIDER
    config = EXCHANGE_RATE_PROVIDERS.get(provider)

    if not config:
        logger.error(f"Provider inconnu: {provider}")
        return None

    api_key = getattr(settings, config['api_key_setting'], None)
    if not api_key:
        logger.warning(f"Cle API non configuree pour {provider}")
        return None

    try:
        # Construire l'URL
        url = config['url']
        params = {'access_key': api_key}

        if '{api_key}' in url:
            url = url.format(api_key=api_key, base=base)
            params = {}
        elif 'base_param' in config:
            params[config['base_param']] = base

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extraire les taux selon le provider
        response_path = config.get('response_path', 'rates')
        rates = data
        for key in response_path.split('.'):
            rates = rates.get(key, {})

        if rates and isinstance(rates, dict):
            logger.info(f"Recupere {len(rates)} taux depuis {provider}")
            return rates

    except requests.RequestException as e:
        logger.error(f"Erreur API {provider}: {e}")
    except Exception as e:
        logger.error(f"Erreur traitement reponse {provider}: {e}")

    return None


def update_rates_in_database(
    rates: Dict[str, float],
    base: str = 'EUR',
    source: str = 'API'
) -> int:
    """
    Met a jour les taux de change dans la base de donnees.

    Args:
        rates: Dict des taux (code -> rate)
        base: Devise de base
        source: Source des taux (API, MANUAL, etc.)

    Returns:
        Nombre de taux mis a jour
    """
    try:
        from .models import Currency, ExchangeRate

        updated_count = 0
        valid_from = _now()

        # Verifier que la devise de base existe
        try:
            base_currency = Currency.objects.get(code=base)
        except Currency.DoesNotExist:
            logger.error(f"Devise de base {base} non trouvee")
            return 0

        for code, rate in rates.items():
            if code == base:
                continue

            try:
                to_currency = Currency.objects.get(code=code)
            except Currency.DoesNotExist:
                # Devise non geree, ignorer
                continue

            # Creer ou mettre a jour le taux
            rate_decimal = Decimal(str(rate))

            ExchangeRate.objects.update_or_create(
                from_currency=base_currency,
                to_currency=to_currency,
                is_current=True,
                defaults={
                    'rate': rate_decimal,
                    'valid_from': valid_from,
                    'source': source,
                }
            )
            updated_count += 1

        logger.info(f"Mis a jour {updated_count} taux de change")
        return updated_count

    except Exception as e:
        logger.error(f"Erreur mise a jour taux en base: {e}")
        return 0


# =============================================================================
# FONCTIONS PRINCIPALES DE CONVERSION
# =============================================================================

def get_rates(base: Optional[str] = None) -> Tuple[str, Dict[str, float], datetime]:
    """
    Retourne les taux de change avec priorite:
    1. Cache Django/memoire
    2. Base de donnees (ExchangeRate)
    3. API externe
    4. Taux de secours statiques

    Args:
        base: Devise de base (defaut EUR)

    Returns:
        Tuple (base, rates_dict, updated_at)
    """
    global _MEMORY_CACHE

    desired_base = (base or _DEFAULT_BASE).upper()
    cache_key = _get_cache_key(desired_base)

    # 1. Verifier le cache Django
    cached = cache.get(cache_key)
    if cached:
        return cached['base'], cached['rates'], cached['updated_at']

    # 2. Verifier le cache memoire
    if _MEMORY_CACHE and _MEMORY_CACHE.base == desired_base:
        if _now() - _MEMORY_CACHE.updated_at < _CACHE_TTL:
            return _MEMORY_CACHE.base, dict(_MEMORY_CACHE.rates), _MEMORY_CACHE.updated_at

    # 3. Essayer la base de donnees
    db_rates = get_rates_from_database(desired_base)
    if db_rates:
        rates_float = {k: float(v) for k, v in db_rates.items()}
        updated_at = _now()

        # Mettre en cache
        cache_data = {'base': desired_base, 'rates': rates_float, 'updated_at': updated_at}
        cache.set(cache_key, cache_data, int(_CACHE_TTL.total_seconds()))
        _MEMORY_CACHE = _RatesCache(base=desired_base, rates=rates_float, updated_at=updated_at)

        return desired_base, rates_float, updated_at

    # 4. Essayer l'API externe (si cle configuree)
    api_rates = fetch_rates_from_api(desired_base)
    if api_rates:
        # Sauvegarder en base pour future utilisation
        update_rates_in_database(api_rates, desired_base, source='API')

        updated_at = _now()
        cache_data = {'base': desired_base, 'rates': api_rates, 'updated_at': updated_at}
        cache.set(cache_key, cache_data, int(_CACHE_TTL.total_seconds()))
        _MEMORY_CACHE = _RatesCache(base=desired_base, rates=api_rates, updated_at=updated_at)

        return desired_base, api_rates, updated_at

    # 5. Fallback sur les taux statiques
    logger.warning("Utilisation des taux de secours statiques")

    if desired_base not in _FALLBACK_RATES:
        desired_base = _DEFAULT_BASE

    # Rebaser les taux
    factor = _FALLBACK_RATES[desired_base]
    rebased: Dict[str, float] = {}
    for code, rate_vs_eur in _FALLBACK_RATES.items():
        if code == desired_base:
            rebased[code] = 1.0
        else:
            rebased[code] = float(rate_vs_eur) / float(factor)

    updated_at = _now()
    _MEMORY_CACHE = _RatesCache(base=desired_base, rates=rebased, updated_at=updated_at)

    return desired_base, rebased, updated_at


def convert_amount(
    amount: Union[float, Decimal, int],
    from_currency: str,
    to_currency: str,
    use_database: bool = True
) -> Tuple[Decimal, Decimal]:
    """
    Convertit un montant d'une devise a une autre.

    Args:
        amount: Montant a convertir
        from_currency: Devise source
        to_currency: Devise cible
        use_database: Utiliser le modele ExchangeRate si disponible

    Returns:
        Tuple (montant_converti, taux_applique)
    """
    from_code = (from_currency or _DEFAULT_BASE).upper()
    to_code = (to_currency or _DEFAULT_BASE).upper()
    amount_decimal = Decimal(str(amount))

    if from_code == to_code:
        return amount_decimal, Decimal('1.0')

    # Priorite au modele ExchangeRate
    if use_database:
        try:
            from .models import ExchangeRate
            rate = ExchangeRate.get_current_rate(from_code, to_code)
            converted = amount_decimal * rate
            return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), rate
        except (ValueError, Exception) as e:
            logger.debug(f"ExchangeRate non disponible: {e}")

    # Fallback sur le service de taux
    base, rates, _ = get_rates(base=from_code)

    if to_code in rates:
        applied_rate = Decimal(str(rates[to_code]))
        converted = amount_decimal * applied_rate
        return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), applied_rate

    # Conversion via EUR
    base, rates, _ = get_rates(base=_DEFAULT_BASE)
    if from_code in rates and to_code in rates:
        amount_in_eur = amount_decimal / Decimal(str(rates[from_code]))
        converted = amount_in_eur * Decimal(str(rates[to_code]))
        applied_rate = Decimal(str(rates[to_code])) / Decimal(str(rates[from_code]))
        return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), applied_rate

    # Pas de conversion possible
    logger.warning(f"Conversion impossible: {from_code} -> {to_code}")
    return amount_decimal, Decimal('1.0')


def format_currency(
    amount: Union[float, Decimal, int],
    currency_code: str,
    include_symbol: bool = True
) -> str:
    """
    Formate un montant selon les conventions de la devise.

    Args:
        amount: Montant a formater
        currency_code: Code ISO de la devise
        include_symbol: Inclure le symbole

    Returns:
        Montant formate (ex: "1 234,56 EUR" ou "€1,234.56")
    """
    try:
        from .models import Currency
        currency = Currency.objects.get(code=currency_code.upper())
        return currency.format_amount(amount, include_symbol)
    except Exception:
        # Fallback simple
        amount_decimal = Decimal(str(amount)).quantize(Decimal('0.01'))
        if include_symbol:
            return f"{amount_decimal} {currency_code.upper()}"
        return str(amount_decimal)


# =============================================================================
# DETECTION DEVISE PREFEREE
# =============================================================================

def _get_request_organization(request):
    """
    Resolution de l'organisation depuis la requete.

    Ordre de priorite:
    - request.user.organization
    - OrganizationMember actif
    - Session organization_context
    - Club de l'utilisateur
    - Header X-Organization-ID
    """
    try:
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            # Attribut direct
            org = getattr(user, 'organization', None)
            if org:
                return org

            # OrganizationMember
            try:
                from apps.organizations.models import OrganizationMember
                membership = (
                    OrganizationMember.objects
                    .filter(user=user, is_active=True)
                    .select_related('organization')
                    .first()
                )
                if membership and membership.organization:
                    return membership.organization
            except Exception:
                pass

            # Session
            try:
                session = getattr(request, 'session', None)
                if session:
                    org_ctx = session.get('organization_context')
                    if org_ctx and isinstance(org_ctx, dict) and org_ctx.get('id'):
                        from apps.organizations.models import Organization
                        return Organization.objects.filter(pk=int(org_ctx['id'])).first()
            except Exception:
                pass

            # Club
            try:
                from apps.competitions.models import Club
                club = Club.objects.filter(owner=user).first()
                if club:
                    if hasattr(club, 'organization') and club.organization:
                        return club.organization
            except Exception:
                pass

        # Header
        try:
            org_id = (
                request.META.get('HTTP_X_ORGANIZATION_ID') or
                request.headers.get('X-Organization-ID')
            )
            if org_id:
                from apps.organizations.models import Organization
                return Organization.objects.filter(pk=int(org_id)).first()
        except Exception:
            pass

    except Exception:
        pass

    return None


def get_preferred_currency_for_request(request) -> Tuple[str, str]:
    """
    Determine la devise preferee pour une requete.

    Priorite:
    1. Parametre query ?currency=XXX
    2. Session currency
    3. Preference utilisateur
    4. Pays de l'organisation
    5. Header X-Country
    6. Defaut EUR

    Returns:
        Tuple (code_devise, source)
    """
    # 1. Query parameter
    if hasattr(request, 'GET'):
        q = request.GET.get('currency')
        if q and isinstance(q, str) and len(q) <= 5:
            return (q.upper(), 'query')

    # 2. Session
    try:
        session = getattr(request, 'session', None)
        if session:
            sess_curr = session.get('currency')
            if sess_curr:
                return (str(sess_curr).upper(), 'session')
    except Exception:
        pass

    # 3. Preference utilisateur
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        preferred = getattr(user, 'preferred_currency', None)
        if preferred:
            return (str(preferred).upper(), 'user')

    # 4. Organisation/pays
    org = _get_request_organization(request)
    if org:
        # Essayer d'abord le champ currency de l'organisation
        org_currency = getattr(org, 'currency', None)
        if org_currency:
            if hasattr(org_currency, 'code'):
                return (org_currency.code, 'organization')
            return (str(org_currency).upper(), 'organization')

        # Sinon, deduire du pays
        country = getattr(org, 'country', '') or ''
        code = COUNTRY_TO_CURRENCY.get(country) or COUNTRY_TO_CURRENCY.get(str(country).upper())
        if code:
            return (code, 'organization')

    # 5. Header X-Country
    try:
        hdr_country = (
            request.META.get('HTTP_X_COUNTRY') or
            request.headers.get('X-Country')
        )
        if hdr_country:
            code = COUNTRY_TO_CURRENCY.get(hdr_country) or COUNTRY_TO_CURRENCY.get(str(hdr_country).upper())
            if code:
                return (code, 'header')
    except Exception:
        pass

    # 6. Defaut
    return (_DEFAULT_BASE, 'default')


def get_currency_for_country(country_code: str) -> str:
    """
    Retourne le code devise pour un pays.

    Args:
        country_code: Code ISO du pays

    Returns:
        Code devise (defaut EUR)
    """
    return COUNTRY_TO_CURRENCY.get(country_code, COUNTRY_TO_CURRENCY.get(country_code.upper(), 'EUR'))


# =============================================================================
# UTILITAIRES
# =============================================================================

def clear_rates_cache():
    """Vide tous les caches de taux."""
    global _MEMORY_CACHE
    _MEMORY_CACHE = None

    # Vider le cache Django pour tous les patterns possibles
    for currency in _FALLBACK_RATES.keys():
        cache.delete(_get_cache_key(currency))

    logger.info("Cache des taux de change vide")


def get_available_currencies() -> list:
    """
    Retourne la liste des devises disponibles.

    Returns:
        Liste de dicts avec code, name, symbol
    """
    try:
        from .models import Currency
        currencies = Currency.objects.filter(is_active=True).values('code', 'name', 'symbol')
        return list(currencies)
    except Exception:
        # Fallback
        return [{'code': code, 'name': code, 'symbol': code} for code in _FALLBACK_RATES.keys()]


def is_currency_supported(currency_code: str) -> bool:
    """Verifie si une devise est supportee."""
    try:
        from .models import Currency
        return Currency.objects.filter(code=currency_code.upper(), is_active=True).exists()
    except Exception:
        return currency_code.upper() in _FALLBACK_RATES
