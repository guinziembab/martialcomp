from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token
from django.utils.translation import gettext as _
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@requires_csrf_token
def csrf_failure(request, reason=""):
    """
    Vue personnalisée pour les erreurs CSRF
    """
    context = {
        'title': _('Erreur de sécurité (CSRF)'),
        'message': _('Votre session a expiré ou une erreur de sécurité s\'est produite.'),
        'reason': reason,
        'suggestions': [
            _('RafraÃ®chissez la page et réessayez'),
            _('Videz le cache de votre navigateur'),
            _('Supprimez les cookies du site et reconnectez-vous'),
            _('Désactivez temporairement les bloqueurs de publicité'),
            _('Essayez en navigation privée/incognito'),
        ]
    }
    
    return render(request, 'competitions/errors/csrf_failure.html', context, status=403)
