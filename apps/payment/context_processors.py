from .models import OrganizationSubscription
from .services import SubscriptionService

def subscription_context(request):
    """
    Contexte pour ajouter les informations d'abonnement Ã  tous les templates
    """
    context = {
        'subscription': None,
        'trial_days_remaining': None,
        'subscription_status': 'none',
    }
    
    if request.user.is_authenticated:
        # Récupérer l'organisation de l'utilisateur
        organization = getattr(request.user, 'organization', None)
        
        if organization:
            # Récupérer l'abonnement
            subscription = OrganizationSubscription.objects.filter(
                organization=organization
            ).first()
            
            if subscription:
                context['subscription'] = subscription
                context['trial_days_remaining'] = subscription.days_remaining
                
                if subscription.is_trial:
                    context['subscription_status'] = 'trial'
                elif subscription.is_active:
                    context['subscription_status'] = 'active'
                else:
                    context['subscription_status'] = 'expired'
            else:
                # Créer un abonnement d'essai si aucun n'existe
                subscription = SubscriptionService.create_trial_subscription(organization)
                if subscription:
                    context['subscription'] = subscription
                    context['trial_days_remaining'] = subscription.days_remaining
                    context['subscription_status'] = 'trial'
    
    return context 
