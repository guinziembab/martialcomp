from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import resolve, Resolver404, reverse
from django.http import HttpResponseRedirect
from ..auth_forms import SignUpForm
from ..models import UserProfile
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
# Importer correctement le signal
from ..models.users import create_user_profile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@ensure_csrf_cookie
def login_view(request):
    """Vue de connexion utilisateur."""
    # Rediriger si déjÃ  connecté
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('competitions:dashboard:index')
    
    # Préparer les informations de profil contextuel
    profile_info = None
    
    # Vérifier si nous sommes sur un sous-domaine d'organisation
    host = request.get_host().lower()
    if '.' in host and not host.startswith('www.') and 'martialcomp.com' in host:
        # Extraire le sous-domaine (par exemple: club-karate.martialcomp.com -> club-karate)
        subdomain = host.split('.')[0]
        
        # Essayer de trouver l'organisation correspondante
        try:
            from apps.multitenant.models import Tenant
            from apps.organizations.models import Organization
            
            # Trouver le tenant par slug (sous-domaine)
            tenant = Tenant.objects.filter(
                slug=subdomain,
                is_active=True
            ).first()
            
            if tenant:
                # Trouver l'organisation correspondante
                organization = Organization.objects.filter(
                    name=tenant.name,
                    is_active=True
                ).first()
                
                if organization:
                    profile_info = {
                        'role': f"Connexion Ã  {organization.name}",
                        'location': organization.address or "Lieu non spécifié",
                        'status': 'Actif' if organization.is_active else 'Inactif',
                        'status_class': 'active' if organization.is_active else 'inactive',
                        'valid_dates': None  # Peut Ãªtre étendu plus tard
                    }
        except ImportError:
            # Les modules ne sont pas disponibles
            pass
        except Exception:
            # Autres erreurs lors de la récupération de l'organisation
            pass
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Tentative d'authentification
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Récupérer l'URL de redirection
            next_url = request.POST.get('next')
            
            # Vérifier si next_url est sécurisé (non vide et interne au site)
            if next_url and not next_url.startswith('/'):
                next_url = None
                
            # Si aucune URL next ou URL invalide, rediriger vers le dashboard
            if not next_url:
                # Utiliser le système de nommage d'URL de Django au lieu d'un chemin en dur
                return redirect('competitions:dashboard:index')
            
            return redirect(next_url)
        else:
            messages.error(request, _("Identifiants invalides. Veuillez réessayer."))
    
    # Passer les informations de profil au template
    context = {
        'profile_info': profile_info
    }
    
    return render(request, 'registration/login.html', context)

def logout_view(request):
    """Vue de déconnexion utilisateur."""
    logout(request)
    messages.success(request, _("Vous Ãªtes maintenant déconnecté."))
    return redirect('welcome')

@transaction.atomic
def signup_view(request):
    """Vue d'inscription utilisateur."""
    # Rediriger si déjÃ  connecté
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('competitions:dashboard:index')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Créer l'utilisateur avec les données du formulaire
                user = form.save()
                
                # S'assurer que l'utilisateur a un profil
                try:
                    # Vérifier si un profil existe déjÃ 
                    profile = UserProfile.objects.get(user=user)
                    
                    # Si le profil existe, mettre Ã  jour ses attributs
                    profile.role = 'spectator'
                    profile.onboarding_step = 'role_selection'
                    profile.onboarding_completed = False
                    profile.save()
                except UserProfile.DoesNotExist:
                    # Créer un nouveau profil si nécessaire
                    profile = UserProfile.objects.create(
                        user=user,
                        role='spectator',
                        onboarding_step='role_selection',
                        onboarding_completed=False
                    )
                
                # Connecter l'utilisateur avec backend spécifique
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Message de bienvenue
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                
                # CORRECTION: Rediriger vers la page d'onboarding au lieu du dashboard
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Redirection de l'utilisateur {user.username} vers l'onboarding")
                
                # Rediriger vers la page de sélection de rÃ´le
                return redirect('competitions:onboarding:role_selection')
                    
            except IntegrityError as e:
                # Gérer spécifiquement l'erreur d'intégrité
                messages.error(request, _("Une erreur est survenue lors de la création du compte. Veuillez réessayer."))
                # Log l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur d'intégrité lors de la création du compte: {str(e)}")
                
            except Exception as e:
                # Gérer les autres exceptions
                messages.error(request, _("Une erreur inattendue est survenue. Veuillez réessayer."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la création du compte: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_view(request):
    """Vue de profil utilisateur avec gestion de la modification."""
    user = request.user
    
    # S'assurer que l'utilisateur a un profil
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user, 
            role='spectator',
            onboarding_step='role_selection',
            onboarding_completed=False
        )
    
    # Importer le formulaire de profil
    from ..forms.profile_forms import UserProfileForm
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Votre profil a été mis Ã  jour avec succès !"))
                return redirect('profile')
            except Exception as e:
                messages.error(request, _("Une erreur est survenue lors de la mise Ã  jour de votre profil."))
                # Log l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la mise Ã  jour du profil: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = UserProfileForm(instance=profile, user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'form': form,
    }
    
    return render(request, 'registration/profile.html', context)

@login_required
def password_change_view(request):
    """Vue de changement de mot de passe."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Importante pour maintenir la session utilisateur après changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, _("Votre mot de passe a été mis Ã  jour avec succès!"))
            return redirect('profile')
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/password_change.html', {
        'form': form
    })

