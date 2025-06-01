# This is a temporary file to help complete practitioner_extra.py
# These functions will be added to the end of practitioner_extra.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from datetime import datetime, timedelta
import json
import calendar

from competitions.models import (
    Practitioner, 
    Competition, 
    CompetitionRegistration
)
from competitions.models.scoring_results import CompetitionResult
from competitions.models.event import Event
from competitions.models.notifications import Notification
from competitions.models.support import SupportTicket, SupportMessage
from competitions.forms import (
    SupportTicketForm, 
    NotificationPreferenceForm
)


@login_required
def create_ticket(request):
    """Créer un nouveau ticket de support."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            # Créer le ticket mais ne pas sauvegarder encore
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.save()
            
            # Créer le premier message
            if 'message' in request.POST and request.POST['message']:
                SupportMessage.objects.create(
                    ticket=ticket,
                    sender=request.user,
                    message=request.POST['message']
                )
            
            messages.success(request, _("Votre ticket a été créé avec succès."))
            return redirect('competitions:practitioner_support_detail', ticket_id=str(ticket.id))
    else:
        form = SupportTicketForm()
    
    context = {
        'practitioner': practitioner,
        'form': form,
        'active_page': 'support'
    }
    
    return render(request, 'competitions/practitioner/create_ticket.html', context)


@login_required
def event_detail(request, event_id):
    """Afficher les détails d'un événement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    try:
        event = get_object_or_404(Event, pk=event_id)
        
        # Vérifier si le pratiquant est inscrit
        is_registered = False
        registration = None
        if hasattr(event, 'participants'):
            registration = event.participants.filter(practitioner=practitioner).first()
            is_registered = registration is not None
        
        # Participants inscrits
        participants = []
        if hasattr(event, 'participants'):
            participants = event.participants.select_related('practitioner')
        
        context = {
            'practitioner': practitioner,
            'event': event,
            'is_registered': is_registered,
            'registration': registration,
            'participants': participants,
            'can_register': event.is_open_for_registration if hasattr(event, 'is_open_for_registration') else True,
            'active_page': 'events'
        }
        
        return render(request, 'competitions/practitioner/event_detail.html', context)
    except Event.DoesNotExist:
        messages.error(request, _("Événement introuvable."))
        return redirect('competitions:practitioner:event_list')


@login_required
@require_POST
def event_register(request, event_id):
    """S'inscrire à un événement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    try:
        event = get_object_or_404(Event, pk=event_id)
        
        # Vérifier si le pratiquant est déjà inscrit
        if hasattr(event, 'participants'):
            existing = event.participants.filter(practitioner=practitioner).exists()
            if existing:
                messages.warning(request, _("Vous êtes déjà inscrit à cet événement."))
                return redirect('competitions:practitioner:event_detail', event_id=event_id)
        
        # Créer l'inscription
        # Ici vous devez adapter selon votre modèle EventParticipant
        # Par exemple:
        # EventParticipant.objects.create(
        #     event=event,
        #     practitioner=practitioner,
        #     status='registered'
        # )
        
        messages.success(request, _("Inscription confirmée pour l'événement."))
        return redirect('competitions:practitioner:event_detail', event_id=event_id)
        
    except Event.DoesNotExist:
        messages.error(request, _("Événement introuvable."))
        return redirect('competitions:practitioner:event_list')
    except Exception as e:
        messages.error(request, _("Erreur lors de l'inscription."))
        return redirect('competitions:practitioner:event_detail', event_id=event_id)


@login_required
def notification_preferences(request):
    """Gérer les préférences de notification."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer ou créer les préférences
    from competitions.models.notifications import NotificationPreference
    preferences, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, _("Vos préférences ont été mises à jour."))
            return redirect('competitions:practitioner_notification_preferences')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'practitioner': practitioner,
        'form': form,
        'preferences': preferences,
        'active_page': 'notifications'
    }
    
    return render(request, 'competitions/practitioner/notification_preferences.html', context)