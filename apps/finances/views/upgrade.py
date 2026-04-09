"""
Vue pour la page de mise à niveau (upgrade) de l'abonnement.
"""
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.finances.services.subscription_service import get_subscription_info
from apps.finances.pricing_tiers import (
    get_market_tier_for_country, get_price_for_country, MARKET_TIER_MATURE,
)
from apps.competitions.utils.feature_control import get_user_organization


@login_required
def upgrade_required_view(request):
    """Affiche la page de comparaison Free vs Premium."""
    organization = get_user_organization(request.user)
    info = get_subscription_info(organization)

    # Calculate total price for Stripe button
    members_count = info.get('members_count', 1) or 1
    country = ''
    if organization:
        country = getattr(organization, 'country', '') or ''
    price_per_member = get_price_for_country(country, 'yearly')
    total_price = price_per_member * members_count

    # Check if Stripe is configured for this market
    market_tier = get_market_tier_for_country(country)
    if market_tier == MARKET_TIER_MATURE:
        stripe_configured = bool(
            getattr(settings, 'STRIPE_PRICE_MATURE_YEARLY', '')
        )
    else:
        stripe_configured = bool(
            getattr(settings, 'STRIPE_PRICE_EMERGENT_YEARLY', '')
        )

    context = {
        'subscription_info': info,
        'page_title': _("Passer à Premium"),
        'members_count': members_count,
        'price_per_member': price_per_member,
        'total_price': total_price,
        'stripe_configured': stripe_configured,
    }
    return render(request, 'finances/upgrade_required.html', context)
