"""
Tests pour la fonctionnalité de profil hors-ligne
"""
import json
import base64
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import timedelta

from competitions.models import Practitioner, PractitionerQRCode, Discipline
from organizations.models import Organization
from competitions.utils.qr_offline import OfflineProfileGenerator, OfflineQRTokenGenerator


class OfflineProfileGeneratorTests(TestCase):
    """
    Tests pour le générateur de profil hors-ligne
    """
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Club',
            code='TEST',
            type='club'
        )
        
        # Créer une discipline
        self.discipline = Discipline.objects.create(
            name='Karate',
            description='Karate Description'
        )
        
        # Créer un pratiquant
        self.practitioner = Practitioner.objects.create(
            user=self.user,
            organization=self.organization,
            first_name='Test',
            last_name='User',
            birth_date=timezone.now().date() - timedelta(days=365*30),  # 30 ans
            license_number='12345',
            email='test@example.com',
            is_active=True
        )
        
        # Ajouter la discipline au pratiquant
        self.practitioner.disciplines.add(self.discipline)
        self.practitioner.primary_discipline = self.discipline
        self.practitioner.save()
        
        # Créer un QR code pour le pratiquant
        self.qr_code = PractitionerQRCode.objects.create(
            practitioner=self.practitioner
        )

    def test_generate_offline_profile(self):
        """
        Teste la génération du profil hors-ligne
        """
        # Générer le profil
        profile_data = OfflineProfileGenerator.generate_offline_profile(self.practitioner)
        
        # Vérifier que le token est présent
        self.assertIn('token', profile_data)
        self.assertIsNotNone(profile_data['token'])
        
        # Vérifier les dates de génération et d'expiration
        self.assertIn('generated_at', profile_data)
        self.assertIn('expires_at', profile_data)
        
        # Vérifier les informations de compression
        self.assertIn('compressed_size', profile_data)
        self.assertIn('compression_ratio', profile_data)
        
        # Vérifier que la taille est raisonnable (< 4000 caractères pour le QR code)
        self.assertLess(profile_data['compressed_size'], 4000)
        
        # Vérifier les données du profil
        self.assertEqual(profile_data['profile_data']['prac_id'], self.practitioner.id)
        self.assertEqual(profile_data['profile_data']['first_name'], self.practitioner.first_name)
        self.assertEqual(profile_data['profile_data']['last_name'], self.practitioner.last_name)

    def test_verify_offline_profile(self):
        """
        Teste la vérification du profil hors-ligne
        """
        # Générer le profil
        profile_data = OfflineProfileGenerator.generate_offline_profile(self.practitioner)
        token = profile_data['token']
        
        # Vérifier le token
        verified_data = OfflineProfileGenerator.verify_offline_profile(token)
        
        # Le token devrait être valide
        self.assertTrue(verified_data['valid'])
        
        # Vérifier les données principales
        self.assertEqual(verified_data['prac_id'], self.practitioner.id)
        self.assertEqual(verified_data['first_name'], self.practitioner.first_name)
        self.assertEqual(verified_data['last_name'], self.practitioner.last_name)
        
        # Vérifier la date d'expiration
        self.assertGreater(verified_data['exp'], int(timezone.now().timestamp()))
        
        # Vérifier les jours restants
        self.assertIn('days_until_expiry', verified_data)
        self.assertGreater(verified_data['days_until_expiry'], 25)  # Devrait être proche de 30 jours

    def test_invalid_token(self):
        """
        Teste la vérification d'un token invalide
        """
        # Créer un token invalide
        fake_token = "InvalidTokenData123"
        
        # Essayer de vérifier le token
        verified_data = OfflineProfileGenerator.verify_offline_profile(fake_token)
        
        # Le token devrait être invalide
        self.assertFalse(verified_data.get('valid', False))
        self.assertEqual(verified_data.get('reason'), 'token_malformed')
        
    def test_tampered_token(self):
        """
        Teste la vérification d'un token modifié
        """
        # Générer le profil
        profile_data = OfflineProfileGenerator.generate_offline_profile(self.practitioner)
        token = profile_data['token']
        
        # Décoder le token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        data = json.loads(decoded)
        
        # Modifier les données (simuler une falsification)
        data['fn'] = 'Hacker'
        
        # Ré-encoder sans recalculer la signature
        tampered_token = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
        
        # Vérifier le token modifié
        verified_data = OfflineProfileGenerator.verify_offline_profile(tampered_token)
        
        # Le token devrait être invalide avec une signature incorrecte
        self.assertFalse(verified_data.get('valid', False))
        self.assertEqual(verified_data.get('reason'), 'signature_invalid')
        
    def test_expired_token(self):
        """
        Teste la vérification d'un token expiré
        """
        # Générer un profil
        profile_data = OfflineProfileGenerator.generate_offline_profile(self.practitioner)
        token = profile_data['token']
        
        # Décoder le token
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        data = json.loads(decoded)
        
        # Modifier la date d'expiration pour qu'elle soit dans le passé
        data['exp'] = int(timezone.now().timestamp()) - 3600  # Expire il y a 1 heure
        
        # Recalculer la signature pour que le token soit valide au niveau du format
        sig = data.pop('sig')
        data['sig'] = OfflineProfileGenerator._generate_profile_signature(data)
        
        # Ré-encoder
        expired_token = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
        
        # Vérifier le token expiré
        verified_data = OfflineProfileGenerator.verify_offline_profile(expired_token)
        
        # Le token devrait être invalide car expiré
        self.assertFalse(verified_data.get('valid', False))
        self.assertEqual(verified_data.get('reason'), 'token_expired')


