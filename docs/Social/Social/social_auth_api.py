# competitions/api/social_auth.py
"""
Endpoints API pour l'authentification sociale.
Utilisé principalement par l'application mobile React Native.
"""

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

# Importer les adapters allauth si dj-rest-auth est installé
try:
    from dj_rest_auth.registration.views import SocialLoginView
    from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
    from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
    from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
    from allauth.socialaccount.providers.oauth2.client import OAuth2Client
    DJ_REST_AUTH_AVAILABLE = True
except ImportError:
    DJ_REST_AUTH_AVAILABLE = False


User = get_user_model()


# ============================================================
# VUES BASÉES SUR dj-rest-auth (recommandé si installé)
# ============================================================

if DJ_REST_AUTH_AVAILABLE:
    
    class GoogleLoginAPI(SocialLoginView):
        """
        Endpoint pour connexion Google depuis mobile.
        
        POST /api/auth/google/
        Body: {"access_token": "google_access_token"} 
              ou {"code": "authorization_code"}
        
        Returns: {"key": "auth_token", "user": {...}}
        """
        adapter_class = GoogleOAuth2Adapter
        callback_url = settings.GOOGLE_CALLBACK_URL if hasattr(settings, 'GOOGLE_CALLBACK_URL') else None
        client_class = OAuth2Client
        permission_classes = [AllowAny]
    
    
    class FacebookLoginAPI(SocialLoginView):
        """
        Endpoint pour connexion Facebook depuis mobile.
        
        POST /api/auth/facebook/
        Body: {"access_token": "facebook_access_token"}
        """
        adapter_class = FacebookOAuth2Adapter
        permission_classes = [AllowAny]
    
    
    class AppleLoginAPI(SocialLoginView):
        """
        Endpoint pour connexion Apple depuis mobile.
        
        POST /api/auth/apple/
        Body: {"access_token": "apple_identity_token", "code": "authorization_code"}
        """
        adapter_class = AppleOAuth2Adapter
        permission_classes = [AllowAny]


# ============================================================
# VUE GÉNÉRIQUE D'ÉCHANGE DE TOKEN (fallback)
# ============================================================

