from django.core.exceptions import PermissionDenied
"""
Utilitaires pour gérer le CSRF dans un environnement multi-tenant
"""

from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Force la génération d'un token CSRF pour la requÃªte
    """
    token = get_token(request)
    return {'csrf_token': token}