class QRCodeModelTests(TestCase):
    """
    Tests pour le modèle PractitionerQRCode
    """
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Club',
            code='TEST',
            type='club'
        )
        
        # Créer un pratiquant
        self.practitioner = Practitioner.objects.create(
            user=self.user,
            organization=self.organization,
            first_name='Test',
            last_name='User',
            birth_date=timezone.now().date() - timedelta(days=365*25),  # 25 ans
            license_number='12345',
            email='test@example.com',
            is_active=True
        )
        
        # Créer un QR code pour le pratiquant
        self.qr_code = PractitionerQRCode.objects.create(
            practitioner=self.practitioner
        )

    def test_generate_offline_profile_method(self):
        """
        Teste la méthode generate_offline_profile du modèle PractitionerQRCode
        """
        # Générer le profil hors-ligne
        profile_data = self.qr_code.generate_offline_profile()
        
        # Vérifier que le token a été stocké dans le modèle
        self.assertIsNotNone(self.qr_code.offline_profile_token)
        self.assertIsNotNone(self.qr_code.offline_profile_generated_at)
        
        # Vérifier que les dates correspondent
        profile_date = timezone.datetime.fromisoformat(profile_data['generated_at'])
        db_date = self.qr_code.offline_profile_generated_at
        self.assertAlmostEqual(profile_date.timestamp(), db_date.timestamp(), delta=1)
        
        # Vérifier les informations retournées
        self.assertIn('token', profile_data)
        self.assertIn('profile_data', profile_data)
        self.assertIn('compressed_size', profile_data)
        
    def test_get_offline_profile_data_method(self):
        """
        Teste la méthode get_offline_profile_data du modèle PractitionerQRCode
        """
        # Cas 1: Premier appel, doit générer un nouveau profil
        profile_data = self.qr_code.get_offline_profile_data()
        self.assertIsNotNone(self.qr_code.offline_profile_token)
        
        # Sauvegarder le token pour comparaison
        original_token = self.qr_code.offline_profile_token
        
        # Cas 2: Deuxième appel peu après, doit réutiliser le même profil
        profile_data2 = self.qr_code.get_offline_profile_data()
        self.assertEqual(original_token, self.qr_code.offline_profile_token)
        
        # Cas 3: Modification de la date de génération pour simuler un token ancien
        self.qr_code.offline_profile_generated_at = timezone.now() - timedelta(days=20)
        self.qr_code.save()
        
        profile_data3 = self.qr_code.get_offline_profile_data()
        self.assertNotEqual(original_token, self.qr_code.offline_profile_token)


