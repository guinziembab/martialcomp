from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _

from ...models import Club, Federation, FederationAdministrator
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@login_required
def handle_final_setup(request):
    """Finalisation de l'onboarding"""
    # Vérifier si l'utilisateur a un profil
    if not hasattr(request.user, 'profile'):
        messages.error(request, _("Profil utilisateur non trouvé."))
        return redirect('/')
    
    # Si l'utilisateur est déjÃ  passé par le processus, rediriger vers le tableau de bord
    if request.user.profile.onboarding_completed:
        messages.info(request, _("Votre compte est déjÃ  configuré."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer le rÃ´le depuis le profil
    role = request.user.profile.role
    
    # Définir les indications pour chaque rÃ´le
    next_steps = []
    
    if role == 'federation_admin':
        next_steps = [
            _("Configurez votre fédération en ajoutant plus de détails."),
            _("Créez des compétitions pour votre fédération."),
            _("Invitez des clubs Ã  rejoindre votre fédération.")
        ]
    elif role == 'club_manager':
        next_steps = [
            _("Configurez votre club en ajoutant plus de détails."),
            _("Inscrivez des membres Ã  votre club."),
            _("Inscrivez votre club aux compétitions.")
        ]
    elif role in ['referee', 'judge']:
        next_steps = [
            _("Complétez votre profil avec vos qualifications."),
            _("Inscrivez-vous comme juge pour les prochaines compétitions."),
            _("Consultez le calendrier des compétitions.")
        ]
    elif role == 'participant':
        next_steps = [
            _("Complétez votre profil avec vos informations sportives."),
            _("Inscrivez-vous aux prochaines compétitions."),
            _("Consultez les résultats des compétitions passées.")
        ]
    else:
        next_steps = [
            _("Explorez les compétitions Ã  venir."),
            _("Consultez les résultats des compétitions passées."),
            _("Suivez les clubs et athlètes qui vous intéressent.")
        ]
    
    # Récupérer le club ou la fédération associé Ã  l'utilisateur
    club = None
    federation = None
    
    if role == 'club_manager':
        club = Club.objects.filter(owner=request.user).first()
    elif role == 'federation_admin':
        try:
            # Chercher via les deux relations possibles
            federation = Federation.objects.filter(owner=request.user).first()
            if not federation:
                # Chercher aussi via la relation administrators
                federation = Federation.objects.filter(administrators__user=request.user).first()
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération de la fédération: {str(e)}")
    
    if request.method == 'POST':
        # Marquer l'onboarding comme terminé
        request.user.profile.onboarding_completed = True
        request.user.profile.save()
        
        # Supprimer l'étape d'onboarding de la session
        if 'onboarding_step' in request.session:
            del request.session['onboarding_step']
        
        messages.success(request, _("Configuration terminée avec succès !"))
        
        # Redirection personnalisée selon le rÃ´le
        try:
            if role == 'federation_admin' and federation:
                # Rediriger vers le tableau de bord spécifique de la fédération
                return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)
            elif role == 'club_manager' and club:
                # Rediriger vers le tableau de bord du club
                return redirect('competitions:club:dashboard')
            else:
                # Redirection par défaut
                return redirect('competitions:dashboard:index')
        except Exception as e:
            logger.error(f"Erreur de redirection: {str(e)}")
            return redirect('/')
    
    context = {
        'next_steps': next_steps,
        'role': role,
        'club': club,
        'federation': federation,
        'step': 'final_setup',
        'current_step': 'final_setup'
    }
    
    return render(request, 'competitions/onboarding/final_setup.html', context)
