"""
Module pour la gestion des profils utilisateurs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from competitions.models import Practitioner, Club
from .practitioners import get_user_club

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
            
            # Ville
            if 'city' in request.POST:
                practitioner.city = request.POST['city']
            
            # Code postal
            if 'postal_code' in request.POST:
                practitioner.postal_code = request.POST['postal_code']
            
            # Contact d'urgence
            if 'emergency_contact_name' in request.POST:
                practitioner.emergency_contact_name = request.POST['emergency_contact_name']
            
            if 'emergency_contact_phone' in request.POST:
                practitioner.emergency_contact_phone = request.POST['emergency_contact_phone']
            
            # Poids et taille (avec validation)
            if 'weight' in request.POST and request.POST['weight']:
                try:
                    weight = float(request.POST['weight'])
                    if 20 <= weight <= 250:  # Valeurs raisonnables
                        practitioner.weight = weight
                except ValueError:
                    pass
            
            if 'height' in request.POST and request.POST['height']:
                try:
                    height = float(request.POST['height'])
                    if 100 <= height <= 250:  # Valeurs raisonnables
                        practitioner.height = height
                except ValueError:
                    pass
            
            # Informations médicales
            if 'blood_group' in request.POST:
                practitioner.blood_group = request.POST['blood_group']
            
            if 'allergies' in request.POST:
                practitioner.allergies = request.POST['allergies']
            
            if 'medical_conditions' in request.POST:
                practitioner.medical_conditions = request.POST['medical_conditions']
            
            # Photo
            if 'photo' in request.FILES:
                practitioner.photo = request.FILES['photo']
            
            # Sauvegarde
            practitioner.save()
            
            messages.success(request, _("Votre profil a été mis à jour avec succès."))
            return redirect('competitions:club:practitioner_profile')
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}", exc_info=True)
            messages.error(request, _("Une erreur est survenue lors de la mise à jour de votre profil: {}").format(str(e)))
    
    return render(request, 'competitions/club/edit_practitioner_profile.html', {
        'practitioner': practitioner,
        'page_title': _("Modifier mon profil")
    })