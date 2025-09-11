from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.urls import reverse
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging

logger = logging.getLogger(__name__)

@csrf_protect
@require_http_methods(["POST"])
def ajax_login_view(request):
    """Vue de connexion AJAX pour éviter les problèmes CSRF de redirection"""
    
    # Debug CSRF
    logger.warning(f'AJAX Login - CSRF token reçu: {request.POST.get("csrfmiddlewaretoken", "MANQUANT")}')
    logger.warning(f'AJAX Login - User-Agent: {request.META.get("HTTP_USER_AGENT", "N/A")}')
    logger.warning(f'AJAX Login - Referer: {request.META.get("HTTP_REFERER", "N/A")}')
    
    username = request.POST.get('login', '')
    password = request.POST.get('password', '')
    
    if not username or not password:
        return JsonResponse({
            'success': False,
            'error': _("Veuillez remplir tous les champs."),
            'redirect': None
        })
    
    user = authenticate(request, username=username, password=password)
    
    if user is None:
        logger.warning(f'AJAX Login - Ã‰chec authentification pour: {username}')
        return JsonResponse({
            'success': False,
            'error': _("Nom d'utilisateur ou mot de passe incorrect."),
            'redirect': None
        })
        
    if not user.is_active:
        return JsonResponse({
            'success': False,
            'error': _("Votre compte est désactivé."),
            'redirect': None
        })
    
    # Connexion réussie
    login(request, user)
    logger.warning(f'AJAX Login - Connexion réussie pour: {username}')
    
    # Déterminer la redirection selon le rÃ´le
    try:
        from apps.competitions.models.users import UserProfile
        profile = UserProfile.objects.get(user=user)
        
        if profile.onboarding_completed:
            role_map_names = {
                'manager': 'competitions:dashboard:manager',
                'club_manager': 'competitions:dashboard:club',
                'participant': 'competitions:dashboard:participant',
                'coach': 'competitions:dashboard:coach',
                'referee': 'competitions:dashboard:referee',
                'external_organizer': 'competitions:dashboard:external_organizer',
                'spectator': 'competitions:dashboard:spectator'
            }
            role_key = str(profile.role).lower().strip()
            if role_key == 'federation_admin':
                from apps.competitions.models import Federation
                federation = Federation.objects.filter(owner=user).first() or Federation.objects.filter(administrators__user=user).first()
                if federation:
                    redirect_url = reverse('competitions:federations:federation_dashboard', kwargs={'federation_id': federation.id})
                else:
                    redirect_url = reverse('competitions:federations:list')
            else:
                redirect_url = reverse(role_map_names.get(role_key, 'competitions:dashboard:spectator'))
        else:
            # Redirection onboarding
            redirect_url = reverse('competitions:onboarding:role_selection')
            
    except Exception as e:
        logger.error(f'AJAX Login - Erreur récupération profil: {e}')
        # Fallback vers spectator
        redirect_url = reverse('competitions:dashboard:spectator')
    
    return JsonResponse({
        'success': True,
        'error': None,
        'redirect': redirect_url,
        'message': _("Connexion réussie !")
    })

