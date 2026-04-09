# competitions/api/auth_urls.py
"""
Configuration des URLs pour l'authentification et la gestion des rôles.
À inclure dans le fichier urls.py principal.
"""

from django.urls import path, include

# Importer les vues
from competitions.api.social_auth import (
    SocialAuthTokenExchangeView,
)
from competitions.views.role_switch import (
    get_available_contexts,
    switch_context,
    context_switcher_partial,
)

# Essayer d'importer les vues dj-rest-auth si disponibles
try:
    from competitions.api.social_auth import (
        GoogleLoginAPI,
        FacebookLoginAPI,
        AppleLoginAPI,
    )
    DJ_REST_AUTH_AVAILABLE = True
except ImportError:
    DJ_REST_AUTH_AVAILABLE = False


# ============================================================
# URLs API pour l'authentification
# ============================================================

auth_api_patterns = [
    # Échange de token social (fallback universel)
    path('social/token/', SocialAuthTokenExchangeView.as_view(), name='social_token'),
]

# Ajouter les endpoints dj-rest-auth si disponibles
if DJ_REST_AUTH_AVAILABLE:
    auth_api_patterns += [
        path('google/', GoogleLoginAPI.as_view(), name='google_login'),
        path('facebook/', FacebookLoginAPI.as_view(), name='facebook_login'),
        path('apple/', AppleLoginAPI.as_view(), name='apple_login'),
    ]


# ============================================================
# URLs API pour les contextes/rôles
# ============================================================

context_api_patterns = [
    # Récupérer les contextes disponibles
    path('contexts/', get_available_contexts, name='available_contexts'),
    
    # Changer de contexte
    path('contexts/switch/', switch_context, name='switch_context'),
    
    # Rendu partiel du switcher (pour AJAX)
    path('contexts/switcher/', context_switcher_partial, name='context_switcher'),
]


# ============================================================
# CONFIGURATION À AJOUTER DANS config/urls.py
# ============================================================

"""
# config/urls.py

from django.urls import path, include

urlpatterns = [
    # ... autres URLs ...
    
    # Authentification Django Allauth (web)
    path('accounts/', include('allauth.urls')),
    
    # API d'authentification (mobile)
    path('api/auth/', include(('competitions.api.auth_urls.auth_api_patterns', 'auth'), namespace='auth')),
    
    # API des contextes
    path('api/', include(('competitions.api.auth_urls.context_api_patterns', 'api'), namespace='api')),
    
    # dj-rest-auth pour JWT (si utilisé)
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]
"""


# ============================================================
# ALTERNATIVE: Fichier urls.py complet pour l'API
# ============================================================

# Si vous préférez un fichier urls.py dédié pour toute l'API:

"""
# competitions/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import des vues
from .social_auth import SocialAuthTokenExchangeView
from ..views.role_switch import get_available_contexts, switch_context

app_name = 'api'

urlpatterns = [
    # === Authentification ===
    path('auth/social/token/', SocialAuthTokenExchangeView.as_view(), name='social_token'),
    
    # === Contextes et Rôles ===
    path('contexts/', get_available_contexts, name='available_contexts'),
    path('contexts/switch/', switch_context, name='switch_context'),
    
    # === Ajouter ici d'autres endpoints API ===
    # path('members/', include('competitions.api.members_urls')),
    # path('competitions/', include('competitions.api.competitions_urls')),
]
"""


# ============================================================
# NAMESPACE POUR LES TEMPLATES
# ============================================================

# Dans les templates, utilisez les noms d'URL comme suit:
# {% url 'api:switch_context' %}
# {% url 'api:available_contexts' %}
# {% url 'auth:google_login' %}
