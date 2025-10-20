from django.core.exceptions import PermissionDenied
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
import json
import uuid
import base64
import hashlib
import os

from .models import RefreshToken, AccessTokenLog, DeviceRegistration, PKCESession
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

User = get_user_model()


class AuthAPITestCase(TestCase):
    """
    Cas de test pour l'API d'authentification.
    """
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Paramètres PKCE
        self.code_verifier = ''.join([chr(65 + i % 26) for i in range(50)])  # ABCDEF...
        verifier_bytes = self.code_verifier.encode('ascii')
        challenge_bytes = hashlib.sha256(verifier_bytes).digest()
        self.code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('ascii').rstrip('=')
        
        # Créer des données de test pour le tenant si nécessaire
        try:
            from multitenant.models import Tenant
            self.tenant = Tenant.objects.create(
                name='Test Tenant',
                subdomain='test'
            )
        except ImportError:
            self.tenant = None
    
    def test_login_success(self):
        """Teste la connexion réussie"""
        url = reverse('api_auth:login')
        data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'device_id': 'test-device-id',
            'device_name': 'Test Device',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'testuser')
        
        # Vérifie que le RefreshToken a été créé en base
        self.assertTrue(RefreshToken.objects.filter(user=self.user).exists())
        # Vérifie que l'AccessTokenLog a été créé
        self.assertTrue(AccessTokenLog.objects.filter(user=self.user).exists())
        # Vérifie que l'appareil a été enregistré
        self.assertTrue(DeviceRegistration.objects.filter(
            user=self.user, 
            device_id='test-device-id'
        ).exists())
    
    def test_login_with_pkce(self):
        """Teste la connexion avec PKCE"""
        url = reverse('api_auth:login')
        data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'device_id': 'test-device-id',
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Vérifie que le RefreshToken a été créé avec le code_challenge
        refresh_token = RefreshToken.objects.get(user=self.user, device_id='test-device-id')
        self.assertEqual(refresh_token.code_challenge, self.code_challenge)
        self.assertEqual(refresh_token.code_challenge_method, 'S256')
    
    def test_login_failure(self):
        """Teste l'échec de connexion avec des identifiants invalides"""
        url = reverse('api_auth:login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword',
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_register_success(self):
        """Teste l'inscription réussie"""
        url = reverse('api_auth:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123',
            'first_name': 'New',
            'last_name': 'User',
            'device_id': 'new-device-id'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')
        
        # Vérifie que l'utilisateur a été créé
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_refresh_token(self):
        """Teste le rafraîchissement du token"""
        # D'abord on se connecte pour obtenir un token
        login_url = reverse('api_auth:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123',
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Ensuite on rafraîchit le token
        refresh_url = reverse('api_auth:refresh')
        refresh_data = {
            'refresh': refresh_token
        }
        
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        self.assertIn('refresh', refresh_response.data)
        
        # Vérifie que l'ancien RefreshToken a été révoqué
        old_token = RefreshToken.objects.get(token=refresh_token)
        self.assertTrue(old_token.revoked)
        
        # Vérifie qu'un nouveau RefreshToken a été créé
        new_token = RefreshToken.objects.get(token=refresh_response.data['refresh'])
        self.assertFalse(new_token.revoked)
    
    def test_logout(self):
        """Teste la déconnexion (révocation du token)"""
        # D'abord on se connecte pour obtenir un token
        login_url = reverse('api_auth:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123',
        }
        
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['refresh']
        
        # Ensuite on se déconnecte
        logout_url = reverse('api_auth:logout')
        logout_data = {
            'refresh': refresh_token
        }
        
        logout_response = self.client.post(logout_url, logout_data, format='json')
        
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifie que le RefreshToken a été révoqué
        token = RefreshToken.objects.get(token=refresh_token)
        self.assertTrue(token.revoked)
    
    def test_pkce_flow(self):
        """Teste le flux PKCE complet"""
        # 1. Initialisation PKCE
        init_url = reverse('api_auth:pkce_init')
        init_data = {
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256',
            'client_id': 'test-client',
            'state': 'random-state-string',
            'redirect_uri': 'https://example.com/callback',
            'scope': 'read write'
        }
        
        init_response = self.client.post(init_url, init_data, format='json')
        
        self.assertEqual(init_response.status_code, status.HTTP_201_CREATED)
        self.assertIn('auth_code', init_response.data)
        auth_code = init_response.data['auth_code']
        
        # 2. Authentification PKCE
        # D'abord on se connecte
        self.client.force_authenticate(user=self.user)
        
        auth_url = reverse('api_auth:pkce_authorize')
        auth_data = {
            'auth_code': auth_code
        }
        
        auth_response = self.client.post(auth_url, auth_data, format='json')
        
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        self.assertTrue(auth_response.data['success'])
        
        # 3. Complétion PKCE
        self.client.force_authenticate(user=None)  # Déconnexion
        
        complete_url = reverse('api_auth:pkce_complete')
        complete_data = {
            'auth_code': auth_code,
            'code_verifier': self.code_verifier,
            'client_id': 'test-client'
        }
        
        complete_response = self.client.post(complete_url, complete_data, format='json')
        
        self.assertEqual(complete_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', complete_response.data)
        self.assertIn('refresh', complete_response.data)
        
        # Vérifie que la session PKCE a été marquée comme utilisée
        pkce_session = PKCESession.objects.get(auth_code=auth_code)
        self.assertTrue(pkce_session.used)
        self.assertEqual(pkce_session.code_verifier, self.code_verifier)
    
    def test_user_view(self):
        """Teste la récupération des informations utilisateur"""
        # D'abord on s'authentifie
        self.client.force_authenticate(user=self.user)
        
        url = reverse('api_auth:user')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_device_registration(self):
        """Teste l'enregistrement d'un appareil"""
        # D'abord on s'authentifie
        self.client.force_authenticate(user=self.user)
        
        url = reverse('api_auth:devices')
        data = {
            'device_id': 'new-device',
            'device_name': 'New Device',
            'device_model': 'Google Pixel',
            'os_version': 'Android 12',
            'app_version': '1.0.0'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['device_id'], 'new-device')
        
        # Vérifie que l'appareil a été enregistré
        device = DeviceRegistration.objects.get(device_id='new-device')
        self.assertEqual(device.user, self.user)
        self.assertEqual(device.device_name, 'New Device')