class OfflineProfileViewsTests(TestCase):
    """
    Tests pour les vues liées au profil hors-ligne
    """
    def setUp(self):
        # Créer un utilisateur pour les tests
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        
        # Créer une organisation
        self.organization = Organization.objects.create(
            name='Test Club',
            code='TEST',
            type='club'
        )
        
        # Créer un pratiquant
        self.practitioner = Practitioner.objects.create(
            user=self.user,
            organization=self.organization,
            first_name='Test',
            last_name='User',
            birth_date=timezone.now().date() - timedelta(days=365*25),
            license_number='12345',
            email='test@example.com',
            is_active=True
        )
        
        # Créer un QR code pour le pratiquant
        self.qr_code = PractitionerQRCode.objects.create(
            practitioner=self.practitioner
        )
        
        # Générer le token de profil hors-ligne
        profile_data = self.qr_code.generate_offline_profile()
        self.token = profile_data['token']
        
        # Créer un client pour les tests
        self.client = Client()
        self.client.login(username='testuser', password='testpassword')

    def test_qr_code_offline_profile_view(self):
        """
        Teste la vue qr_code_offline_profile
        """
        # Accéder à la vue de génération du profil hors-ligne
        url = reverse('competitions:qr:offline_profile', args=[self.practitioner.id])
        response = self.client.get(url)
        
        # Vérifier le code de statut
        self.assertEqual(response.status_code, 200)
        
        # Vérifier que le template est utilisé
        self.assertTemplateUsed(response, 'competitions/qr_scanner/offline_profile.html')
        
        # Vérifier que les données du profil sont dans le contexte
        self.assertIn('profile_data', response.context)
        self.assertIn('token', response.context['profile_data'])
        
        # Vérifier l'accès JSON
        response_json = self.client.get(url + '?format=json')
        self.assertEqual(response_json.status_code, 200)
        data = json.loads(response_json.content)
        self.assertIn('profile_token', data)
        self.assertIn('qr_image_url', data)
        
    def test_verify_offline_profile_view(self):
        """
        Teste la vue verify_offline_profile
        """
        # Créer les données de requête
        data = {'token': self.token}
        
        # Envoyer une requête POST à la vue de vérification
        url = reverse('competitions:qr:verify_offline_profile')
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Vérifier le code de statut
        self.assertEqual(response.status_code, 200)
        
        # Vérifier la réponse JSON
        data = json.loads(response.content)
        self.assertTrue(data['valid'])
        self.assertIn('profile', data)
        self.assertEqual(data['profile']['prac_id'], self.practitioner.id)
        
    def test_view_offline_profile_public_view(self):
        """
        Teste la vue view_offline_profile_public
        """
        # Accéder à la vue publique sans token (devrait afficher le formulaire)
        url = reverse('competitions:qr:view_offline_profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'competitions/qr_scanner/offline_profile_entry.html')
        
        # Accéder à la vue publique avec un token valide
        url = reverse('competitions:qr:view_offline_profile_with_token', args=[self.token])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'competitions/qr_scanner/offline_profile_view.html')
        
        # Vérifier que les informations du profil sont présentes
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile']['first_name'], self.practitioner.first_name)
        
        # Tester avec un token invalide
        url = reverse('competitions:qr:view_offline_profile_with_token', args=['invalid_token'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'competitions/qr_scanner/offline_profile_error.html')
        
    def test_post_token_to_view_profile(self):
        """
        Teste l'envoi d'un token via POST au formulaire de consultation
        """
        # Envoyer le token via POST
        url = reverse('competitions:qr:view_offline_profile')
        response = self.client.post(url, {'token': self.token})
        
        # Doit rediriger ou afficher le profil directement
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'competitions/qr_scanner/offline_profile_view.html')
        
        # Vérifier que les informations du profil sont présentes
        self.assertIn('profile', response.context)
        self.assertEqual(response.context['profile']['first_name'], self.practitioner.first_name)