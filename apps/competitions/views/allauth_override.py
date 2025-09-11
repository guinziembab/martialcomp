from django.core.exceptions import PermissionDenied
# Modifier competitions/views/allauth_override.py

from allauth.account.views import SignupView
from django.shortcuts import redirect
from django.urls import reverse
from allauth.account import signals
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import logging
from django.db import IntegrityError
from django.contrib.auth.models import User
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

class CustomSignupView(SignupView):
    """
    Vue d'inscription personnalisée qui force la redirection vers l'onboarding.
    Cette vue remplace celle de django-allauth.
    """
    
    def form_valid(self, form):
        try:
            # Vérifier si l'utilisateur existe déjÃ  avant de sauvegarder
            username = form.cleaned_data.get('username')
            if User.objects.filter(username__iexact=username).exists():
                # Ajouter une erreur au formulaire
                form.add_error('username', _("Ce nom d'utilisateur est déjÃ  utilisé. Veuillez en choisir un autre."))
                return self.form_invalid(form)
            
            # Enregistrer l'utilisateur comme d'habitude
            self.user = form.save(self.request)
            
            # Créer le profil utilisateur si nécessaire
            from apps.competitions.models import UserProfile
            profile, created = UserProfile.objects.get_or_create(
                user=self.user,
                defaults={
                    'role': 'spectator',
                    'onboarding_step': 'role_selection',
                    'onboarding_completed': False
                }
            )
            
            # Log l'action
            if created:
                logger.info(f"Profil utilisateur créé pour {self.user.username}")
            else:
                logger.info(f"Profil utilisateur existant mis Ã  jour pour {self.user.username}")
            
            # Message de bienvenue
            messages.success(self.request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
            
            # Rediriger vers la page de sélection de rÃ´le (avec le namespace complet)
            redirect_url = '/competitions/onboarding/role/'
            logger.info(f"Redirection après inscription vers {redirect_url} pour {self.user.username}")
            
            # Connecter l'utilisateur manuellement avec backend explicite
            from django.contrib.auth import login
            
            # Définir le backend explicitement pour éviter l'erreur
            self.user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            # Login de l'utilisateur
            try:
                login(self.request, self.user)
                logger.info(f"Utilisateur {self.user.username} connecté avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de la connexion: {e}")
                # Continuer mÃªme si la connexion échoue
            
            # Rediriger vers l'onboarding
            return redirect(redirect_url)
            
        except IntegrityError as e:
            # Gérer explicitement l'erreur d'intégrité (nom d'utilisateur dupliqué)
            logger.error(f"Erreur d'intégrité lors de la création du compte: {str(e)}")
            if "username" in str(e).lower():
                form.add_error('username', _("Ce nom d'utilisateur est déjÃ  utilisé. Veuillez en choisir un autre."))
            else:
                form.add_error(None, _("Une erreur est survenue lors de la création du compte. Veuillez réessayer."))
            return self.form_invalid(form)
            
        except Exception as e:
            # Gérer les autres exceptions
            logger.error(f"Erreur lors de la redirection vers l'onboarding: {str(e)}")
            form.add_error(None, _("Une erreur est survenue. Veuillez réessayer."))
            return self.form_invalid(form)

