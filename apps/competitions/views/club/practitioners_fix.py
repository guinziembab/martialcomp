"""
Vue corrigée pour la gestion des pratiquants - Fix 403 error
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q

logger = logging.getLogger(__name__)

def get_user_organization_and_club(request):
    """Obtenir à la fois l'organisation et le club de l'utilisateur"""
    try:
        user = request.user
        
        # 1. Via le middleware
        if hasattr(request, 'user_organization') and request.user_organization:
            organization = request.user_organization
            # Trouver le club associé
            from apps.competitions.models import Club
            club = Club.objects.filter(organization=organization, owner=user).first()
            if not club:
                club = Club.objects.filter(organization=organization).first()
            return organization, club
        
        # 2. Via UserProfile
        from apps.competitions.models.users import UserProfile
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.organization:
                organization = profile.organization
                from apps.competitions.models import Club
                club = Club.objects.filter(organization=organization, owner=user).first()
                if not club:
                    club = Club.objects.filter(organization=organization).first()
                return organization, club
        except UserProfile.DoesNotExist:
            pass
        
        # 3. Via Club ownership
        from apps.competitions.models import Club
        owned_club = Club.objects.filter(owner=user).select_related('organization').first()
        if owned_club:
            return owned_club.organization, owned_club
        
        return None, None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération org/club: {str(e)}")
        return None, None

@login_required
def practitioner_create_fixed(request):
    """Version corrigée de practitioner_create"""
    try:
        logger.info(f"practitioner_create_fixed appelé par {request.user.username}")
        
        # Récupérer organisation ET club
        organization, club = get_user_organization_and_club(request)
        
        logger.info(f"Organisation trouvée: {organization}")
        logger.info(f"Club trouvé: {club}")
        
        if not organization:
            messages.error(request, _("Vous n'êtes associé à aucune organisation. Contactez un administrateur."))
            return redirect('competitions:dashboard:dashboard')
        
        # Import tardif pour éviter les imports circulaires
        from apps.competitions.forms import PractitionerForm
        from apps.competitions.models import Practitioner
        
        if request.method == 'POST':
            form = PractitionerForm(request.POST, request.FILES)
            if form.is_valid():
                practitioner = form.save(commit=False)
                practitioner.organization = organization
                practitioner.save()
                
                messages.success(request, _(f"Le pratiquant {practitioner.full_name} a été créé avec succès."))
                return redirect('competitions:club:practitioners')
        else:
            form = PractitionerForm()
        
        context = {
            'form': form,
            'club': club if club else organization,  # Utiliser club si disponible, sinon organisation
            'organization': organization,
            'page_title': _("Ajouter un Pratiquant"),
        }
        
        return render(request, 'competitions/club/practitioner_form.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans practitioner_create_fixed: {str(e)}", exc_info=True)
        messages.error(request, _(f"Erreur lors de la création du pratiquant: {str(e)}"))
        return redirect('competitions:club:practitioners')