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
from shop.models import Order, OrderItem
from competitions.models.support import SupportTicket, SupportMessage
from competitions.forms import (
    SupportTicketForm,
    NotificationPreferenceForm
)


@login_required
def practitioner_orders(request):
    """Vue pour le suivi des commandes boutique du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer les commandes de l'utilisateur
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    # Statistiques
    order_stats = {
        'total': orders.count(),
        'pending': orders.filter(status='pending').count(),
        'processing': orders.filter(status='processing').count(),
        'shipped': orders.filter(status='shipped').count(),
        'delivered': orders.filter(status='delivered').count(),
        'cancelled': orders.filter(status='cancelled').count(),
    }
    
    context = {
        'practitioner': practitioner,
        'orders': orders,
        'order_stats': order_stats,
        'status_filter': status_filter,
        'active_page': 'orders'
    }
    
    return render(request, 'competitions/practitioner/orders.html', context)


@login_required
def practitioner_order_detail(request, order_id):
    """Vue détaillée d'une commande spécifique."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'practitioner': practitioner,
        'order': order,
        'active_page': 'orders'
    }
    
    return render(request, 'competitions/practitioner/order_detail.html', context)


@login_required
def practitioner_create_ticket(request):
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
def practitioner_notification_preferences(request):
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


@login_required
def practitioner_notifications(request):
    """Vue des notifications du pratiquant."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer les notifications
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Marquer les notifications non lues comme lues
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    # Compter par type
    notification_stats = {
        'total': notifications.count(),
        'competition': notifications.filter(type='competition').count(),
        'order': notifications.filter(type='order').count(),
        'grade': notifications.filter(type='grade').count(),
        'membership': notifications.filter(type='membership').count(),
        'system': notifications.filter(type='system').count(),
    }
    
    context = {
        'practitioner': practitioner,
        'notifications': notifications[:50],  # Limiter à 50 dernières
        'notification_stats': notification_stats,
        'active_page': 'notifications'
    }
    
    return render(request, 'competitions/practitioner/notifications.html', context)


@login_required
@require_POST
def practitioner_notification_mark_read(request, notification_id):
    """Marquer une notification comme lue."""
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        user=request.user
    )
    notification.is_read = True
    notification.save()
    
    return JsonResponse({'status': 'success'})


@login_required
def practitioner_support(request):
    """Vue pour le support et les demandes d'information."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer les tickets de support
    tickets = SupportTicket.objects.filter(
        user=request.user
    ).order_by('-created_at')
    
    # Traitement du formulaire de nouveau ticket
    if request.method == 'POST':
        subject = request.POST.get('subject')
        category = request.POST.get('category')
        message = request.POST.get('message')
        
        if subject and category and message:
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                category=category,
                status='open'
            )
            
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message
            )
            
            messages.success(request, _("Votre demande a été envoyée avec succès."))
            return redirect('competitions:practitioner_support_detail', ticket_id=ticket.id)
    
    # Statistiques
    ticket_stats = {
        'total': tickets.count(),
        'open': tickets.filter(status='open').count(),
        'in_progress': tickets.filter(status='in_progress').count(),
        'closed': tickets.filter(status='closed').count(),
    }
    
    context = {
        'practitioner': practitioner,
        'tickets': tickets,
        'ticket_stats': ticket_stats,
        'active_page': 'support'
    }
    
    return render(request, 'competitions/practitioner/support.html', context)


