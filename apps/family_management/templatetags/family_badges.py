from django import template
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from apps.family_management.models import Family, FamilyMember, FamilyPaymentGroup, FamilyEvent

register = template.Library()

@register.simple_tag(takes_context=True)
def get_family_badge_count(context):
    """
    Calcule le nombre total d'actions familiales en attente pour l'utilisateur.
    Retourne un dictionnaire avec les différents types de badges.
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return {'total': 0, 'payments': 0, 'events': 0, 'notifications': 0}
    
    user = request.user
    
    # Familles oÃ¹ l'utilisateur est responsable ou membre
    user_families = Family.objects.filter(
        Q(primary_responsible=user) | 
        Q(members__user=user, members__is_active=True)
    ).distinct()
    
    if not user_families.exists():
        return {'total': 0, 'payments': 0, 'events': 0, 'notifications': 0}
    
    # Paiements en attente
    pending_payments = FamilyPaymentGroup.objects.filter(
        family__in=user_families,
        is_paid=False
    ).count()
    
    # Ã‰vénements Ã  venir (7 prochains jours)
    upcoming_events = FamilyEvent.objects.filter(
        family__in=user_families,
        start_date__gte=timezone.now(),
        start_date__lte=timezone.now() + timedelta(days=7)
    ).count()
    
    # Notifications non lues (placeholder - Ã  implémenter selon votre système)
    unread_notifications = 0  # Ã€ adapter selon votre système de notifications
    
    total = pending_payments + upcoming_events + unread_notifications
    
    return {
        'total': total,
        'payments': pending_payments,
        'events': upcoming_events,
        'notifications': unread_notifications
    }

@register.simple_tag(takes_context=True)
def has_family_access(context):
    """
    Vérifie si l'utilisateur a accès Ã  l'espace famille.
    """
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
    
    user = request.user
    
    # Vérifier si l'utilisateur est responsable ou membre d'au moins une famille
    return Family.objects.filter(
        Q(primary_responsible=user) | 
        Q(members__user=user, members__is_active=True)
    ).exists() 

