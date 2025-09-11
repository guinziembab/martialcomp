from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.urls import NoReverseMatch
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta
from ..models.users import UserProfile
from ..models.competitions import Competition
from ..models.discipline import Discipline
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

def welcome(request):
    # =========================================================
    # DÉTECTION TENANT - PRIORITÉ ABSOLUE
    # =========================================================
    
    # Si on est sur un sous-domaine tenant, rediriger vers la vue organization
    if hasattr(request, 'tenant') and request.tenant is not None:
        from apps.competitions.views.organization_sites import organization_site_view
        return organization_site_view(request)
    
    # Si l'utilisateur vient d'une page dashboard, ne pas rediriger
    referer = request.META.get('HTTP_REFERER', '')
    if 'dashboard' in referer:
        return render(request, 'competitions/welcome.html', get_welcome_context(request))
    
    # Si un paramètre no_redirect est présent, afficher simplement la page
    if request.GET.get('no_redirect'):
        return render(request, 'competitions/welcome.html', get_welcome_context(request))
    
    if request.user.is_authenticated:
        # Paramètre pour permettre de voir la page d'accueil même connecté
        if request.GET.get('show_welcome'):
            return render(request, 'competitions/welcome.html', get_welcome_context(request))
            
        try:
            # =========================================================
            # LOGIQUE D'ONBOARDING CORRIGÉE - PRIORITÉ ABSOLUE
            # =========================================================
            
            # Vérifier d'abord si l'utilisateur a un profil complet
            try:
                user_profile = UserProfile.objects.get(user=request.user)
                
                # Si le profil n'est pas complet ou onboarding pas terminé
                if not user_profile.onboarding_completed:
                    # Toujours permettre de voir la page d'accueil après connexion
                    # L'onboarding sera proposé via des boutons dans l'interface
                    if not request.session.get('onboarding_suggested'):
                        request.session['onboarding_suggested'] = True
                        messages.info(request, _("Bienvenue ! Pour profiter pleinement de la plateforme, nous vous invitons à compléter votre profil."))
                        return render(request, 'competitions/welcome.html', get_welcome_context(request))
                    
                    # Si l'utilisateur a déjà vu la suggestion et n'a pas fait l'onboarding,
                    # afficher la page d'accueil avec des liens vers l'onboarding
                    return render(request, 'competitions/welcome.html', get_welcome_context(request))
                        
            except UserProfile.DoesNotExist:
                # Pas de profil utilisateur, créer un profil minimal et afficher l'accueil
                UserProfile.objects.create(
                    user=request.user,
                    onboarding_completed=False
                )
                request.session['profile_initialized'] = True
                messages.info(request, _("Bienvenue ! Votre profil a été créé. Vous pouvez explorer la plateforme."))
                return render(request, 'competitions/welcome.html', get_welcome_context(request))
            
            # =========================================================
            # REDIRECTION DASHBOARD SEULEMENT SI ONBOARDING TERMINÉ
            # =========================================================
            
            # Onboarding terminé, redirection normale selon le rôle
            role = getattr(request.user, 'role', None)
            
            if role == 'club_manager':
                return redirect('competitions:dashboard:club')
            elif role == 'participant':
                return redirect('competitions:dashboard:participant')
            elif role == 'referee':
                return redirect('competitions:dashboard:referee')
            elif role == 'manager':
                return redirect('competitions:dashboard:manager')
            else:
                # Rôle spectateur ou non défini
                return redirect('competitions:dashboard:spectator')
                
        except Exception as e:
            # Log l'erreur et affiche la page d'accueil avec message informatif
            print(f"Erreur de redirection onboarding: {str(e)}")
            messages.warning(request, _("Bienvenue ! Veuillez compléter votre profil pour accéder à toutes les fonctionnalités."))
            return render(request, 'competitions/welcome.html', get_welcome_context(request))
    
    # Utilisateurs non connectés
    return render(request, 'competitions/welcome.html', get_welcome_context(request))

def get_welcome_context(request):
    """Récupère toutes les données nécessaires pour la page d'accueil"""
    context = {
        'page_title': _('Bienvenue sur MartialComp'),
        'meta_description': _('Plateforme de gestion des compétitions d\'arts martiaux'),
    }
    
    # Ajouter les compétitions publiques récentes
    try:
        recent_competitions = Competition.objects.filter(
            is_published=True,
            start_date__gte=timezone.now()
        ).order_by('start_date')[:6]
        context['recent_competitions'] = recent_competitions
    except Exception as e:
        print(f"Erreur lors de la récupération des compétitions: {e}")
        context['recent_competitions'] = []
    
    # Ajouter les disciplines populaires
    try:
        popular_disciplines = Discipline.objects.filter(
            is_active=True
        ).order_by('name')[:8]
        context['popular_disciplines'] = popular_disciplines
    except Exception as e:
        print(f"Erreur lors de la récupération des disciplines: {e}")
        context['popular_disciplines'] = []
    
    return context

def home(request):
    """Vue d'accueil alternative"""
    return welcome(request)

# Alias pour compatibilité
home_view = welcome


