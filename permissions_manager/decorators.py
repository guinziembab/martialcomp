# permissions_manager/decorators.py

from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from .auth import user_has_permission

def permission_required(permission_code, context_resolver=None, login_url=None):
    """
    Décorateur pour vérifier qu'un utilisateur a une permission donnée

    Args:
        permission_code: Code de la permission requise
        context_resolver: Fonction qui extrait le contexte à partir de la requête/vue
                        (par exemple lambda request, *args, **kwargs: get_object_or_404(Club, pk=kwargs['pk']))
        login_url: URL de redirection si non connecté
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Si l'utilisateur n'est pas connecté, rediriger
            if not request.user.is_authenticated:
                if login_url:
                    return redirect(login_url)
                return redirect(f"{reverse('login')}?next={request.path}")

            # Déterminer le contexte si un resolver est fourni
            context = None
            if context_resolver:
                context = context_resolver(request, *args, **kwargs)

            # Vérifier la permission
            if user_has_permission(request.user, permission_code, context):
                return view_func(request, *args, **kwargs)

            # Permission refusée
            raise PermissionDenied("Vous n'avez pas les permissions requises.")

        return _wrapped_view
    return decorator