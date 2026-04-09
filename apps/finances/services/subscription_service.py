"""
Service centralisé pour les informations d'abonnement.
Fournit un dict réutilisable dans les vues, templates et API.
Inclut la synchronisation de quantité Stripe (per-seat billing).
"""
import logging
from django.urls import reverse

logger = logging.getLogger(__name__)


def sync_stripe_member_count(organization):
    """
    Synchronise le nombre de membres actifs avec Stripe.
    Appelé après chaque ajout/suppression de membre sur un org premium.

    Ne fait rien si l'org est en Free ou n'a pas de subscription Stripe.
    Échoue silencieusement (log warning) pour ne pas bloquer le flow.
    """
    from apps.competitions.utils.feature_control import (
        get_organization_subscription,
    )
    from apps.competitions.models import Practitioner
    from apps.finances.services.stripe_service import (
        StripeService, StripeServiceError,
    )

    try:
        subscription = get_organization_subscription(organization)
        if not subscription:
            return
        if not subscription.stripe_subscription_id:
            return

        tier = subscription.subscription_tier
        if tier and tier.name == 'free':
            return

        # Count current active members
        members_count = Practitioner.objects.filter(
            organization=organization,
            is_active=True,
        ).count()

        if members_count < 1:
            members_count = 1

        StripeService.update_subscription_quantity(
            subscription.stripe_subscription_id,
            members_count,
        )
        logger.info(
            "Stripe quantity synced: org=%s, members=%d",
            organization.pk, members_count,
        )
    except StripeServiceError as e:
        logger.warning(
            "Failed to sync Stripe quantity for org %s: %s",
            organization.pk, e,
        )
    except Exception as e:
        logger.warning(
            "Unexpected error syncing Stripe quantity for org %s: %s",
            organization.pk, e,
        )


def get_subscription_info(organization):
    """
    Retourne un dict avec toutes les infos d'abonnement pour l'UI.

    Args:
        organization: Instance de Club ou Organization

    Returns:
        dict avec: tier_name, is_free, members_count, max_members,
                   can_add_member, remaining_slots, is_at_limit,
                   pricing, upgrade_url
    """
    from apps.competitions.utils.feature_control import (
        get_organization_subscription,
    )
    from apps.competitions.models import Practitioner

    default = {
        'tier_name': 'free',
        'display_name': 'Free',
        'is_free': True,
        'members_count': 0,
        'max_members': 10,
        'can_add_member': True,
        'remaining_slots': 10,
        'is_at_limit': False,
        'is_near_limit': False,
        'pricing': None,
        'upgrade_url': reverse('upgrade_required'),
    }

    if not organization:
        return default

    try:
        subscription = get_organization_subscription(organization)
        if not subscription:
            return default

        # Compter les membres actifs
        members_count = Practitioner.objects.filter(
            organization=organization,
            is_active=True,
        ).count()

        # Mettre à jour le compteur sur la subscription
        subscription.current_members_count = members_count
        subscription.save(update_fields=['current_members_count'])

        tier = subscription.subscription_tier
        tier_name = tier.name if tier else 'free'
        max_members = tier.max_members if tier else 10
        is_free = tier_name == 'free'
        can_add = members_count < max_members
        remaining = max(0, max_members - members_count)

        # Pricing effectif
        pricing = None
        try:
            pricing = subscription.effective_pricing
        except Exception as e:
            logger.warning(f"Erreur calcul pricing: {e}")

        return {
            'tier_name': tier_name,
            'display_name': tier.display_name if tier else 'Free',
            'is_free': is_free,
            'members_count': members_count,
            'max_members': max_members,
            'can_add_member': can_add,
            'remaining_slots': remaining,
            'is_at_limit': remaining == 0 and is_free,
            'is_near_limit': remaining <= 2 and is_free and remaining > 0,
            'pricing': pricing,
            'upgrade_url': reverse('upgrade_required'),
        }

    except Exception as e:
        logger.error(f"Erreur get_subscription_info: {e}")
        return default
