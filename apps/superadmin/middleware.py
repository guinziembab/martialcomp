# -*- coding: utf-8 -*-
"""
Middleware pour Super Admin WebSocket.
"""

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from urllib.parse import parse_qs


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    Middleware d'authentification pour les WebSockets.
    Utilise le token de session ou un token d'API.
    """

    async def __call__(self, scope, receive, send):
        # Récupérer l'utilisateur depuis la session
        if 'user' not in scope or scope['user'] is None:
            scope['user'] = await self.get_user_from_scope(scope)

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user_from_scope(self, scope):
        """Récupérer l'utilisateur depuis le scope."""
        from django.contrib.auth import get_user_model
        from django.contrib.sessions.models import Session

        User = get_user_model()

        # Essayer de récupérer depuis les cookies
        headers = dict(scope.get('headers', []))
        cookie_header = headers.get(b'cookie', b'').decode()

        if cookie_header:
            # Parser les cookies
            cookies = {}
            for item in cookie_header.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value

            session_key = cookies.get('sessionid')
            if session_key:
                try:
                    session = Session.objects.get(session_key=session_key)
                    session_data = session.get_decoded()
                    user_id = session_data.get('_auth_user_id')
                    if user_id:
                        return User.objects.get(pk=user_id)
                except (Session.DoesNotExist, User.DoesNotExist):
                    pass

        # Essayer avec un token dans la query string
        query_string = scope.get('query_string', b'').decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            # Vérifier le token (implémentation basique)
            # En production, utiliser un système de token plus robuste
            try:
                from django.core.signing import Signer
                signer = Signer()
                user_id = signer.unsign(token)
                return User.objects.get(pk=user_id)
            except Exception:
                pass

        return AnonymousUser()


def get_websocket_application():
    """
    Retourne l'application ASGI configurée pour les WebSockets.
    À utiliser dans asgi.py.
    """
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    from django.core.asgi import get_asgi_application
    from apps.superadmin.routing import websocket_urlpatterns

    return ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            WebSocketAuthMiddleware(
                URLRouter(websocket_urlpatterns)
            )
        ),
    })
