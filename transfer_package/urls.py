from django.urls import path
from .views import (
    LoginView, RegisterView, RefreshTokenView, LogoutView, UserView,
    DeviceRegistrationView, PKCEInitView, PKCEAuthorizationView,
    PKCECompleteView, RevokeTokenView, UserProfileView,
    SocialLoginGoogleView, SocialLoginFacebookView,
)

app_name = 'api_auth'

urlpatterns = [
    # Endpoints d'authentification standard
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserView.as_view(), name='user'),
    # Profile (compat & v1)
    path('profile/', UserProfileView.as_view(), name='profile'),
    
    # Endpoints pour la gestion des appareils
    path('devices/', DeviceRegistrationView.as_view(), name='devices'),
    path('devices/revoke/', RevokeTokenView.as_view(), name='revoke_device'),
    
    # Endpoints pour PKCE (Proof Key for Code Exchange)
    path('pkce/init/', PKCEInitView.as_view(), name='pkce_init'),
    path('pkce/authorize/', PKCEAuthorizationView.as_view(), name='pkce_authorize'),
    path('pkce/complete/', PKCECompleteView.as_view(), name='pkce_complete'),

    # Social auth endpoints
    path('social/google/', SocialLoginGoogleView.as_view(), name='social_google'),
    path('social/facebook/', SocialLoginFacebookView.as_view(), name='social_facebook'),
]