from django.core.exceptions import PermissionDenied
# competitions/views/onboarding_redirect.py

from django.shortcuts import redirect
from django.views import View
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging

logger = logging.getLogger(__name__)

class OnboardingRedirectView(View):
    """
    Vue simple qui redirige toutes les requÃªtes vers le bon chemin d'onboarding.
    Cette vue est conçue pour intercepter les anciennes URL et les rediriger vers
    les nouvelles URL avec le préfixe /competitions/.
    """
    
    def get(self, request, *args, **kwargs):
        # Récupérer le suffixe d'URL si spécifié
        suffix = kwargs.get('suffix', 'role')
        
        # Construire l'URL de redirection
        redirect_url = f'/competitions/onboarding/{suffix}/'
        
        # Log la redirection
        logger.info(f"OnboardingRedirectView: Redirection de {request.path} vers {redirect_url}")
        
        # Rediriger vers le bon chemin
        return redirect(redirect_url)

    # Supporter également les requÃªtes POST
    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
