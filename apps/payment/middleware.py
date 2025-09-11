from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from .models import OrganizationSubscription
from .services import SubscriptionService

class SubscriptionMiddleware:
    """
    Middleware pour vérifier le statut de l'abonnement
    et rediriger les utilisateurs si nécessaire
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs exemptées de la vérification d'abonnement
        exempt_urls = [
            '/payment/',
            '/admin/',
            '/accounts/',
            '/static/',
            '/media/',
            '/api/',
            '/favicon.ico',
        ]
        
        # Vérifier si l'URL actuelle est exemptée
        current_path = request.path
        is_exempt = any(current_path.startswith(url) for url in exempt_urls)
        
        if not is_exempt and request.user.is_authenticated:
            # Récupérer l'organisation de l'utilisateur
            organization = getattr(request.user, 'organization', None)
            
            if organization:
                # Vérifier l'abonnement
                subscription = OrganizationSubscription.objects.filter(
                    organization=organization
                ).first()
                
                if not subscription:
                    # Créer un abonnement d'essai si aucun n'existe
                    subscription = SubscriptionService.create_trial_subscription(organization)
                
                # Vérifier si l'abonnement est expiré
                if subscription and not subscription.is_active and not subscription.is_trial:
                    # Rediriger vers la page de renouvellement
                    if not current_path.startswith('/payment/'):
                        messages.warning(
                            request,
                            'Votre abonnement a expiré. Veuillez le renouveler pour continuer.'
                        )
                        return redirect('payment:subscription_plans')
                
                # Vérifier si l'essai est sur le point d'expirer (7 jours avant)
                if subscription and subscription.is_trial and subscription.days_remaining <= 7:
                    if not current_path.startswith('/payment/'):
                        messages.info(
                            request,
                            f'Votre essai gratuit se termine dans {subscription.days_remaining} jours. '
                            'Pensez Ã  choisir un plan pour continuer.'
                        )

        response = self.get_response(request)
        return response 
