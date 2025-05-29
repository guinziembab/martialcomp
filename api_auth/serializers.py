from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken as JWTRefreshToken
import uuid
import base64
import hashlib
import secrets
import string

from .models import RefreshToken, DeviceRegistration, PKCESession, AccessTokenLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les données utilisateur"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'is_active']
        read_only_fields = ['id', 'date_joined', 'is_active']


class LoginSerializer(serializers.Serializer):
    """Serializer pour le login"""
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, write_only=True)
    device_id = serializers.CharField(max_length=255, required=False)
    device_name = serializers.CharField(max_length=255, required=False)
    device_model = serializers.CharField(max_length=255, required=False)
    os_version = serializers.CharField(max_length=50, required=False)
    app_version = serializers.CharField(max_length=50, required=False)
    
    # PKCE params
    code_challenge = serializers.CharField(max_length=128, required=False)
    code_challenge_method = serializers.CharField(max_length=10, default="S256", required=False)
    tenant_id = serializers.CharField(max_length=36, required=False)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        code_challenge = attrs.get('code_challenge')
        tenant_id = attrs.get('tenant_id')
        
        if not username or not password:
            raise serializers.ValidationError(_("Nom d'utilisateur et mot de passe sont requis."))
        
        # Authentifier l'utilisateur
        user = authenticate(username=username, password=password)
        
        if not user:
            raise serializers.ValidationError(_("Identifiants invalides."))
        
        if not user.is_active:
            raise serializers.ValidationError(_("Ce compte a été désactivé."))
        
        # Ajouter l'utilisateur authentifié aux données validées
        attrs['user'] = user
        
        return attrs


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement de nouveaux utilisateurs"""
    password = serializers.CharField(max_length=128, write_only=True)
    password_confirm = serializers.CharField(max_length=128, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        
    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password != password_confirm:
            raise serializers.ValidationError(_("Les mots de passe ne correspondent pas."))
        
        # Vérifier la complexité du mot de passe
        if len(password) < 8:
            raise serializers.ValidationError(_("Le mot de passe doit contenir au moins 8 caractères."))
        
        return attrs
    
    def create(self, validated_data):
        # Retirer le champ de confirmation du mot de passe
        validated_data.pop('password_confirm')
        
        # Créer l'utilisateur
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        return user


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement des appareils mobiles"""
    
    class Meta:
        model = DeviceRegistration
        fields = [
            'id', 'device_id', 'device_name', 'device_model', 
            'os_version', 'app_version', 'push_token', 'is_active'
        ]
        read_only_fields = ['id', 'is_active']
        
    def create(self, validated_data):
        # L'utilisateur est récupéré du contexte
        user = self.context['request'].user
        tenant = getattr(self.context['request'], 'tenant', None)
        
        # Vérifier si l'appareil existe déjà
        device, created = DeviceRegistration.objects.get_or_create(
            user=user,
            device_id=validated_data['device_id'],
            defaults={
                'device_name': validated_data.get('device_name'),
                'device_model': validated_data.get('device_model'),
                'os_version': validated_data.get('os_version'),
                'app_version': validated_data.get('app_version'),
                'push_token': validated_data.get('push_token'),
                'tenant': tenant
            }
        )
        
        # Si l'appareil existe déjà, mettre à jour les informations
        if not created:
            for key, value in validated_data.items():
                if key != 'device_id':  # Ne pas modifier l'ID de l'appareil
                    setattr(device, key, value)
            device.last_used_at = timezone.now()
            device.save()
            
        return device


