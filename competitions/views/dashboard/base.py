from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ...models import UserProfile, Federation
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
        
        # Redirigez en fonction du rôle
        if profile.role == 'admin' and request.user.is_staff:
            return redirect('dashboard:admin')
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
            
            # 3. Si aucune fédération trouvée, rediriger vers la création ou la liste
            messages.warning(request, _("Vous n'êtes associé à aucune fédération. Créez-en une pour continuer."))
            
            # Rediriger vers la liste des fédérations pour permettre la création ou l'affiliation
            return redirect('competitions:federations:list')
            
        elif profile.role == 'club_manager':
            return redirect('dashboard:club')
        elif profile.role == 'judge' or profile.role == 'referee':
            return redirect('dashboard:referee')
        elif profile.role == 'coach':
            return redirect('dashboard:coach_multidiscipline')
        elif profile.role == 'participant':
            return redirect('dashboard:participant')
        else:
            # Rôle standard ou non reconnu
            return redirect('dashboard:spectator')
    except UserProfile.DoesNotExist:
        # Si l'utilisateur n'a pas de profil, créer un message d'erreur
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')
    except Exception as e:
        # Capture des erreurs génériques
        messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
        logger.error(f"Dashboard error: {str(e)}")
        return redirect('welcome')