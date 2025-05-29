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

@ensure_csrf_cookie
def login_view(request):
    """Vue de connexion utilisateur."""
    # Rediriger si déjà connecté
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
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
                return redirect('dashboard:index')
            
            return redirect(next_url)
        else:
            messages.error(request, _("Identifiants invalides. Veuillez réessayer."))
    
    return render(request, 'registration/login.html')

def logout_view(request):
    """Vue de déconnexion utilisateur."""
    logout(request)
    messages.success(request, _("Vous êtes maintenant déconnecté."))
    return redirect('welcome')

@transaction.atomic
def signup_view(request):
    """Vue d'inscription utilisateur."""
    # Rediriger si déjà connecté
    if request.user.is_authenticated:
        return redirect('dashboard:index')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Créer l'utilisateur avec les données du formulaire
                user = form.save()
                
                # S'assurer que l'utilisateur a un profil
                try:
                    # Vérifier si un profil existe déjà
                    profile = UserProfile.objects.get(user=user)
                    
                    # Si le profil existe, mettre à jour ses attributs
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
                
                # Connecter l'utilisateur
                login(request, user)
                
                # Message de bienvenue
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                
                # Rediriger vers le début du processus d'onboarding
                try:
                    return redirect('competitions:onboarding:start')  # Utiliser le namespace complet
                except Resolver404:
                    # Fallback si la première URL n'est pas trouvée
                    try:
                        return redirect('onboarding:start')
                    except Resolver404:
                        # Second fallback
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
    """Vue de profil utilisateur."""
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
    
    # Logique pour le formulaire de profil ici...
    # On utiliserait un ProfileForm pour gérer les mises à jour des données
    
    context = {
        'user': user,
        'profile': profile,
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
            messages.success(request, _("Votre mot de passe a été mis à jour avec succès!"))
            return redirect('profile')
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/password_change.html', {
        'form': form
    })