class TokenSerializer(serializers.Serializer):
    """Serializer pour le retour des tokens JWT"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer(read_only=True)
    expires_in = serializers.IntegerField()


class RefreshTokenSerializer(serializers.Serializer):
    """Serializer pour le rafraîchissement des tokens"""
    refresh = serializers.CharField()
    code_verifier = serializers.CharField(required=False)
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        code_verifier = attrs.get('code_verifier')
        
        # Vérifier si le token existe et est valide
        try:
            token = RefreshToken.objects.get(token=refresh_token)
        except RefreshToken.DoesNotExist:
            raise serializers.ValidationError(_("Token de rafraîchissement invalide."))
        
        if token.is_expired:
            raise serializers.ValidationError(_("Token de rafraîchissement expiré."))
        
        if token.revoked:
            raise serializers.ValidationError(_("Token de rafraîchissement révoqué."))
        
        # Si PKCE est utilisé, vérifier le code_verifier
        if token.code_challenge and not code_verifier:
            raise serializers.ValidationError(_("Code verifier requis pour PKCE."))
        
        if token.code_challenge and code_verifier:
            # Vérifier que le code_verifier correspond au code_challenge
            if token.code_challenge_method == "S256":
                verifier_bytes = code_verifier.encode('ascii')
                challenge_bytes = hashlib.sha256(verifier_bytes).digest()
                calculated_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('ascii').rstrip('=')
                
                if token.code_challenge != calculated_challenge:
                    raise serializers.ValidationError(_("Code verifier invalide."))
            
            # Pour la méthode "plain" (non recommandée mais supportée)
            elif token.code_challenge_method == "plain":
                if token.code_challenge != code_verifier:
                    raise serializers.ValidationError(_("Code verifier invalide."))
        
        attrs['token_obj'] = token
        attrs['user'] = token.user
        
        return attrs


class PKCEInitSerializer(serializers.ModelSerializer):
    """Serializer pour initialiser le flux PKCE"""
    
    class Meta:
        model = PKCESession
        fields = [
            'code_challenge', 'code_challenge_method', 'state', 
            'redirect_uri', 'scope', 'client_id'
        ]
        
    def create(self, validated_data):
        # Définir une date d'expiration (10 minutes)
        validated_data['expires_at'] = timezone.now() + timezone.timedelta(minutes=10)
        
        # Créer un code d'autorisation aléatoire
        chars = string.ascii_letters + string.digits
        auth_code = ''.join(secrets.choice(chars) for _ in range(40))
        validated_data['auth_code'] = auth_code
        
        # Tenant context
        tenant = getattr(self.context.get('request'), 'tenant', None)
        if tenant:
            validated_data['tenant'] = tenant
        
        # Create the PKCE session
        pkce_session = PKCESession.objects.create(**validated_data)
        return pkce_session


class PKCECompleteSerializer(serializers.Serializer):
    """Serializer pour compléter le flux PKCE et échanger le code contre des tokens"""
    auth_code = serializers.CharField(max_length=128)
    code_verifier = serializers.CharField(max_length=128)
    client_id = serializers.CharField(max_length=255)
    
    def validate(self, attrs):
        auth_code = attrs.get('auth_code')
        code_verifier = attrs.get('code_verifier')
        client_id = attrs.get('client_id')
        
        # Vérifier si la session PKCE existe et est valide
        try:
            pkce_session = PKCESession.objects.get(auth_code=auth_code, client_id=client_id, used=False)
        except PKCESession.DoesNotExist:
            raise serializers.ValidationError(_("Code d'autorisation ou client_id invalide."))
        
        if pkce_session.is_expired:
            raise serializers.ValidationError(_("Code d'autorisation expiré."))
        
        # Vérifier le code_verifier par rapport au code_challenge
        if pkce_session.code_challenge_method == "S256":
            verifier_bytes = code_verifier.encode('ascii')
            challenge_bytes = hashlib.sha256(verifier_bytes).digest()
            calculated_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('ascii').rstrip('=')
            
            if pkce_session.code_challenge != calculated_challenge:
                raise serializers.ValidationError(_("Code verifier invalide."))
        
        # Pour la méthode "plain" (non recommandée mais supportée)
        elif pkce_session.code_challenge_method == "plain":
            if pkce_session.code_challenge != code_verifier:
                raise serializers.ValidationError(_("Code verifier invalide."))
        
        # Marquer la session comme utilisée
        pkce_session.used = True
        pkce_session.code_verifier = code_verifier
        pkce_session.save(update_fields=['used', 'code_verifier'])
        
        attrs['pkce_session'] = pkce_session
        attrs['user'] = pkce_session.user
        
        return attrs


class LogoutSerializer(serializers.Serializer):
    """Serializer pour la déconnexion (révocation des tokens)"""
    refresh = serializers.CharField()
    
    def validate(self, attrs):
        refresh_token = attrs.get('refresh')
        
        # Vérifier si le token existe
        try:
            token = RefreshToken.objects.get(token=refresh_token)
        except RefreshToken.DoesNotExist:
            # Si le token n'existe pas, considérons que c'est déjà fait
            pass
        else:
            # Si le token existe et n'est pas déjà révoqué, l'ajouter aux attributs validés
            if not token.revoked:
                attrs['token_obj'] = token
        
        return attrs