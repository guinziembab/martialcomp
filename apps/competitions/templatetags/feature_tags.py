"""
Template tags pour le contrÃ´le d'affichage des fonctionnalités par abonnement.
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.urls import reverse

from apps.competitions.utils.feature_control import (
    has_feature,
    get_user_organization,
    get_organization_subscription,
    check_usage_limits,
    get_available_features
)

register = template.Library()


@register.filter
def has_feature_access(user, feature_name):
    """
    Template filter pour vérifier l'accès Ã  une fonctionnalité.
    
    Usage: {% if user|has_feature_access:"combat_system" %}
    """
    if not user or not user.is_authenticated:
        return False
    return has_feature(user, feature_name)


@register.simple_tag
def feature_enabled(user, feature_name):
    """
    Template tag pour vérifier l'accès Ã  une fonctionnalité.
    
    Usage: {% feature_enabled user "combat_system" as combat_enabled %}
    """
    if not user or not user.is_authenticated:
        return False
    return has_feature(user, feature_name)


@register.inclusion_tag('competitions/includes/feature_gate.html')
def feature_gate(user, feature_name, upgrade_text=None, upgrade_url=None):
    """
    Inclusion tag pour afficher un message de mise Ã  niveau si la fonctionnalité n'est pas disponible.
    
    Usage: {% feature_gate user "combat_system" %}
    """
    has_access = has_feature(user, feature_name) if user and user.is_authenticated else False
    
    context = {
        'has_access': has_access,
        'feature_name': feature_name,
        'upgrade_text': upgrade_text or _('Cette fonctionnalité nécessite un abonnement supérieur'),
        'upgrade_url': upgrade_url or reverse('upgrade_required') if has_access else '#'
    }
    
    return context


@register.inclusion_tag('competitions/includes/subscription_status.html')
def subscription_status(user):
    """
    Inclusion tag pour afficher le statut de l'abonnement.
    
    Usage: {% subscription_status user %}
    """
    if not user or not user.is_authenticated:
        return {'subscription': None}
    
    organization = get_user_organization(user)
    subscription = get_organization_subscription(organization) if organization else None
    
    context = {
        'subscription': subscription,
        'organization': organization
    }
    
    return context


@register.simple_tag
def usage_limits(user, limit_type):
    """
    Template tag pour récupérer les limites d'utilisation.
    
    Usage: {% usage_limits user "members" as member_limits %}
    """
    if not user or not user.is_authenticated:
        return {'allowed': False, 'current': 0, 'limit': 0, 'remaining': 0}
    
    organization = get_user_organization(user)
    if not organization:
        return {'allowed': False, 'current': 0, 'limit': 0, 'remaining': 0}
    
    return check_usage_limits(organization, limit_type)


@register.inclusion_tag('competitions/includes/usage_meter.html')
def usage_meter(user, limit_type, show_label=True):
    """
    Inclusion tag pour afficher un indicateur d'utilisation.
    
    Usage: {% usage_meter user "members" %}
    """
    limits = usage_limits(user, limit_type)
    
    # Calculer le pourcentage d'utilisation
    if limits['limit'] > 0:
        percentage = (limits['current'] / limits['limit']) * 100
    else:
        percentage = 0
    
    # Déterminer la couleur selon le pourcentage
    if percentage < 70:
        color_class = 'success'
    elif percentage < 90:
        color_class = 'warning'
    else:
        color_class = 'danger'
    
    context = {
        'limits': limits,
        'percentage': percentage,
        'color_class': color_class,
        'limit_type': limit_type,
        'show_label': show_label
    }
    
    return context


@register.simple_tag
def available_features(user):
    """
    Template tag pour récupérer toutes les fonctionnalités disponibles.
    
    Usage: {% available_features user as features %}
    """
    if not user or not user.is_authenticated:
        return []
    
    return get_available_features(user)


@register.filter
def subscription_tier_name(user):
    """
    Template filter pour récupérer le nom du tier d'abonnement.
    
    Usage: {{ user|subscription_tier_name }}
    """
    if not user or not user.is_authenticated:
        return _('Non connecté')
    
    organization = get_user_organization(user)
    subscription = get_organization_subscription(organization) if organization else None
    
    if subscription:
        return subscription.subscription_tier.display_name
    
    return _('Aucun abonnement')


@register.inclusion_tag('competitions/includes/feature_comparison.html')
def feature_comparison(user, features_list):
    """
    Inclusion tag pour afficher une comparaison de fonctionnalités.
    
    Usage: {% feature_comparison user features_list %}
    """
    if not user or not user.is_authenticated:
        return {'comparison': []}
    
    available = get_available_features(user)
    
    comparison = []
    for feature in features_list:
        comparison.append({
            'name': feature,
            'available': feature in available,
            'display_name': feature.replace('_', ' ').title()
        })
    
    return {'comparison': comparison}


@register.simple_tag
def subscription_upgrade_url(current_tier=None, target_tier=None):
    """
    Template tag pour générer l'URL de mise Ã  niveau d'abonnement.
    
    Usage: {% subscription_upgrade_url current_tier target_tier %}
    """
    try:
        if target_tier:
            return reverse('upgrade_subscription', kwargs={'tier': target_tier})
        else:
            return reverse('upgrade_required')
    except:
        return '#'


@register.inclusion_tag('competitions/includes/tier_badge.html')
def tier_badge(user, show_trial=True):
    """
    Inclusion tag pour afficher un badge du tier d'abonnement.
    
    Usage: {% tier_badge user %}
    """
    if not user or not user.is_authenticated:
        return {'tier': None, 'is_trial': False}
    
    organization = get_user_organization(user)
    subscription = get_organization_subscription(organization) if organization else None
    
    context = {
        'tier': subscription.subscription_tier if subscription else None,
        'is_trial': subscription.is_trial if subscription else False,
        'show_trial': show_trial
    }
    
    return context


@register.simple_tag
def feature_help_text(feature_name):
    """
    Template tag pour récupérer le texte d'aide d'une fonctionnalité.
    
    Usage: {% feature_help_text "combat_system" %}
    """
    try:
        from apps.finances.models.subscription import FeatureFlag
        feature = FeatureFlag.objects.get(name=feature_name, is_active=True)
        return feature.description
    except:
        return ""


@register.inclusion_tag('competitions/includes/feature_unlock_button.html')
def feature_unlock_button(user, feature_name, button_text=None, css_class="btn btn-primary"):
    """
    Inclusion tag pour afficher un bouton de déverrouillage de fonctionnalité.
    
    Usage: {% feature_unlock_button user "combat_system" %}
    """
    has_access = has_feature(user, feature_name) if user and user.is_authenticated else False
    
    context = {
        'has_access': has_access,
        'feature_name': feature_name,
        'button_text': button_text or _('Débloquer cette fonctionnalité'),
        'css_class': css_class,
        'upgrade_url': reverse('upgrade_required')
    }
    
    return context


@register.filter
def feature_icon(feature_name):
    """
    Template filter pour récupérer l'icÃ´ne d'une fonctionnalité.
    
    Usage: {{ "combat_system"|feature_icon }}
    """
    icons = {
        'combat_system': 'fas fa-fist-raised',
        'scoring_system': 'fas fa-chart-line',
        'competitions': 'fas fa-trophy',
        'practitioner_management': 'fas fa-users',
        'financial': 'fas fa-euro-sign',
        'ecommerce': 'fas fa-shopping-cart',
        'communications': 'fas fa-envelope',
        'documents_ged': 'fas fa-file-alt',
        'family_management': 'fas fa-home',
        'events_planning': 'fas fa-calendar',
        'qr_mobile': 'fas fa-qrcode',
        'analytics_reporting': 'fas fa-analytics'
    }
    
    return icons.get(feature_name, 'fas fa-star')


@register.simple_tag
def render_feature_card(feature_name, user=None):
    """
    Template tag pour rendre une carte de fonctionnalité.
    
    Usage: {% render_feature_card "combat_system" user %}
    """
    try:
        from apps.finances.models.subscription import FeatureFlag
        feature = FeatureFlag.objects.get(name=feature_name, is_active=True)
        
        has_access = has_feature(user, feature_name) if user and user.is_authenticated else False
        
        return mark_safe(f'''
        <div class="feature-card {'available' if has_access else 'locked'}">
            <div class="feature-icon">
                <i class="{feature_icon(feature_name)}"></i>
            </div>
            <h5>{feature.display_name}</h5>
            <p>{feature.description}</p>
            <div class="feature-status">
                {'âœ… Disponible' if has_access else 'ðŸ”’ Nécessite un upgrade'}
            </div>
        </div>
        ''')
    except:
        return ""