@login_required
def practitioner_support_detail(request, ticket_id):
    """Vue détaillée d'un ticket de support."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    ticket = get_object_or_404(SupportTicket, id=ticket_id, user=request.user)
    
    # Traitement de nouveau message
    if request.method == 'POST':
        message = request.POST.get('message')
        if message:
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message
            )
            
            # Réouvrir le ticket si fermé
            if ticket.status == 'closed':
                ticket.status = 'open'
                ticket.save()
            
            messages.success(request, _("Message envoyé avec succès."))
            return redirect('competitions:practitioner_support_detail', ticket_id=ticket.id)
    
    # Récupérer les messages
    messages_list = ticket.messages.order_by('created_at')
    
    context = {
        'practitioner': practitioner,
        'ticket': ticket,
        'messages': messages_list,
        'active_page': 'support'
    }
    
    return render(request, 'competitions/practitioner/support_detail.html', context)


@login_required
def practitioner_events(request):
    """Vue des événements et alertes."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer les événements à venir
    upcoming_events = Event.objects.filter(
        Q(organization=practitioner.organization) | Q(is_public=True),
        start_date__gte=timezone.now().date()
    ).order_by('start_date')
    
    # Événements par type
    events_by_type = {
        'competition': upcoming_events.filter(event_type='competition'),
        'training': upcoming_events.filter(event_type='training'),
        'seminar': upcoming_events.filter(event_type='seminar'),
        'meeting': upcoming_events.filter(event_type='meeting'),
        'other': upcoming_events.filter(event_type='other'),
    }
    
    # Alertes personnalisées
    alerts = []
    
    # Alerte certificat médical
    if practitioner.medical_certificate_date:
        medical_expiry = practitioner.medical_certificate_date + timedelta(days=365)
        days_until_expiry = (medical_expiry - timezone.now().date()).days
        
        if days_until_expiry <= 30:
            alerts.append({
                'type': 'warning' if days_until_expiry > 0 else 'danger',
                'title': _("Certificat médical"),
                'message': _("Expire dans {} jours").format(days_until_expiry) if days_until_expiry > 0 
                          else _("Expiré depuis {} jours").format(abs(days_until_expiry)),
                'icon': 'fa-file-medical',
                'action': _("Renouveler")
            })
    
    # Alerte adhésion
    if practitioner.membership_end_date:
        days_until_membership_end = (practitioner.membership_end_date - timezone.now().date()).days
        
        if days_until_membership_end <= 30:
            alerts.append({
                'type': 'warning' if days_until_membership_end > 0 else 'danger',
                'title': _("Adhésion"),
                'message': _("Expire dans {} jours").format(days_until_membership_end) if days_until_membership_end > 0 
                          else _("Expirée depuis {} jours").format(abs(days_until_membership_end)),
                'icon': 'fa-id-card',
                'action': _("Renouveler")
            })
    
    # Alertes compétitions
    upcoming_competitions = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition__start_date__gte=timezone.now().date(),
        competition__start_date__lte=timezone.now().date() + timedelta(days=7)
    )
    
    for registration in upcoming_competitions:
        days_until = (registration.competition.start_date - timezone.now().date()).days
        alerts.append({
            'type': 'info',
            'title': registration.competition.name,
            'message': _("Dans {} jours").format(days_until),
            'icon': 'fa-trophy',
            'action': _("Voir détails")
        })
    
    context = {
        'practitioner': practitioner,
        'upcoming_events': upcoming_events,
        'events_by_type': events_by_type,
        'alerts': alerts,
        'active_page': 'events'
    }
    
    return render(request, 'competitions/practitioner/events.html', context)


