# -*- coding: utf-8 -*-
"""
Template tags pour le module finances.

Ce module fournit:
- Formatage des montants selon la devise
- Conversion de devises dans les templates
- Affichage des symboles de devises

Mis a jour: Janvier 2025 - Support multi-devise
"""

from decimal import Decimal, InvalidOperation
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Permet d'acceder aux cles d'un dictionnaire dans un template Django,
    particulierement utile pour les cles contenant des caracteres speciaux.

    Usage: {{ mydict|get_item:"key-with-hyphen" }}
    """
    return dictionary.get(key, '')


# =============================================================================
# FILTRES DE FORMATAGE DE DEVISES
# =============================================================================

@register.filter(name='format_currency')
def format_currency(amount, currency_code='EUR'):
    """
    Formate un montant selon les conventions de la devise.

    Usage:
        {{ 1234.56|format_currency:"EUR" }}  -> "1 234,56 EUR"
        {{ 1234.56|format_currency:"USD" }}  -> "$1,234.56"
        {{ 1234.56|format_currency:"XOF" }}  -> "1 235 FCFA"

    Args:
        amount: Montant a formater
        currency_code: Code ISO de la devise (defaut EUR)

    Returns:
        str: Montant formate
    """
    if amount is None:
        return ""

    # Gerer les cas ou currency_code est None ou vide
    if not currency_code:
        currency_code = 'EUR'

    try:
        from apps.finances.currency_service import format_currency as fmt_curr
        return fmt_curr(amount, currency_code, include_symbol=True)
    except Exception:
        # Fallback simple
        try:
            decimal_amount = Decimal(str(amount))
            return f"{decimal_amount:.2f} {currency_code}"
        except (InvalidOperation, ValueError):
            return str(amount)


@register.filter(name='format_amount')
def format_amount(amount, currency_code='EUR'):
    """
    Formate un montant sans le symbole de devise.

    Usage:
        {{ 1234.56|format_amount:"EUR" }}  -> "1 234,56"

    Args:
        amount: Montant a formater
        currency_code: Code ISO de la devise

    Returns:
        str: Montant formate sans symbole
    """
    if amount is None:
        return ""

    try:
        from apps.finances.models import Currency
        currency = Currency.objects.get(code=currency_code.upper())
        return currency.format_amount(amount, include_symbol=False)
    except Exception:
        try:
            decimal_amount = Decimal(str(amount))
            return f"{decimal_amount:.2f}"
        except (InvalidOperation, ValueError):
            return str(amount)


@register.filter(name='currency_symbol')
def currency_symbol(currency_code):
    """
    Retourne le symbole d'une devise.

    Usage:
        {{ "EUR"|currency_symbol }}  -> "EUR"
        {{ "USD"|currency_symbol }}  -> "$"
        {{ "XOF"|currency_symbol }}  -> "FCFA"

    Args:
        currency_code: Code ISO de la devise

    Returns:
        str: Symbole de la devise
    """
    if not currency_code:
        return ""

    try:
        from apps.finances.models import Currency
        currency = Currency.objects.get(code=currency_code.upper())
        return currency.symbol
    except Exception:
        return currency_code.upper()


@register.filter(name='convert_currency')
def convert_currency(amount, conversion):
    """
    Convertit un montant d'une devise a une autre.

    Usage:
        {{ 100|convert_currency:"USD:EUR" }}  -> montant converti

    Args:
        amount: Montant a convertir
        conversion: Chaine "FROM:TO" (ex: "USD:EUR")

    Returns:
        Decimal: Montant converti
    """
    if amount is None or not conversion:
        return amount

    try:
        parts = conversion.split(':')
        if len(parts) != 2:
            return amount

        from_currency, to_currency = parts
        from apps.finances.currency_service import convert_amount
        converted, _ = convert_amount(amount, from_currency, to_currency)
        return converted
    except Exception:
        return amount


@register.filter(name='convert_and_format')
def convert_and_format(amount, conversion):
    """
    Convertit et formate un montant.

    Usage:
        {{ 100|convert_and_format:"USD:EUR" }}  -> "90,91 EUR"

    Args:
        amount: Montant a convertir
        conversion: Chaine "FROM:TO" (ex: "USD:EUR")

    Returns:
        str: Montant converti et formate
    """
    if amount is None or not conversion:
        return ""

    try:
        parts = conversion.split(':')
        if len(parts) != 2:
            return str(amount)

        from_currency, to_currency = parts
        from apps.finances.currency_service import convert_amount, format_currency
        converted, _ = convert_amount(amount, from_currency, to_currency)
        return format_currency(converted, to_currency, include_symbol=True)
    except Exception:
        return str(amount)


@register.filter(name='convert_from_eur')
def convert_from_eur(amount, target_currency='EUR'):
    """
    Convertit un montant depuis EUR vers la devise cible et le formate.

    C'est le filtre principal a utiliser pour afficher des montants stockes
    en EUR dans la devise preferee de l'utilisateur.

    Usage:
        {{ 1234.56|convert_from_eur:"XOF" }}  -> "810 047 FCFA"
        {{ 1234.56|convert_from_eur:"USD" }}  -> "$1,358.02"
        {{ 1234.56|convert_from_eur:"EUR" }}  -> "1 234,56 EUR"

    Args:
        amount: Montant en EUR a convertir
        target_currency: Code ISO de la devise cible (defaut EUR)

    Returns:
        str: Montant converti et formate dans la devise cible
    """
    if amount is None:
        return ""

    if not target_currency:
        target_currency = 'EUR'

    try:
        # Si la devise cible est EUR, pas de conversion necessaire
        if target_currency.upper() == 'EUR':
            from apps.finances.currency_service import format_currency as fmt_curr
            return fmt_curr(amount, 'EUR', include_symbol=True)

        # Convertir de EUR vers la devise cible
        from apps.finances.currency_service import convert_amount, format_currency as fmt_curr
        converted, _ = convert_amount(amount, 'EUR', target_currency.upper())
        return fmt_curr(converted, target_currency.upper(), include_symbol=True)
    except Exception as e:
        # Fallback: formater sans conversion
        try:
            decimal_amount = Decimal(str(amount))
            return f"{decimal_amount:.2f} {target_currency}"
        except (InvalidOperation, ValueError):
            return str(amount)


@register.filter(name='convert_from_eur_raw')
def convert_from_eur_raw(amount, target_currency='EUR'):
    """
    Convertit un montant depuis EUR vers la devise cible SANS formatage.

    Utile pour les calculs JavaScript ou les attributs data-*.

    Usage:
        {{ 1234.56|convert_from_eur_raw:"XOF" }}  -> 810047.32
        {{ 1234.56|convert_from_eur_raw:"USD" }}  -> 1358.02

    Args:
        amount: Montant en EUR a convertir
        target_currency: Code ISO de la devise cible

    Returns:
        Decimal: Montant converti (non formate)
    """
    if amount is None:
        return 0

    if not target_currency:
        target_currency = 'EUR'

    try:
        # Si la devise cible est EUR, pas de conversion
        if target_currency.upper() == 'EUR':
            return Decimal(str(amount))

        # Convertir de EUR vers la devise cible
        from apps.finances.currency_service import convert_amount
        converted, _ = convert_amount(amount, 'EUR', target_currency.upper())
        return converted
    except Exception:
        try:
            return Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return 0


# =============================================================================
# TAGS DE CONTEXTE
# =============================================================================

@register.simple_tag
def get_currency_rate(from_currency, to_currency):
    """
    Retourne le taux de change entre deux devises.

    Usage:
        {% get_currency_rate "EUR" "USD" as rate %}
        {{ rate }}  -> 1.10

    Args:
        from_currency: Devise source
        to_currency: Devise cible

    Returns:
        Decimal: Taux de change
    """
    try:
        from apps.finances.models import ExchangeRate
        return ExchangeRate.get_current_rate(from_currency, to_currency)
    except Exception:
        return Decimal('1.0')


@register.simple_tag
def get_available_currencies():
    """
    Retourne la liste des devises disponibles.

    Usage:
        {% get_available_currencies as currencies %}
        {% for c in currencies %}{{ c.code }}{% endfor %}

    Returns:
        QuerySet: Devises actives
    """
    try:
        from apps.finances.models import Currency
        return Currency.objects.filter(is_active=True).order_by('code')
    except Exception:
        return []


@register.simple_tag(takes_context=True)
def get_user_currency(context):
    """
    Retourne la devise preferee de l'utilisateur.

    Usage:
        {% get_user_currency as user_currency %}
        {{ user_currency }}  -> "EUR"

    Returns:
        str: Code de la devise preferee
    """
    try:
        request = context.get('request')
        if request:
            from apps.finances.currency_service import (
                get_preferred_currency_for_request
            )
            code, _ = get_preferred_currency_for_request(request)
            return code
    except Exception:
        pass
    return 'EUR'


@register.inclusion_tag('finances/tags/currency_selector.html', takes_context=True)
def currency_selector(context, css_class=''):
    """
    Affiche un selecteur de devise.

    Usage:
        {% currency_selector css_class="form-select" %}

    Args:
        context: Contexte du template
        css_class: Classes CSS pour le select

    Returns:
        dict: Contexte pour le template
    """
    try:
        from apps.finances.models import Currency

        currencies = Currency.objects.filter(is_active=True).order_by('code')
        current = 'EUR'

        request = context.get('request')
        if request:
            from apps.finances.currency_service import (
                get_preferred_currency_for_request
            )
            current, _ = get_preferred_currency_for_request(request)

        return {
            'currencies': currencies,
            'current_currency': current,
            'css_class': css_class,
        }
    except Exception:
        return {
            'currencies': [],
            'current_currency': 'EUR',
            'css_class': css_class,
        }


@register.inclusion_tag('finances/tags/price_display.html')
def price_display(amount, currency_code='EUR', show_converted=False,
                  convert_to='EUR'):
    """
    Affiche un prix avec formatage et conversion optionnelle.

    Usage:
        {% price_display 100 "USD" %}
        {% price_display 100 "USD" show_converted=True convert_to="EUR" %}

    Args:
        amount: Montant
        currency_code: Devise du montant
        show_converted: Afficher aussi la conversion
        convert_to: Devise cible pour conversion

    Returns:
        dict: Contexte pour le template
    """
    try:
        from apps.finances.currency_service import format_currency, convert_amount

        formatted = format_currency(amount, currency_code, include_symbol=True)

        converted_amount = None
        converted_formatted = None

        if show_converted and currency_code != convert_to:
            converted_amount, rate = convert_amount(
                amount, currency_code, convert_to
            )
            converted_formatted = format_currency(
                converted_amount, convert_to, include_symbol=True
            )

        return {
            'amount': amount,
            'currency_code': currency_code,
            'formatted': formatted,
            'show_converted': show_converted,
            'converted_amount': converted_amount,
            'converted_formatted': converted_formatted,
            'convert_to': convert_to,
        }
    except Exception:
        return {
            'amount': amount,
            'currency_code': currency_code,
            'formatted': f"{amount} {currency_code}",
            'show_converted': False,
        }
