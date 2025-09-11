from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


# Very small in-memory cache for currency rates
@dataclass
class _RatesCache:
    base: str
    rates: Dict[str, float]
    updated_at: datetime


# Singleton cache instance
_CACHE: Optional[_RatesCache] = None
_CACHE_TTL = timedelta(hours=1)


# Minimal country -> currency mapping (extend as needed)
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
    'GB': 'GBP', 'UK': 'GBP', 'United Kingdom': 'GBP', 'Great Britain': 'GBP',

    # Americas
    'US': 'USD', 'USA': 'USD', 'United States': 'USD',
    'CA': 'CAD', 'Canada': 'CAD',
    'BR': 'BRL', 'Brazil': 'BRL',

    # Africa
    'NG': 'NGN', 'Nigeria': 'NGN',
    'CI': 'XOF', "Côte d'Ivoire": 'XOF', 'Ivory Coast': 'XOF',
    'SN': 'XOF', 'Senegal': 'XOF',
    'BF': 'XOF', 'Benin': 'XOF', 'BJ': 'XOF', 'TG': 'XOF', 'Togo': 'XOF', 'ML': 'XOF', 'NE': 'XOF', 'Niger': 'XOF', 'GW': 'XOF', 'Guinea-Bissau': 'XOF',
    'GA': 'XAF', 'Gabon': 'XAF',
    'CM': 'XAF', 'Cameroon': 'XAF',
    'TD': 'XAF', 'Chad': 'XAF',
    'CF': 'XAF', 'Central African Republic': 'XAF',
    'CG': 'XAF', 'Congo': 'XAF', 'Republic of the Congo': 'XAF',
    'GQ': 'XAF', 'Equatorial Guinea': 'XAF',
    'MA': 'MAD', 'Morocco': 'MAD',
    'DZ': 'DZD', 'Algeria': 'DZD',
    'TN': 'TND', 'Tunisia': 'TND',

    # Asia
    'JP': 'JPY', 'Japan': 'JPY',
    'CN': 'CNY', 'China': 'CNY',
    'IN': 'INR', 'India': 'INR',
    'KR': 'KRW', 'South Korea': 'KRW',

    # Middle East
    'AE': 'AED', 'UAE': 'AED', 'United Arab Emirates': 'AED',
    'SA': 'SAR', 'Saudi Arabia': 'SAR',
}

# Static fallback rates relative to base EUR (illustrative, not live)
# NOTE: In production, replace with a proper provider and persistent cache.
_DEFAULT_BASE = 'EUR'
_DEFAULT_RATES: Dict[str, float] = {
    'EUR': 1.0,
    'USD': 1.10,
    'GBP': 0.85,
    'CAD': 1.47,
    'BRL': 6.00,
    'NGN': 1800.0,
    'XOF': 655.957,
    'XAF': 655.957,
    'MAD': 10.8,
    'DZD': 148.0,
    'TND': 3.4,
    'JPY': 170.0,
    'CNY': 7.9,
    'INR': 92.0,
    'KRW': 1500.0,
    'AED': 4.0,
    'SAR': 4.1,
}


def _now() -> datetime:
    return datetime.utcnow()


