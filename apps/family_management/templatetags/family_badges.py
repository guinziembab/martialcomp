from django import template
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

register = template.Library()

# Importation sécurisée des modèles
try:
    from apps.family_management.models import Family, FamilyMember, FamilyPaymentGroup, FamilyEvent
    FAMILY_MANAGEMENT_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.debug(f"Module family_management non disponible: {e}")
    FAMILY_MANAGEMENT_AVAILABLE = False
    Family = None
    FamilyMember = None
    FamilyPaymentGroup = None
    FamilyEvent = None


@register.simple_tag(takes_context=True)
def get_family_badge_count(context):
    """
    Calcule le nombre total d'actions familiales en attente pour l'utilisateur.
    Retourne un dictionnaire avec les différents types de badges.
    """
    default_result = {'total': 0, 'payments': 0, 'events': 0, 'notifications': 0}

    # Si le module n'est pas disponible, retourner les valeurs par défaut
    if not FAMILY_MANAGEMENT_AVAILABLE or Family is None:
        return default_result

    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return default_result

    user = request.user

    try:
        # Familles où l'utilisateur est responsable ou membre
        user_families = Family.objects.filter(
            Q(primary_responsible=user) |
            Q(members__user=user, members__is_active=True)
        ).distinct()

        if not user_families.exists():
            return default_result

        # Paiements en attente
        pending_payments = 0
        if FamilyPaymentGroup is not None:
            try:
                pending_payments = FamilyPaymentGroup.objects.filter(
                    family__in=user_families,
                    is_paid=False
                ).count()
            except Exception:
                pass

        # Événements à venir (7 prochains jours)
        upcoming_events = 0
        if FamilyEvent is not None:
            try:
                upcoming_events = FamilyEvent.objects.filter(
                    family__in=user_families,
                    start_date__gte=timezone.now(),
                    start_date__lte=timezone.now() + timedelta(days=7)
                ).count()
            except Exception:
                pass

        # Notifications non lues (placeholder)
        unread_notifications = 0

        total = pending_payments + upcoming_events + unread_notifications

        return {
            'total': total,
            'payments': pending_payments,
            'events': upcoming_events,
            'notifications': unread_notifications
        }
    except Exception as e:
        logger.warning(f"Erreur dans get_family_badge_count: {e}")
        return default_result


@register.simple_tag(takes_context=True)
def has_family_access(context):
    """
    Vérifie si l'utilisateur a accès à l'espace famille.
    """
    # Si le module n'est pas disponible
    if not FAMILY_MANAGEMENT_AVAILABLE or Family is None:
        return False

    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False

    user = request.user

    try:
        # Vérifier si l'utilisateur est responsable ou membre d'au moins une famille
        return Family.objects.filter(
            Q(primary_responsible=user) |
            Q(members__user=user, members__is_active=True)
        ).exists()
    except Exception as e:
        logger.warning(f"Erreur dans has_family_access: {e}")
        return False
