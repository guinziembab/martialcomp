from django.core.exceptions import PermissionDenied
"""
Vue d'inscription simplifiée pour contourner les problèmes d'allauth
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.views.decorators.csrf import csrf_protect
from ..models import UserProfile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@csrf_protect
@transaction.atomic
def simple_signup_view(request):
    """
    Vue d'inscription simplifiée qui évite allauth.
    """
    if request.user.is_authenticated:
        return redirect('competitions:onboarding:role_selection')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation simple
        errors = []
        
        if not username or len(username) < 3:
            errors.append(_("Le nom d'utilisateur doit contenir au moins 3 caractères."))
        
        if User.objects.filter(username=username).exists():
            errors.append(_("Ce nom d'utilisateur existe déjÃ ."))
        
        if not email:
            errors.append(_("L'email est requis."))
        
        if User.objects.filter(email=email).exists():
            errors.append(_("Cet email est déjÃ  utilisé."))
        
        if not password1 or len(password1) < 8:
            errors.append(_("Le mot de passe doit contenir au moins 8 caractères."))
        
        if password1 != password2:
            errors.append(_("Les mots de passe ne correspondent pas."))
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            try:
                # Créer l'utilisateur
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password1
                )
                logger.info(f"âœ… Utilisateur {username} créé avec succès")
                
                # Créer ou récupérer le profil (au cas oÃ¹ un signal l'aurait déjÃ  créé)
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'role': 'spectator',
                        'onboarding_step': 'role_selection',
                        'onboarding_completed': False
                    }
                )
                if created:
                    logger.info(f"âœ… Profil créé pour {username}: {profile.role}")
                else:
                    # Mettre Ã  jour le profil existant
                    profile.role = 'spectator'
                    profile.onboarding_step = 'role_selection'
                    profile.onboarding_completed = False
                    profile.save()
                    logger.info(f"âœ… Profil mis Ã  jour pour {username}: {profile.role}")
                
                # Connecter l'utilisateur avec backend explicite
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                logger.info(f"âœ… Utilisateur {username} connecté avec succès")
                
                # Message de succès
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                
                # Redirection vers l'onboarding
                logger.info(f"ðŸ”„ Redirection vers l'onboarding pour {username}")
                return redirect('competitions:onboarding:role_selection')
                
            except Exception as e:
                logger.error(f"âŒ Erreur lors de la création du compte {username}: {str(e)}")
                import traceback
                logger.error(f"âŒ Traceback: {traceback.format_exc()}")
                messages.error(request, _("Une erreur est survenue lors de la création du compte. Veuillez réessayer."))
    
    return render(request, 'competitions/simple_signup.html', {
        'title': _("Créer un compte - Simple"),
    })

def simple_login_view(request):
    """
    Vue de connexion simplifiée pour test.
    """
    if request.user.is_authenticated:
        # Vérifier l'onboarding
        try:
            profile = request.user.profile
            if not profile.onboarding_completed:
                return redirect('competitions:onboarding:role_selection')
            else:
                return redirect('competitions:dashboard:index')
        except:
            return redirect('competitions:onboarding:role_selection')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                # Vérifier l'onboarding
                try:
                    profile = user.profile
                    if not profile.onboarding_completed:
                        return redirect('competitions:onboarding:role_selection')
                    else:
                        return redirect('competitions:dashboard:index')
                except:
                    return redirect('competitions:onboarding:role_selection')
            else:
                messages.error(request, _("Identifiants incorrects."))
        else:
            messages.error(request, _("Veuillez remplir tous les champs."))
    
    return render(request, 'competitions/simple_login.html', {
        'title': _("Se connecter - Simple"),
    })
