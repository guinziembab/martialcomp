from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
import uuid
import datetime
import secrets
import string

from .models import RefreshToken, DeviceRegistration, PKCESession, AccessTokenLog
from .serializers import (
    LoginSerializer, RegistrationSerializer, TokenSerializer, UserSerializer,
    RefreshTokenSerializer, DeviceRegistrationSerializer, LogoutSerializer,
    PKCEInitSerializer, PKCECompleteSerializer
)

User = get_user_model()


class LoginView(APIView):
    """
    Vue pour l'authentification des utilisateurs et la génération de tokens JWT
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Récupération de l'utilisateur et des données d'appareil
            user = serializer.validated_data['user']
            device_id = serializer.validated_data.get('device_id')
            device_name = serializer.validated_data.get('device_name')
            device_model = serializer.validated_data.get('device_model')
            os_version = serializer.validated_data.get('os_version')
            app_version = serializer.validated_data.get('app_version')
            
            # PKCE parameters
            code_challenge = serializer.validated_data.get('code_challenge')
            code_challenge_method = serializer.validated_data.get('code_challenge_method', 'S256')
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None)
            
            # Génération des tokens JWT
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Ajouter des claims personnalisés au token JWT
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Si un appareil est spécifié, l'enregistrer
            if device_id:
                device, created = DeviceRegistration.objects.get_or_create(
                    user=user,
                    device_id=device_id,
                    defaults={
                        'device_name': device_name,
                        'device_model': device_model,
                        'os_version': os_version,
                        'app_version': app_version,
                        'tenant': tenant
                    }
                )
                
                # Si l'appareil existe, mettre à jour ses informations
                if not created:
                    if device_name:
                        device.device_name = device_name
                    if device_model:
                        device.device_model = device_model
                    if os_version:
                        device.os_version = os_version
                    if app_version:
                        device.app_version = app_version
                    device.last_used_at = timezone.now()
                    device.save()
            
            # Créer un RefreshToken dans la base de données
            # Calculer la date d'expiration (par défaut 30 jours)
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            # Créer un token de rafraîchissement en base de données
            db_refresh_token = RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant,
                code_challenge=code_challenge,
                code_challenge_method=code_challenge_method if code_challenge else None,
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RegisterView(APIView):
    """
    Vue pour l'inscription de nouveaux utilisateurs
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Récupération des informations d'appareil
            device_data = {
                'device_id': request.data.get('device_id'),
                'device_name': request.data.get('device_name'),
                'device_model': request.data.get('device_model'),
                'os_version': request.data.get('os_version'),
                'app_version': request.data.get('app_version'),
            }
            
            # Si un ID d'appareil est fourni, l'enregistrer
            if device_data['device_id']:
                DeviceRegistration.objects.create(
                    user=user,
                    **{k: v for k, v in device_data.items() if v is not None},
                    tenant=getattr(request, 'tenant', None)
                )
            
            # Générer des tokens pour le nouvel utilisateur
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None)
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Créer un RefreshToken dans la base de données
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=device_data.get('device_id'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=device_data.get('device_id'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RefreshTokenView(APIView):
    """
    Vue pour rafraîchir les tokens d'accès
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if serializer.is_valid():
            # Récupérer les objets validés
            db_token = serializer.validated_data['token_obj']
            user = serializer.validated_data['user']
            
            # Générer un nouveau token JWT
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None) or db_token.tenant
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Révoquer l'ancien token de rafraîchissement
            db_token.revoked = True
            db_token.save(update_fields=['revoked'])
            
            # Créer un nouveau token de rafraîchissement en base de données
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            new_db_token = RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=db_token.device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', '') or db_token.user_agent,
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=db_token.device_id,
                user_agent=request.META.get('HTTP_USER_AGENT', '') or db_token.user_agent,
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutView(APIView):
    """
    Vue pour la déconnexion et la révocation des tokens
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            # Si un token a été trouvé, le révoquer
            token_obj = serializer.validated_data.get('token_obj')
            if token_obj:
                token_obj.revoked = True
                token_obj.save(update_fields=['revoked'])
                
                # Révoquer aussi toutes les sessions PKCE associées
                PKCESession.objects.filter(
                    user=token_obj.user, 
                    used=False
                ).update(used=True)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(APIView):
    """
    Vue pour obtenir les informations de l'utilisateur connecté
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)


class DeviceRegistrationView(APIView):
    """
    Vue pour enregistrer un nouvel appareil
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DeviceRegistrationSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            device = serializer.save()
            return Response(DeviceRegistrationSerializer(device).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """Récupérer tous les appareils enregistrés pour l'utilisateur"""
        devices = DeviceRegistration.objects.filter(user=request.user)
        serializer = DeviceRegistrationSerializer(devices, many=True)
        return Response(serializer.data)


class PKCEInitView(APIView):
    """
    Vue pour initialiser le flux PKCE (sans authentification)
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PKCEInitSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            pkce_session = serializer.save()
            
            return Response({
                'auth_code': pkce_session.auth_code,
                'expires_in': int((pkce_session.expires_at - timezone.now()).total_seconds())
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PKCEAuthorizationView(APIView):
    """
    Vue pour autoriser un flux PKCE (avec authentification)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        auth_code = request.data.get('auth_code')
        if not auth_code:
            return Response(
                {'error': _("Code d'autorisation requis.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pkce_session = PKCESession.objects.get(auth_code=auth_code, used=False)
        except PKCESession.DoesNotExist:
            return Response(
                {'error': _("Code d'autorisation invalide.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if pkce_session.is_expired:
            return Response(
                {'error': _("Code d'autorisation expiré.")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Associer l'utilisateur à la session PKCE
        pkce_session.user = request.user
        pkce_session.save(update_fields=['user'])
        
        return Response({
            'success': True,
            'message': _("Autorisation accordée avec succès.")
        })


class PKCECompleteView(APIView):
    """
    Vue pour compléter le flux PKCE et échanger un code contre des tokens JWT
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PKCECompleteSerializer(data=request.data)
        if serializer.is_valid():
            # Récupérer les objets validés
            pkce_session = serializer.validated_data['pkce_session']
            user = serializer.validated_data['user']
            
            if not user:
                return Response(
                    {'error': _("Session PKCE non autorisée.")},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Générer les tokens JWT
            jwt_refresh = JWTRefreshToken.for_user(user)
            
            # Multi-tenant context
            tenant = getattr(request, 'tenant', None) or pkce_session.tenant
            if tenant:
                jwt_refresh['tenant_id'] = str(tenant.id)
                jwt_refresh['tenant_name'] = tenant.name
            
            # Définis le JTI pour le token d'accès pour les logs
            jti = str(uuid.uuid4())
            jwt_refresh.access_token['jti'] = jti
            
            # Créer un RefreshToken dans la base de données
            expires_in_days = getattr(settings, 'REFRESH_TOKEN_LIFETIME_DAYS', 30)
            expires_at = timezone.now() + datetime.timedelta(days=expires_in_days)
            
            db_refresh_token = RefreshToken.objects.create(
                user=user,
                token=str(jwt_refresh),
                expires_at=expires_at,
                device_id=None,  # À remplir avec un appareil si disponible
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant,
                code_challenge=pkce_session.code_challenge,
                code_challenge_method=pkce_session.code_challenge_method,
            )
            
            # Enregistrer le jeton d'accès dans les logs
            access_token_expires = timezone.now() + datetime.timedelta(minutes=60)  # 1 heure par défaut
            
            AccessTokenLog.objects.create(
                user=user,
                jti=jti,
                expires_at=access_token_expires,
                device_id=None,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                ip_address=self.get_client_ip(request),
                tenant=tenant
            )
            
            # Préparer la réponse
            response_data = {
                'access': str(jwt_refresh.access_token),
                'refresh': str(jwt_refresh),
                'user': UserSerializer(user).data,
                'expires_in': 3600  # 1 heure pour le token d'accès
            }
            
            return Response(TokenSerializer(response_data).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client en tenant compte des proxy"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RevokeTokenView(APIView):
    """
    Vue pour révoquer un token spécifique ou tous les tokens d'un utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        device_id = request.data.get('device_id')
        all_devices = request.data.get('all_devices', False)
        
        if device_id:
            # Révoquer tous les tokens pour un appareil spécifique
            RefreshToken.objects.filter(
                user=request.user, 
                device_id=device_id, 
                revoked=False
            ).update(revoked=True)
            
            return Response({'message': _("Tokens révoqués pour l'appareil spécifié.")})
        
        elif all_devices:
            # Révoquer tous les tokens pour tous les appareils
            RefreshToken.objects.filter(
                user=request.user,
                revoked=False
            ).update(revoked=True)
            
            return Response({'message': _("Tous les tokens ont été révoqués.")})
        
        return Response(
            {'error': _("Veuillez spécifier device_id ou all_devices=True.")},
            status=status.HTTP_400_BAD_REQUEST
        )