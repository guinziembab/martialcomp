from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.urls import reverse, NoReverseMatch

from ...models import UserProfile
from ...forms.onboarding import RoleSelectionForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def handle_role_selection(request):
    """Gestion de la sélection du rôle dans le processus d'onboarding."""
    try:
        # Récupérer ou créer le profil utilisateur
        try:
            profile = UserProfile.objects.get(user=request.user)
            if getattr(profile, 'onboarding_completed', False):
                messages.info(request, _("Votre compte est déjà configuré."))
                
                # Redirection vers dashboard approprié selon le rôle
                role = getattr(profile, 'role', 'spectator')
                if role == 'club_manager':
                    return redirect('/dashboard/club/')
                elif role == 'judge':
                    return redirect('/dashboard/referee/')
                elif role == 'participant':
                    return redirect('/dashboard/participant/')
                else:
                    return redirect('/dashboard/')
                    
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=request.user, 
                role='spectator',
                onboarding_step='role_selection'
            )
            logger.info(f"Profil créé pour utilisateur {request.user.username}")
    
        if request.method == 'POST':
            form = RoleSelectionForm(request.POST)
            if form.is_valid():
                role = form.cleaned_data['role']
                
                # Mettre à jour le rôle dans le profil
                profile.role = role
                
                # Définir l'étape suivante en fonction du rôle
                if role == 'federation_admin':
                    profile.onboarding_step = 'federation'
                    profile.save()
                    request.session['onboarding_step'] = 'federation'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:federation')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/federation/')
                        
                elif role == 'club_manager':
                    profile.onboarding_step = 'club_creation'
                    profile.save()
                    request.session['onboarding_step'] = 'club_creation'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:club_creation')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/club/creation/')
                        
                elif role == 'judge':
                    profile.onboarding_step = 'judge_profile'
                    profile.save()
                    request.session['onboarding_step'] = 'judge_profile'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:judge_profile')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/judge/')
                        
                elif role == 'coach':
                    # Utiliser la version ultra-simplifiée qui contourne les problèmes de modèle
                    profile.onboarding_step = 'coach_profile_simplified'
                    profile.save()
                    request.session['onboarding_step'] = 'coach_profile_simplified'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:coach_profile_simplified')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/coach/')
                        
                elif role == 'participant':
                    profile.onboarding_step = 'participant_profile'
                    profile.save()
                    request.session['onboarding_step'] = 'participant_profile'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:participant_profile')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/participant/')
                        
                elif role == 'external_organizer':
                    profile.onboarding_step = 'external_organizer_profile'
                    profile.save()
                    request.session['onboarding_step'] = 'external_organizer_profile'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:external_organizer_profile')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/external_organizer/')
                        
                else:
                    # Pour les autres rôles (spectateur, etc.), passer directement à l'étape finale
                    profile.onboarding_step = 'final_setup'
                    profile.save()
                    request.session['onboarding_step'] = 'final_setup'
                    
                    # Redirection avec fallback
                    try:
                        return redirect('competitions:onboarding:final_setup')
                    except NoReverseMatch:
                        return redirect('/competitions/onboarding/final/')
                
                # Messages avec encodage correct
                messages.success(request, _("Rôle sélectionné avec succès"))
                logger.info(f"Utilisateur {request.user.username} a sélectionné le rôle: {role}")
            else:
                messages.error(request, _("Rôle invalide sélectionné"))
        else:
            # Créer le formulaire pour GET
            form = RoleSelectionForm()
        
        # Contexte pour le template
        context = {
            'form': form,
            'step': 'role_selection',
            'current_step': 'role_selection',
            'profile': profile,
            'available_roles': [
                {
                    'key': 'participant', 
                    'name': _('Participant'), 
                    'description': _('Je participe aux compétitions'),
                    'icon': 'fas fa-user-ninja'
                },
                {
                    'key': 'club_manager', 
                    'name': _('Gestionnaire de club'), 
                    'description': _('Je gère un club'),
                    'icon': 'fas fa-users-cog'
                },
                {
                    'key': 'judge', 
                    'name': _('Juge/Arbitre'), 
                    'description': _('Je juge les compétitions'),
                    'icon': 'fas fa-gavel'
                },
                {
                    'key': 'coach', 
                    'name': _('Entraîneur'), 
                    'description': _('J\'entraîne des pratiquants'),
                    'icon': 'fas fa-chalkboard-teacher'
                },
                {
                    'key': 'federation_admin', 
                    'name': _('Administrateur fédération'), 
                    'description': _('Je gère une fédération'),
                    'icon': 'fas fa-building'
                },
                {
                    'key': 'external_organizer', 
                    'name': _('Organisateur externe'), 
                    'description': _('J\'organise des événements'),
                    'icon': 'fas fa-calendar-alt'
                },
                {
                    'key': 'spectator', 
                    'name': _('Spectateur'), 
                    'description': _('Je regarde les compétitions'),
                    'icon': 'fas fa-eye'
                },
            ]
        }
        
        return render(request, 'competitions/onboarding/role_selection.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans handle_role_selection: {e}")
        messages.error(request, _("Une erreur est survenue lors de la sélection du rôle"))
        
        # Redirection de secours
        try:
            return redirect('/dashboard/')
        except:
            return redirect('/')