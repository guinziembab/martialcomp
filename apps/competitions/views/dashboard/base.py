from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ...models import UserProfile, Federation
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
import logging
logger = logging.getLogger('django')

@login_required
def dashboard(request):
    """
    Vue principale qui redirige vers le tableau de bord approprié 
    selon le rôle de l'utilisateur.
    """
    logger.debug(f"Dashboard called: User={request.user.username}, Path={request.path}, Method={request.method}")
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        logger.debug(f"User {request.user.username} has role: {profile.role}")
        
        # Vérifier d'abord si l'utilisateur a un mode dashboard en session
        dashboard_mode = request.session.get('dashboard_mode')
        
        # Si l'utilisateur est pratiquant, vérifier s'il a un profil juge
        if profile.role == 'participant':
            from ...models import Practitioner, Judge
            judge_profile = None
            
            # Vérifier d'abord s'il y a un profil Judge directement lié à l'utilisateur
            try:
                judge_profile = Judge.objects.get(user=request.user)
                logger.info(f"User {request.user.username} has direct judge profile")
            except Judge.DoesNotExist:
                # Sinon, vérifier via le profil pratiquant
                try:
                    practitioner = Practitioner.objects.get(user=request.user)
                    judge_profile = Judge.objects.get(practitioner=practitioner)
                    logger.info(f"User {request.user.username} has judge profile via practitioner")
                except (Practitioner.DoesNotExist, Judge.DoesNotExist):
                    pass
            
            if judge_profile:
                # Si un mode dashboard est défini en session, l'utiliser
                if dashboard_mode == 'judge':
                    return redirect('competitions:dashboard:referee')
                elif dashboard_mode == 'participant':
                    return redirect('competitions:dashboard:participant')
                
                # Sinon, si l'utilisateur a un profil juge mais pas de mode en session,
                # le rediriger vers le dashboard juge par défaut
                request.session['dashboard_mode'] = 'judge'
                logger.info(f"User {request.user.username} has judge profile, redirecting to referee dashboard")
                return redirect('competitions:dashboard:referee')
            else:
                # Pas de profil juge, continuer comme pratiquant normal
                if dashboard_mode == 'judge':
                    # Réinitialiser le mode si le profil n'existe pas
                    request.session['dashboard_mode'] = 'participant'
        
        # Redirigez en fonction du rôle
        if profile.role == 'admin' and request.user.is_staff:
            return redirect('competitions:dashboard:admin')
        elif profile.role == 'federation_admin':
            # Vérification améliorée pour trouver les fédérations associées à l'utilisateur
            federation = None
            
            # 1. Vérifier via la relation d'administrateur
            from ...models import FederationAdministrator
            admin_roles = FederationAdministrator.objects.filter(user=request.user)
            
            if admin_roles.exists():
                federation_admin = admin_roles.filter(is_primary=True).first() or admin_roles.first()
                federation = federation_admin.federation
                logger.info(f"Found federation {federation.id} for admin {request.user.username}")
                # Utiliser le namespace correct pour la redirection
                return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
                
            # 2. Vérifier via la relation owner
            try:
                federation = Federation.objects.get(owner=request.user)
                logger.info(f"Found federation {federation.id} owned by {request.user.username}")
                # Assurer l'existence d'une entrée FederationAdministrator
                FederationAdministrator.objects.get_or_create(
                    user=request.user,
                    federation=federation,
                    defaults={'role': 'owner', 'is_primary': True}
                )
                return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
            except Federation.DoesNotExist:
                logger.warning(f"No federation found for owner {request.user.username}")
                pass
            
            # 3. Si aucune fédération trouvée, rediriger vers l'index des fédérations qui gère mieux ce cas
            messages.warning(request, _("Vous n'êtes associé à aucune fédération. Créez-en une pour continuer."))
            
            # Rediriger vers le dashboard des fédérations
            return redirect('competitions:dashboard:federations')
            
        elif profile.role == 'club_manager':
            return redirect('competitions:dashboard:club')
        elif profile.role == 'event_manager':
            return redirect('competitions:dashboard:manager')
        elif profile.role == 'judge' or profile.role == 'referee':
            return redirect('competitions:dashboard:referee')
        elif profile.role == 'coach':
            return redirect('competitions:dashboard:coach')
        elif profile.role == 'participant':
            return redirect('competitions:dashboard:participant')
        else:
            # Rôle standard ou non reconnu
            return redirect('competitions:dashboard:spectator')
    except UserProfile.DoesNotExist:
        # Si l'utilisateur n'a pas de profil, créer un message d'erreur
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')
    except Exception as e:
        # Capture des erreurs génériques
        messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
        logger.error(f"Dashboard error: {str(e)}")
        return redirect('welcome')
