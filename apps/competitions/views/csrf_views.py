"""
Vues pour la gestion des erreurs CSRF et le rafraîchissement des jetons.
"""
import logging
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
@require_GET
def refresh_csrf_token(request):
    """
    Vue pour rafraîchir le jeton CSRF.
    Retourne un nouveau jeton CSRF en JSON.
    """
    try:
        csrf_token = get_token(request)
        return JsonResponse({
            'success': True,
            'csrfToken': csrf_token,
            'message': _('Jeton CSRF rafraîchi avec succès')
        })
    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement du jeton CSRF: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': _('Erreur lors du rafraîchissement du jeton CSRF')
        }, status=500)

def csrf_failure(request, reason=""):
    """
    Vue personnalisée pour les erreurs CSRF.
    Affiche une page d'erreur conviviale avec des instructions pour résoudre le problème.
    """
    context = {
        'reason': reason,
        'error_title': _('Erreur de sécurité (CSRF)'),
        'error_message': _('Votre session a expiré ou une erreur de sécurité s\'est produite.'),
        'solutions': [
            _('Rafraîchissez la page et réessayez'),
            _('Videz le cache de votre navigateur'),
            _('Supprimez les cookies du site et reconnectez-vous'),
            _('Désactivez temporairement les bloqueurs de publicité'),
            _('Essayez en navigation privée/incognito')
        ],
        'technical_reason': reason
    }
    
    logger.warning(f"Erreur CSRF pour l'utilisateur {request.user}: {reason}")
    
    return render(request, 'competitions/errors/csrf_failure.html', context, status=403)

@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Vue simple pour obtenir un jeton CSRF.
    Utile pour les requêtes AJAX.
    """
    return JsonResponse({
        'csrfToken': get_token(request)
    })

def test_csrf(request):
    """
    Vue de test pour la gestion CSRF.
    Affiche une page avec des formulaires et tests AJAX.
    """
    context = {}
    
    if request.method == 'POST':
        test_field = request.POST.get('test_field', '')
        messages.success(request, _(f'Formulaire soumis avec succès ! Valeur : "{test_field}"'))
        logger.info(f"Test CSRF réussi pour l'utilisateur {request.user}: {test_field}")
    
    return render(request, 'competitions/test_csrf.html', context)
