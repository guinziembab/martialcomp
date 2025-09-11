# permissions_manager/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.http import HttpResponseForbidden
from .models import Permission

class PermissionsMiddleware(MiddlewareMixin):
    """
    Middleware pour vérifier les permissions sur certaines URLs

    Ce middleware peut Ãªtre utilisé pour définir des règles de permissions
    basées sur les patterns d'URL plutÃ´t que sur les vues individuelles.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Charger les règles d'URL ici
        self.url_permission_rules = {
            # 'url_name': 'permission_code',
            'federation_edit': 'federation.edit',
            'club_edit': 'club.edit',
            'judge_edit': 'judge.edit',
            # etc.
        }

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated:
            return None  # Géré par les décorateurs login_required

        # Récupérer le nom de l'URL
        url_name = resolve(request.path_info).url_name

        # Vérifier si une règle s'applique Ã  cette URL
        if url_name in self.url_permission_rules:
            permission_code = self.url_permission_rules[url_name]

            # Trouver le contexte (éventuellement dans view_kwargs)
            context = None
            # Logique pour déterminer le contexte Ã  partir de l'URL

            from .auth import user_has_permission
            if not user_has_permission(request.user, permission_code, context):
                return HttpResponseForbidden("Accès refusé")

        return None  # Continuer le traitement