@login_required
def practitioner_calendar(request):
    """Vue du calendrier complet des activités."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer le mois et l'année depuis les paramètres
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    
    # Calculer le mois précédent et suivant
    if month == 1:
        prev_month, prev_year = 12, year - 1
        next_month, next_year = 2, year
    elif month == 12:
        prev_month, prev_year = 11, year
        next_month, next_year = 1, year + 1
    else:
        prev_month, prev_year = month - 1, year
        next_month, next_year = month + 1, year
    
    # Créer le calendrier
    cal = calendar.monthcalendar(year, month)
    
    # Récupérer tous les événements du mois
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    
    # Événements
    events = Event.objects.filter(
        Q(organization=practitioner.organization) | Q(is_public=True),
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    
    # Compétitions inscrites
    registrations = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition__start_date__lte=end_date,
        competition__end_date__gte=start_date
    )
    
    # Créer un dictionnaire d'événements par jour
    events_by_day = {}
    
    for event in events:
        current = event.start_date
        while current <= event.end_date and current <= end_date:
            if current.month == month:
                if current.day not in events_by_day:
                    events_by_day[current.day] = []
                events_by_day[current.day].append({
                    'type': 'event',
                    'title': event.title,
                    'time': event.start_time,
                    'color': event.color or 'primary'
                })
            current += timedelta(days=1)
    
    for registration in registrations:
        current = registration.competition.start_date
        while current <= registration.competition.end_date and current <= end_date:
            if current.month == month:
                if current.day not in events_by_day:
                    events_by_day[current.day] = []
                events_by_day[current.day].append({
                    'type': 'competition',
                    'title': registration.competition.name,
                    'time': registration.competition.start_time,
                    'color': 'success'
                })
            current += timedelta(days=1)
    
    context = {
        'practitioner': practitioner,
        'calendar': cal,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'events_by_day': events_by_day,
        'active_page': 'calendar'
    }
    
    return render(request, 'competitions/practitioner/calendar.html', context)


@login_required
def practitioner_calendar_api(request):
    """API pour récupérer les événements du calendrier."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            return JsonResponse({'error': 'No practitioner profile'}, status=404)
    except:
        return JsonResponse({'error': 'Error retrieving profile'}, status=500)
    
    # Récupérer les dates de début et fin
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    if not start or not end:
        return JsonResponse({'error': 'Missing start or end date'}, status=400)
    
    try:
        start_date = datetime.fromisoformat(start).date()
        end_date = datetime.fromisoformat(end).date()
    except:
        return JsonResponse({'error': 'Invalid date format'}, status=400)
    
    # Récupérer les événements
    events = []
    
    # Événements généraux
    general_events = Event.objects.filter(
        Q(organization=practitioner.organization) | Q(is_public=True),
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    
    for event in general_events:
        events.append({
            'id': f'event_{event.id}',
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': (event.end_date + timedelta(days=1)).isoformat(),
            'color': event.color or '#007bff',
            'url': f'/competitions/event/{event.id}/'
        })
    
    # Compétitions
    competitions = Competition.objects.filter(
        start_date__lte=end_date,
        end_date__gte=start_date
    )
    
    registered_competitions = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition__in=competitions
    ).values_list('competition_id', flat=True)
    
    for competition in competitions:
        is_registered = competition.id in registered_competitions
        events.append({
            'id': f'competition_{competition.id}',
            'title': competition.name,
            'start': competition.start_date.isoformat(),
            'end': (competition.end_date + timedelta(days=1)).isoformat(),
            'color': '#28a745' if is_registered else '#6c757d',
            'url': f'/competitions/competitions/{competition.id}/',
            'classNames': ['competition', 'registered' if is_registered else 'not-registered']
        })
    
    return JsonResponse(events, safe=False)


@login_required
def practitioner_create_ticket_alt(request):
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
        subject = request.POST.get('subject')
        category = request.POST.get('category', 'general')
        priority = request.POST.get('priority', 'medium')
        message = request.POST.get('message')
        
        if subject and message:
            # Créer le ticket
            ticket = SupportTicket.objects.create(
                user=request.user,
                subject=subject,
                category=category,
                priority=priority,
                status='open'
            )
            
            # Ajouter le premier message
            SupportMessage.objects.create(
                ticket=ticket,
                sender=request.user,
                message=message
            )
            
            messages.success(request, _("Votre ticket a été créé avec succès."))
            
            # Créer une notification
            Notification.objects.create(
                user=request.user,
                type='system',
                title=_("Ticket créé"),
                message=_("Votre ticket #{} a été créé avec succès.").format(ticket.id),
                is_read=False
            )
            
            return redirect('competitions:practitioner_support_detail', ticket_id=ticket.id)
        else:
            messages.error(request, _("Veuillez remplir tous les champs obligatoires."))
    
    context = {
        'practitioner': practitioner,
        'active_page': 'support',
        'categories': [
            ('general', _('Général')),
            ('technical', _('Technique')),
            ('billing', _('Facturation')),
            ('competition', _('Compétition')),
            ('training', _('Formation')),
            ('other', _('Autre'))
        ],
        'priorities': [
            ('low', _('Basse')),
            ('medium', _('Moyenne')),
            ('high', _('Haute')),
            ('urgent', _('Urgente'))
        ]
    }
    
    return render(request, 'competitions/practitioner/create_ticket.html', context)