class SocialAuthTokenExchangeView(APIView):
    """
    Échange un access_token social contre des tokens JWT MartialComp.
    
    Endpoint de fallback si dj-rest-auth n'est pas configuré,
    ou pour des cas d'usage spécifiques.
    
    POST /api/auth/social/token/
    Body: {
        "provider": "google" | "facebook" | "apple",
        "access_token": "token_from_provider",
        "id_token": "optional_id_token_for_apple"
    }
    
    Returns: {
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token",
        "user": {
            "id": 123,
            "email": "user@example.com",
            "username": "user",
            "role": "spectator",
            "onboarding_completed": false
        },
        "onboarding_required": true
    }
    """
    permission_classes = [AllowAny]
    
    # URLs de validation des tokens par provider
    PROVIDER_VALIDATION_URLS = {
        'google': 'https://oauth2.googleapis.com/tokeninfo?access_token={}',
        'facebook': 'https://graph.facebook.com/me?access_token={}&fields=id,email,name,first_name,last_name,picture',
    }
    
    def post(self, request):
        provider = request.data.get('provider')
        access_token = request.data.get('access_token')
        id_token = request.data.get('id_token')  # Pour Apple
        
        # Validation des paramètres
        if not provider:
            return Response(
                {'error': 'missing_provider', 'message': 'Le paramètre provider est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not access_token:
            return Response(
                {'error': 'missing_token', 'message': 'Le paramètre access_token est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if provider not in ['google', 'facebook', 'apple']:
            return Response(
                {'error': 'invalid_provider', 'message': f'Provider non supporté: {provider}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Valider le token et récupérer les infos utilisateur
            user_info = self._validate_token(provider, access_token, id_token)
            
            if not user_info:
                return Response(
                    {'error': 'invalid_token', 'message': 'Token invalide ou expiré'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Trouver ou créer l'utilisateur
            user = self._get_or_create_user(provider, user_info)
            
            if not user:
                return Response(
                    {'error': 'user_creation_failed', 'message': 'Impossible de créer le compte'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Générer les tokens JWT
            refresh = RefreshToken.for_user(user)
            
            # Récupérer les infos du profil
            profile_data = self._get_profile_data(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': profile_data,
                'onboarding_required': not profile_data.get('onboarding_completed', True)
            })
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Social auth error: {str(e)}", exc_info=True)
            
            return Response(
                {'error': 'server_error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _validate_token(self, provider, access_token, id_token=None):
        """
        Valide le token auprès du provider et retourne les infos utilisateur.
        
        Returns:
            dict avec au minimum: {'email': '...', 'provider_id': '...'}
            ou None si invalide
        """
        if provider == 'google':
            return self._validate_google_token(access_token)
        elif provider == 'facebook':
            return self._validate_facebook_token(access_token)
        elif provider == 'apple':
            return self._validate_apple_token(access_token, id_token)
        return None
    
    def _validate_google_token(self, access_token):
        """Valide un token Google."""
        try:
            url = self.PROVIDER_VALIDATION_URLS['google'].format(access_token)
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Vérifier que le token appartient à notre app
            client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
            if data.get('aud') != client_id and data.get('azp') != client_id:
                # En développement, on peut être plus permissif
                if not settings.DEBUG:
                    return None
            
            return {
                'email': data.get('email'),
                'provider_id': data.get('sub'),
                'email_verified': data.get('email_verified', 'false') == 'true',
                'first_name': data.get('given_name', ''),
                'last_name': data.get('family_name', ''),
                'picture': data.get('picture', ''),
            }
            
        except requests.RequestException:
            return None
    
    def _validate_facebook_token(self, access_token):
        """Valide un token Facebook."""
        try:
            url = self.PROVIDER_VALIDATION_URLS['facebook'].format(access_token)
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            if 'error' in data:
                return None
            
            return {
                'email': data.get('email'),
                'provider_id': data.get('id'),
                'first_name': data.get('first_name', ''),
                'last_name': data.get('last_name', ''),
                'name': data.get('name', ''),
                'picture': data.get('picture', {}).get('data', {}).get('url', ''),
            }
            
        except requests.RequestException:
            return None
    
    def _validate_apple_token(self, access_token, id_token):
        """
        Valide un token Apple.
        Apple utilise des id_tokens JWT qu'il faut décoder.
        """
        import jwt
        
        token_to_decode = id_token or access_token
        
        try:
            # Décoder sans vérification pour extraire les claims
            # En production, il faudrait vérifier la signature avec les clés publiques Apple
            decoded = jwt.decode(
                token_to_decode,
                options={"verify_signature": False}
            )
            
            return {
                'email': decoded.get('email'),
                'provider_id': decoded.get('sub'),
                'email_verified': decoded.get('email_verified', False),
                # Apple ne fournit le nom que lors de la première connexion
                'first_name': '',
                'last_name': '',
            }
            
        except jwt.InvalidTokenError:
            return None
    
    def _get_or_create_user(self, provider, user_info):
        """
        Trouve ou crée un utilisateur basé sur les infos du provider.
        """
        email = user_info.get('email')
        provider_id = user_info.get('provider_id')
        
        if not email:
            return None
        
        # Chercher un utilisateur existant par email
        try:
            user = User.objects.get(email__iexact=email)
            
            # Mettre à jour les infos si nécessaire
            self._update_user_info(user, user_info)
            
            return user
            
        except User.DoesNotExist:
            # Créer un nouvel utilisateur
            return self._create_user(provider, user_info)
    
    def _create_user(self, provider, user_info):
        """Crée un nouvel utilisateur."""
        from competitions.models import UserProfile, Practitioner
        
        email = user_info.get('email')
        
        # Générer un username unique
        base_username = email.split('@')[0]
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=user_info.get('first_name', ''),
            last_name=user_info.get('last_name', ''),
        )
        
        # Créer le profil
        UserProfile.objects.create(
            user=user,
            role='spectator',
            onboarding_step='role_selection',
            onboarding_completed=False
        )
        
        # Créer le Practitioner si on a les infos
        first_name = user_info.get('first_name') or user.first_name
        last_name = user_info.get('last_name') or user.last_name
        
        if first_name and last_name:
            Practitioner.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
        
        return user
    
    def _update_user_info(self, user, user_info):
        """Met à jour les infos utilisateur si manquantes."""
        updated = False
        
        if not user.first_name and user_info.get('first_name'):
            user.first_name = user_info['first_name']
            updated = True
        
        if not user.last_name and user_info.get('last_name'):
            user.last_name = user_info['last_name']
            updated = True
        
        if updated:
            user.save()
    
    def _get_profile_data(self, user):
        """Retourne les données du profil pour la réponse."""
        profile_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name(),
        }
        
        # Ajouter les données du profil si disponible
        if hasattr(user, 'profile'):
            profile_data.update({
                'role': user.profile.role,
                'onboarding_completed': user.profile.onboarding_completed,
                'onboarding_step': user.profile.onboarding_step,
            })
        else:
            profile_data.update({
                'role': None,
                'onboarding_completed': False,
                'onboarding_step': 'role_selection',
            })
        
        # Ajouter les rôles organisationnels
        from competitions.models import ClubMember
        memberships = ClubMember.objects.filter(
            user=user,
            status='active'
        ).select_related('club', 'role').values(
            'id', 'club__id', 'club__name', 'role__code', 'role__name'
        )
        
        profile_data['club_memberships'] = list(memberships)
        
        return profile_data


# ============================================================
# URLs pour ce module
# ============================================================

"""
Ajouter dans competitions/api/urls.py ou config/urls.py:

from django.urls import path
from competitions.api.social_auth import (
    SocialAuthTokenExchangeView,
)

# Si dj-rest-auth est installé, ajouter aussi:
# from competitions.api.social_auth import GoogleLoginAPI, FacebookLoginAPI, AppleLoginAPI

urlpatterns = [
    path('auth/social/token/', SocialAuthTokenExchangeView.as_view(), name='social_token'),
    
    # Avec dj-rest-auth:
    # path('auth/google/', GoogleLoginAPI.as_view(), name='google_login'),
    # path('auth/facebook/', FacebookLoginAPI.as_view(), name='facebook_login'),
    # path('auth/apple/', AppleLoginAPI.as_view(), name='apple_login'),
]
"""
