# competitions/adapters.py
"""
Adaptateurs personnalisés pour django-allauth.
Gère la création de comptes et la liaison avec les profils MartialComp.
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import resolve_url
from django.contrib.auth import get_user_model

User = get_user_model()


class MartialCompAccountAdapter(DefaultAccountAdapter):
    """
    Adapter pour les comptes standards (email/password).
    
    Responsabilités:
    - Créer le UserProfile lors de l'inscription
    - Rediriger vers l'onboarding si nécessaire
    - Gérer les emails de vérification
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Sauvegarde l'utilisateur et crée le profil associé.
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Extraire les données du formulaire si disponibles
        if hasattr(form, 'cleaned_data'):
            user.first_name = form.cleaned_data.get('first_name', '')
            user.last_name = form.cleaned_data.get('last_name', '')
        
        if commit:
            user.save()
            self._create_user_profile(user)
        
        return user
    
    def _create_user_profile(self, user):
        """Crée le profil utilisateur avec état d'onboarding."""
        from competitions.models import UserProfile
        
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'spectator',
                'onboarding_step': 'role_selection',
                'onboarding_completed': False
            }
        )
    
    def get_login_redirect_url(self, request):
        """
        Détermine l'URL de redirection après connexion.
        """
        user = request.user
        
        # Vérifier si l'onboarding est nécessaire
        if hasattr(user, 'profile') and not user.profile.onboarding_completed:
            return resolve_url('onboarding:role')
        
        # Rediriger vers le dashboard approprié selon le contexte
        active_context = request.session.get('active_context', {})
        context_type = active_context.get('type', 'practitioner')
        
        dashboard_urls = {
            'practitioner': '/dashboard/participant/',
            'judge': '/dashboard/judge/',
            'organizational': '/dashboard/club/',
            'federation': '/dashboard/federation/',
        }
        
        return dashboard_urls.get(context_type, settings.LOGIN_REDIRECT_URL)
    
    def is_open_for_signup(self, request):
        """
        Vérifie si les inscriptions sont ouvertes.
        Peut être contrôlé via settings.
        """
        return getattr(settings, 'ACCOUNT_ALLOW_REGISTRATION', True)
    
    def get_email_confirmation_redirect_url(self, request):
        """URL après confirmation d'email."""
        if request.user.is_authenticated:
            return self.get_login_redirect_url(request)
        return resolve_url('account_login')


class MartialCompSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Adapter pour les comptes sociaux (Google, Facebook, Apple).
    
    Responsabilités:
    - Lier un compte social à un compte existant (même email)
    - Créer UserProfile et Practitioner si données suffisantes
    - Gérer l'extraction des données des providers
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Appelé avant la connexion sociale.
        Lie automatiquement à un compte existant si même email.
        """
        if sociallogin.is_existing:
            return
        
        # Récupérer l'email du compte social
        email = self._get_email_from_sociallogin(sociallogin)
        
        if email:
            try:
                # Chercher un utilisateur existant avec cet email
                user = User.objects.get(email__iexact=email)
                
                # Lier le compte social au compte existant
                sociallogin.connect(request, user)
                
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                # Si plusieurs comptes avec le même email, ne pas lier automatiquement
                pass
    
    def _get_email_from_sociallogin(self, sociallogin):
        """Extrait l'email des données du provider."""
        # Essayer d'abord les email addresses
        if sociallogin.email_addresses:
            return sociallogin.email_addresses[0].email
        
        # Sinon, chercher dans extra_data
        extra_data = sociallogin.account.extra_data
        return extra_data.get('email')
    
    def save_user(self, request, sociallogin, form=None):
        """
        Sauvegarde l'utilisateur créé via auth sociale.
        Crée également le profil et le Practitioner si possible.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Extraire les données du provider
        extra_data = sociallogin.account.extra_data
        provider = sociallogin.account.provider
        
        # Mettre à jour les infos utilisateur depuis le provider
        self._update_user_from_provider(user, extra_data, provider)
        
        # Créer le profil utilisateur
        self._create_user_profile(user)
        
        # Créer le Practitioner si données suffisantes
        self._create_practitioner(user, extra_data, provider)
        
        return user
    
    def _update_user_from_provider(self, user, extra_data, provider):
        """Met à jour les infos utilisateur depuis les données du provider."""
        updated = False
        
        # Prénom
        first_name = (
            extra_data.get('given_name') or
            extra_data.get('first_name') or
            extra_data.get('name', '').split()[0] if extra_data.get('name') else ''
        )
        if first_name and not user.first_name:
            user.first_name = first_name
            updated = True
        
        # Nom
        last_name = (
            extra_data.get('family_name') or
            extra_data.get('last_name') or
            ' '.join(extra_data.get('name', '').split()[1:]) if extra_data.get('name') else ''
        )
        if last_name and not user.last_name:
            user.last_name = last_name
            updated = True
        
        if updated:
            user.save()
    
    def _create_user_profile(self, user):
        """Crée le profil utilisateur."""
        from competitions.models import UserProfile
        
        UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'role': 'spectator',
                'onboarding_step': 'role_selection',
                'onboarding_completed': False
            }
        )
    
    def _create_practitioner(self, user, extra_data, provider):
        """
        Crée un Practitioner si les données sont suffisantes.
        """
        from competitions.models import Practitioner
        
        # Vérifier si un Practitioner existe déjà
        if Practitioner.objects.filter(user=user).exists():
            return
        
        # Extraire prénom et nom
        first_name = (
            extra_data.get('given_name') or
            extra_data.get('first_name') or
            user.first_name
        )
        last_name = (
            extra_data.get('family_name') or
            extra_data.get('last_name') or
            user.last_name
        )
        
        # Créer le Practitioner seulement si on a prénom ET nom
        if first_name and last_name:
            Practitioner.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=extra_data.get('email', user.email),
            )
    
    def get_login_redirect_url(self, request):
        """URL de redirection après connexion sociale."""
        user = request.user
        
        # Vérifier l'onboarding
        if hasattr(user, 'profile') and not user.profile.onboarding_completed:
            return resolve_url('onboarding:role')
        
        return settings.LOGIN_REDIRECT_URL
    
    def populate_user(self, request, sociallogin, data):
        """
        Peuple les champs de l'utilisateur depuis les données sociales.
        Appelé avant save_user.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # S'assurer que l'email est défini
        if not user.email:
            email = self._get_email_from_sociallogin(sociallogin)
            if email:
                user.email = email
        
        return user
    
    def is_open_for_signup(self, request, sociallogin):
        """
        Vérifie si les inscriptions sociales sont autorisées.
        """
        return getattr(settings, 'SOCIALACCOUNT_ALLOW_REGISTRATION', True)
    
    def get_connect_redirect_url(self, request, socialaccount):
        """
        URL de redirection après connexion d'un compte social à un compte existant.
        """
        return resolve_url('dashboard:profile')
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Gère les erreurs d'authentification sociale.
        """
        # Logger l'erreur pour debug
        import logging
        logger = logging.getLogger(__name__)
        logger.error(
            f"Social auth error with {provider_id}: {error}",
            exc_info=exception,
            extra={'extra_context': extra_context}
        )
        
        # Appeler le comportement par défaut
        super().authentication_error(request, provider_id, error, exception, extra_context)