def _get_request_organization(request):
    """Best-effort organization resolution from request/user.

    Order:
      - request.user.organization if present
      - first active OrganizationMember of user
      - session 'organization_context' id
      - user's owned Club -> related organization
      - header X-Organization-ID (numeric id)
    Returns Organization or None (imported lazily to avoid hard deps at import time).
    """
    try:
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            # Direct attribute on user (some projects attach it during login)
            org = getattr(user, 'organization', None)
            if org:
                return org

            # OrganizationMember lookup
            try:
                from apps.organizations.models import OrganizationMember  # type: ignore
                membership = (
                    OrganizationMember.objects
                    .filter(user=user, is_active=True)
                    .select_related('organization')
                    .first()
                )
                if membership and getattr(membership, 'organization', None):
                    return membership.organization
            except Exception:
                pass

            # Session-provided organization context
            try:
                org_ctx = getattr(request, 'session', {}).get('organization_context') if hasattr(request, 'session') else None
                if org_ctx and isinstance(org_ctx, dict) and org_ctx.get('id'):
                    from apps.organizations.models import Organization  # type: ignore
                    org_obj = Organization.objects.filter(pk=int(org_ctx['id'])).first()
                    if org_obj:
                        return org_obj
            except Exception:
                pass

            # User's owned club -> organization
            try:
                from apps.competitions.models import Club  # type: ignore
                club = Club.objects.filter(owner=user).first()
                if club:
                    if getattr(club, 'organization', None):
                        return club.organization
                    # legacy mapping
                    as_org = getattr(club, 'as_organization', None)
                    if as_org:
                        return as_org
            except Exception:
                pass

        # Header-based fallback (explicit org id provided by client)
        org_id = None
        try:
            org_id = request.META.get('HTTP_X_ORGANIZATION_ID') or request.headers.get('X-Organization-ID')  # type: ignore[attr-defined]
        except Exception:
            org_id = None
        if org_id:
            try:
                from apps.organizations.models import Organization  # type: ignore
                return Organization.objects.filter(pk=int(org_id)).first()
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_preferred_currency_for_request(request) -> Tuple[str, str]:
    """
    Determine preferred currency code for the request.
    Priority: query ?currency -> session -> user.preferred_currency -> organization country -> default EUR.
    Returns tuple: (currency_code, source_label)
    """
    # 1) explicit in query
    q = request.GET.get('currency') if hasattr(request, 'GET') else None
    if q and isinstance(q, str) and len(q) <= 5:
        return (q.upper(), 'query')

    # 2) session
    sess_curr = getattr(getattr(request, 'session', None), 'get', lambda *_: None)('currency') if hasattr(request, 'session') else None
    if sess_curr:
        return (str(sess_curr).upper(), 'session')

    # 3) user setting
    user = getattr(request, 'user', None)
    if user and getattr(user, 'is_authenticated', False):
        preferred = getattr(user, 'preferred_currency', None)
        if preferred:
            return (str(preferred).upper(), 'user')

    # 4) organization by country
    org = _get_request_organization(request)
    if org:
        country = getattr(org, 'country', '') or ''
        code = COUNTRY_TO_CURRENCY.get(country, COUNTRY_TO_CURRENCY.get(str(country).upper()))
        if code:
            return (code, 'organization')

    # 5) explicit country header (mobile can send X-Country)
    try:
        hdr_country = request.META.get('HTTP_X_COUNTRY') or request.headers.get('X-Country')  # type: ignore[attr-defined]
        if hdr_country:
            code = COUNTRY_TO_CURRENCY.get(hdr_country) or COUNTRY_TO_CURRENCY.get(str(hdr_country).upper())
            if code:
                return (code, 'header')
    except Exception:
        pass

    # fallback
    return (_DEFAULT_BASE, 'default')


def _cache_valid(cache: Optional[_RatesCache]) -> bool:
    if not cache:
        return False
    return _now() - cache.updated_at < _CACHE_TTL


def get_rates(base: Optional[str] = None) -> Tuple[str, Dict[str, float], datetime]:
    """
    Return (base, rates, updated_at). For now, serves static fallback rates with 1h TTL cache.
    """
    global _CACHE
    desired_base = (base or _DEFAULT_BASE).upper()

    if _cache_valid(_CACHE) and _CACHE and _CACHE.base == desired_base:
        return _CACHE.base, dict(_CACHE.rates), _CACHE.updated_at

    # For now, compute simple re-based rates from the default table
    if desired_base not in _DEFAULT_RATES:
        desired_base = _DEFAULT_BASE

    # Rebase
    factor = _DEFAULT_RATES[desired_base]
    rebased: Dict[str, float] = {}
    for code, rate_vs_eur in _DEFAULT_RATES.items():
        if code == desired_base:
            rebased[code] = 1.0
        else:
            # rate(desired->code) = rate(code vs EUR) / rate(desired vs EUR)
            rebased[code] = float(rate_vs_eur) / float(factor)

    _CACHE = _RatesCache(base=desired_base, rates=rebased, updated_at=_now())
    return _CACHE.base, dict(_CACHE.rates), _CACHE.updated_at


def convert_amount(amount: float, from_currency: str, to_currency: str) -> Tuple[float, float]:
    """
    Convert amount from one currency to another using our in-memory rates.
    Returns (converted_amount, applied_rate).
    """
    from_code = (from_currency or _DEFAULT_BASE).upper()
    to_code = (to_currency or _DEFAULT_BASE).upper()

    if from_code == to_code:
        return float(amount), 1.0

    base, rates, _ = get_rates(base=from_code)
    # In this representation, rates[c] is 1 unit of base -> c units
    if to_code not in rates:
        # Fallback: try via default EUR
        base, rates, _ = get_rates(base=_DEFAULT_BASE)
        if from_code not in rates or to_code not in rates:
            # Give up, return as-is
            return float(amount), 1.0
        # Convert from -> EUR, then EUR -> to
        amount_in_eur = float(amount) / float(rates[from_code])
        converted = amount_in_eur * float(rates[to_code])
        applied_rate = float(rates[to_code]) / float(rates[from_code])
        return float(converted), float(applied_rate)

    applied_rate = float(rates[to_code])
    converted = float(amount) * applied_rate
    return float(converted), float(applied_rate)
