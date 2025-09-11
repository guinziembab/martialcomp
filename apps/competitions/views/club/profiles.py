from django.core.exceptions import PermissionDenied
"""
Module pour la gestion des profils utilisateurs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from apps.competitions.models import Practitioner, Club
from .practitioners import get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

import logging
logger = logging.getLogger(__name__)

@login_required
def user_profile(request):
    """Affichage et modification du profil de l'utilisateur."""
    # Vérifier si l'utilisateur a un profil de pratiquant
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        # Rediriger vers le profil du pratiquant si existant
        return redirect('competitions:club:practitioner_profile')
    except Practitioner.DoesNotExist:
        pass
    
    # Récupérer le club associé à l'utilisateur
    club = get_user_club(request)
    
    context = {
        'user': request.user,
        'club': club,
        'page_title': _("Mon profil")
    }
    
    return render(request, 'competitions/club/profile.html', context)

@login_required
def practitioner_profile(request):
    """Affiche le profil du pratiquant associé à l'utilisateur connecté."""
    try:
        # Vérifier si la relation disciplines existe réellement dans le modèle
        prefetch_fields = []
        if hasattr(Practitioner, 'disciplines'):
            prefetch_fields.append('disciplines')
        if hasattr(Practitioner, 'qualifications'):
            prefetch_fields.append('qualifications')
        
        # Récupérer le pratiquant avec les relations appropriées
        if prefetch_fields:
            practitioner = Practitioner.objects.select_related('club', 'user').prefetch_related(*prefetch_fields).get(user=request.user)
        else:
            practitioner = Practitioner.objects.select_related('club', 'user').get(user=request.user)
        
        # Récupérer les inscriptions aux compétitions
        try:
            from ..models import CompetitionRegistration
            registrations = CompetitionRegistration.objects.filter(practitioner=practitioner)
        except ImportError:
            registrations = []
        
        return render(request, 'competitions/club/practitioner_profile.html', {
            'practitioner': practitioner,
            'registrations': registrations,
            'page_title': _("Mon profil de pratiquant")
        })
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'avez pas encore de profil de pratiquant."))
        return redirect('competitions:dashboard:index')
    except Exception as e:
        logger.error(f"Erreur lors de l'accès au profil du pratiquant: {str(e)}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de l'accès à votre profil: {}").format(str(e)))
        return redirect('competitions:dashboard:index')

@login_required
def update_practitioner_profile(request):
    """Permet à l'utilisateur de mettre à jour son propre profil de pratiquant."""
    try:
        practitioner = Practitioner.objects.get(user=request.user)
    except Practitioner.DoesNotExist:
        messages.error(request, _("Vous n'avez pas encore de profil de pratiquant."))
        return redirect('competitions:dashboard:index')
    
    if request.method == 'POST':
        # Seuls certains champs sont modifiables par l'utilisateur
        try:
            # Email
            if 'email' in request.POST and request.POST['email']:
                practitioner.email = request.POST['email']
            
            # Téléphone
            if 'phone' in request.POST:
                practitioner.phone = request.POST['phone']
            
            # Adresse
            if 'address' in request.POST:
                practitioner.address = request.POST['address']
            
            # Date de naissance
            if 'birth_date' in request.POST and request.POST['birth_date']:
                from datetime import datetime
                try:
                    birth_date = datetime.strptime(request.POST['birth_date'], '%Y-%m-%d').date()
                    practitioner.birth_date = birth_date
                except ValueError:
                    messages.error(request, _("Format de date invalide."))
                    return render(request, 'competitions/club/update_profile.html', {
                        'practitioner': practitioner,
                        'page_title': _("Modifier mon profil")
                    })
            
            practitioner.save()
            messages.success(request, _("Profil mis à jour avec succès."))
            return redirect('competitions:club:practitioner_profile')
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}", exc_info=True)
            messages.error(request, _("Une erreur est survenue lors de la mise à jour: {}").format(str(e)))
    
    return render(request, 'competitions/club/update_profile.html', {
        'practitioner': practitioner,
        'page_title': _("Modifier mon profil")
    })