@login_required
def practitioner_event_detail(request, event_id):
    """Afficher les détails d'un événement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    # Récupérer l'événement
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions d'accès
    if not event.is_public and event.organization != practitioner.organization:
        messages.error(request, _("Vous n'avez pas accès à cet événement."))
        return redirect('competitions:practitioner_events')
    
    # Vérifier si le pratiquant est inscrit
    is_registered = event.participants.filter(id=practitioner.id).exists()
    
    # Compter les participants
    participant_count = event.participants.count()
    spots_available = event.max_participants - participant_count if event.max_participants else None
    
    # Récupérer les informations supplémentaires
    registration_deadline_passed = False
    if event.registration_deadline:
        registration_deadline_passed = timezone.now() > event.registration_deadline
    
    can_register = (
        not is_registered and 
        not registration_deadline_passed and 
        (spots_available is None or spots_available > 0)
    )
    
    context = {
        'practitioner': practitioner,
        'event': event,
        'is_registered': is_registered,
        'participant_count': participant_count,
        'spots_available': spots_available,
        'can_register': can_register,
        'registration_deadline_passed': registration_deadline_passed,
        'active_page': 'events'
    }
    
    return render(request, 'competitions/practitioner/event_detail.html', context)


@login_required
def practitioner_event_register(request, event_id):
    """S'inscrire à un événement."""
    try:
        practitioner = request.user.practitioners.first()
        if not practitioner:
            messages.error(request, _("Aucun profil de pratiquant trouvé."))
            return redirect('competitions:home')
    except Exception as e:
        messages.error(request, _("Erreur lors de la récupération du profil."))
        return redirect('competitions:home')
    
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not event.is_public and event.organization != practitioner.organization:
        messages.error(request, _("Vous n'avez pas accès à cet événement."))
        return redirect('competitions:practitioner_events')
    
    # Vérifier la date limite d'inscription
    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.error(request, _("La date limite d'inscription est dépassée."))
        return redirect('competitions:practitioner_event_detail', event_id=event.id)
    
    # Vérifier si déjà inscrit
    if event.participants.filter(id=practitioner.id).exists():
        messages.warning(request, _("Vous êtes déjà inscrit à cet événement."))
        return redirect('competitions:practitioner_event_detail', event_id=event.id)
    
    # Vérifier les places disponibles
    if event.max_participants:
        current_count = event.participants.count()
        if current_count >= event.max_participants:
            messages.error(request, _("Il n'y a plus de places disponibles pour cet événement."))
            return redirect('competitions:practitioner_event_detail', event_id=event.id)
    
    # Inscription
    event.participants.add(practitioner)
    event.save()
    
    # Créer une notification
    Notification.objects.create(
        user=request.user,
        type='system',
        title=_("Inscription confirmée"),
        message=_("Votre inscription à l'événement '{}' a été confirmée.").format(event.title),
        is_read=False
    )
    
    messages.success(request, _("Votre inscription a été confirmée."))
    
    # Redirection selon le type d'événement
    if event.event_type == 'competition':
        return redirect('competitions:competitions', competition_id=event.competition.id)
    else:
        return redirect('competitions:practitioner_event_detail', event_id=event.id)


# La fonction notification_preferences a été supprimée pour éviter les duplications.
# Utilisez practitioner_notification_preferences à la place.