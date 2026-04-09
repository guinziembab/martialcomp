from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count
from datetime import timedelta
import csv
import io

from apps.competitions.models.event import (
    Event,
    EventParticipant,
    EventOccurrence,
    EventOccurrenceAttendance,
    OccurrenceStatus,
    AttendanceStatus,
)
from apps.competitions.models.event_feedback import EventFeedback
from apps.competitions.models.club import Club
from apps.competitions.models.practitioners import Practitioner
from apps.competitions.forms.event_forms import (
    EventForm,
    EventFilterForm,
    EventParticipantForm,
    PublicEventRegistrationForm,
    OccurrenceEditForm,
    OccurrenceCancelForm,
    OccurrenceAttendanceForm,
)
from apps.competitions.forms.event_feedback import EventFeedbackForm
from apps.competitions.forms.event_import_export import EventImportForm, EventExportForm
from apps.competitions.forms.event_notifications import EventNotificationForm
from apps.competitions.utils.decorators import club_required, federation_required
from apps.competitions.utils.permission_helpers import get_user_club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def event_list(request):
    """Liste tous les événements disponibles avec filtres"""
    # Logique d'affichage des événements selon les permissions
    try:
        # Déterminer les événements Ã  afficher selon le rÃ´le
        if request.user.is_staff or request.user.is_superuser:
            # Staff/Admin : voir tous les événements non archivés
            events = Event.objects.filter(is_archived=False)
            
            # Inclure les événements archivés si demandé
            if request.GET.get('include_archived'):
                events = get_organization_queryset(Event, request.user)
        else:
            # Utilisateurs normaux : seulement les événements publics non archivés
            events = Event.objects.filter(is_public=True, is_archived=False)
            
            # Inclure les événements archivés publics si demandé
            if request.GET.get('include_archived'):
                events = Event.objects.filter(is_public=True)
        
        # Si l'utilisateur a une organisation, inclure aussi les événements de son organisation
        user_organization = None
        try:
            if hasattr(request.user, 'userprofile') and request.user.userprofile.organization:
                user_organization = request.user.userprofile.organization
                # Ajouter les événements de l'organisation de l'utilisateur
                if not (request.user.is_staff or request.user.is_superuser):
                    if request.GET.get('include_archived'):
                        org_events = Event.objects.filter(organization=user_organization)
                    else:
                        org_events = Event.objects.filter(organization=user_organization, is_archived=False)
                    # Utiliser distinct() au lieu de union() pour éviter les erreurs
                    combined_ids = list(events.values_list('id', flat=True)) + list(org_events.values_list('id', flat=True))
                    events = Event.objects.filter(id__in=combined_ids).distinct()
        except (AttributeError, Exception) as e:
            # Log l'erreur mais continue avec les événements publics
            print(f"Erreur accès organisation utilisateur: {e}")
            
    except Exception as e:
        # En cas d'erreur, retourner une liste vide avec message d'erreur
        events = Event.objects.none()
        messages.error(request, _("Erreur lors du chargement des événements. Veuillez contacter l'administrateur."))
        print(f"ERREUR CRITIQUE event_list: {e}")
    
    # user_organization déjÃ  défini ci-dessus
    
    # Filtrage
    filter_form = EventFilterForm(request.GET or None, user=request.user)
    if filter_form.is_valid():
        if filter_form.cleaned_data.get('search'):
            events = events.filter(title__icontains=filter_form.cleaned_data['search'])
        if filter_form.cleaned_data.get('type'):
            events = events.filter(event_type=filter_form.cleaned_data['type'])
        if filter_form.cleaned_data.get('start_date'):
            events = events.filter(start_date__gte=filter_form.cleaned_data['start_date'])
        if filter_form.cleaned_data.get('end_date'):
            events = events.filter(end_date__lte=filter_form.cleaned_data['end_date'])
        if filter_form.cleaned_data.get('organization'):
            events = events.filter(organization=filter_form.cleaned_data['organization'])
    
    # Division par statut pour faciliter l'affichage
    today = timezone.now().date()
    
    upcoming_events = events.filter(start_date__gte=today).order_by('start_date')
    ongoing_events = events.filter(start_date__lte=today, end_date__gte=today).order_by('end_date')
    past_events = events.filter(end_date__lt=today).order_by('-end_date')
    
    # Pagination
    paginator_upcoming = Paginator(upcoming_events, 10)
    paginator_ongoing = Paginator(ongoing_events, 5)
    paginator_past = Paginator(past_events, 10)
    
    page = request.GET.get('page', 1)
    
    # Récupérer toutes les organisations pour les filtres
    from apps.organizations.models import Organization
    # Organization model doesn't have an 'organization' field, so get all organizations for now
    organizations = Organization.objects.all()
    
    # Ajouter les informations de permissions pour chaque événement
    for event in events:
        event.user_can_manage = (
            request.user == event.created_by or 
            request.user.is_staff or
            (hasattr(request.user, 'userprofile') and 
             request.user.userprofile.role in ['club_manager', 'federation_admin', 'coach'])
        )
    
    context = {
        'events': events,  # Tous les événements pour l'affichage principal
        'upcoming_events': paginator_upcoming.get_page(page),
        'ongoing_events': paginator_ongoing.get_page(page),
        'past_events': paginator_past.get_page(page),
        'filter_form': filter_form,
        'user_organization': user_organization,
        'organizations': organizations,
    }
    
    return render(request, 'competitions/events/event_list.html', context)


@login_required
def create_event(request):
    """Création d'un nouvel événement"""
    # Vérifier que l'utilisateur a un club
    user_club = None
    try:
        if hasattr(request.user, 'userprofile'):
            user_club = request.user.userprofile.organization
            # Vérifier aussi si l'utilisateur est admin d'un club avec la méthode is_club_admin
            if not user_club and hasattr(request.user, 'is_club_admin'):
                if request.user.is_club_admin():
                    # L'utilisateur est admin d'un club, on autorise
                    user_club = True
    except:
        pass
    
    # Vérifier les permissions pour créer un événement
    can_create = False
    if request.user.is_staff:
        can_create = True
    elif hasattr(request.user, 'userprofile'):
        profile = request.user.userprofile
        # Autoriser les responsables de club, fédération et coaches
        if profile.role in ['club_manager', 'federation_admin', 'coach']:
            can_create = True
        # Autoriser si l'utilisateur a un club associé
        elif user_club:
            can_create = True
    
    if not can_create:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer un événement. RÃ´les autorisés : Responsable de club, Responsable de fédération, Coach."))
        return redirect('competitions:events:event_list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            # Assigner l'organisation si pas spécifiée avant de sauvegarder
            if not form.cleaned_data.get('organization') and user_club and user_club is not True:
                form.instance.organization = user_club

            # Utiliser la méthode save() du formulaire qui gère la récurrence
            event = form.save(commit=True)

            # Message de succès adapté
            if event.is_recurring:
                occurrences_count = event.occurrences.count()
                messages.success(
                    request,
                    _("L'événement récurrent a été créé avec succès. {count} occurrences ont été générées.").format(
                        count=occurrences_count
                    )
                )
            else:
                messages.success(request, _("L'événement a été créé avec succès."))

            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        # Pré-remplir l'organisation si l'utilisateur en a une
        initial = {}
        if user_club and user_club is not True:  # Vérifier que user_club est un objet Club
            initial['organization'] = user_club

        form = EventForm(initial=initial, user=request.user)
    
    context = {
        'form': form,
        'is_new': True,
    }
    
    return render(request, 'competitions/events/event_form.html', context)


def event_detail(request, event_id):
    """
    Affiche les détails d'un événement.
    Accessible publiquement pour permettre l'inscription aux stages/séminaires.
    """
    event = get_object_or_404(Event, id=event_id)

    # Vérifier si l'utilisateur est déjà inscrit (seulement si authentifié)
    user_registration = None
    is_organizer = False
    is_club_admin = False
    can_edit = False
    club_participants = []
    is_club_manager = False
    user_club = None

    if request.user.is_authenticated:
        try:
            user_registration = EventParticipant.objects.filter(
                event=event,
                user=request.user
            ).first()
        except:
            pass

        # Seul le créateur peut éditer/supprimer
        is_organizer = (request.user == event.created_by)
        can_edit = is_organizer

        # Récupérer les inscrits du club pour les responsables de club
        user_club = get_user_club(request)
        if user_club:
            is_club_manager = True
            club_org = user_club.organization or getattr(user_club, 'as_organization', None)
            if club_org:
                # Trouver les user_ids des pratiquants du club
                from apps.competitions.models.practitioners import Practitioner
                club_user_ids = list(
                    Practitioner.objects.filter(
                        organization=club_org,
                        user__isnull=False
                    ).values_list('user_id', flat=True)
                )
                # Chercher les participants inscrits via user, practitioner OU guest_club
                from django.db.models import Q
                # Noms du club pour matcher les invités
                club_names = [user_club.name]
                if club_org.name and club_org.name != user_club.name:
                    club_names.append(club_org.name)
                guest_q = Q()
                for cn in club_names:
                    guest_q |= Q(is_guest=True, guest_club__iexact=cn)
                club_participants_qs = EventParticipant.objects.filter(
                    event=event
                ).filter(
                    Q(practitioner__organization=club_org) |
                    Q(user_id__in=club_user_ids) |
                    guest_q
                ).exclude(
                    status='cancelled'
                ).select_related('practitioner', 'user').distinct()
                # Enrichir : attacher le practitioner du club quand manquant
                user_to_pract = dict(
                    Practitioner.objects.filter(
                        organization=club_org,
                        user_id__in=club_user_ids
                    ).values_list('user_id', 'id')
                )
                pract_cache = {}
                for p in club_participants_qs:
                    if not p.practitioner and p.user_id and p.user_id in user_to_pract:
                        pract_id = user_to_pract[p.user_id]
                        if pract_id not in pract_cache:
                            pract_cache[pract_id] = Practitioner.objects.get(id=pract_id)
                        p.practitioner = pract_cache[pract_id]
                club_participants = list(club_participants_qs)

    context = {
        'event': event,
        'user_registration': user_registration,
        'can_edit': can_edit,
        'user_can_edit': can_edit,
        'user_can_view_participants': can_edit or is_club_manager,
        'can_register': not user_registration and event.registration_required,
        'registration_closed': event.registration_deadline and event.registration_deadline < timezone.now(),
        'is_authenticated': request.user.is_authenticated,
        'is_club_manager': is_club_manager,
        'club_participants': club_participants,
        'user_club': user_club,
    }

    return render(request, 'competitions/events/event_detail.html', context)


@login_required
def edit_event(request, event_id):
    """Modifier un événement existant"""
    event = get_object_or_404(Event, id=event_id)
    
    # Seul le créateur peut modifier
    if request.user != event.created_by:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Stocker si c'était déjà récurrent avant modification
    was_recurring = event.is_recurring

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event, user=request.user)
        if form.is_valid():
            event = form.save()

            # Si l'événement devient récurrent ou si les paramètres de récurrence changent
            if event.is_recurring:
                if not was_recurring:
                    # Nouvellement récurrent - générer les occurrences
                    event.generate_occurrences(months_ahead=6)
                    occurrences_count = event.occurrences.count()
                    messages.success(
                        request,
                        _("L'événement a été mis à jour et rendu récurrent. {count} occurrences ont été générées.").format(
                            count=occurrences_count
                        )
                    )
                else:
                    messages.success(request, _("L'événement récurrent a été mis à jour avec succès."))
            else:
                messages.success(request, _("L'événement a été mis à jour avec succès."))

            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event, user=request.user)
    
    context = {
        'form': form,
        'event': event,
        'is_new': False,
    }
    
    return render(request, 'competitions/events/event_form.html', context)


@login_required
def delete_event(request, event_id):
    """Supprimer un événement"""
    event = get_object_or_404(Event, id=event_id)

    # Vérifier les permissions : créateur OU manager/admin de l'organisation
    can_delete = (request.user == event.created_by)
    if not can_delete and event.organization:
        try:
            from apps.organizations.models import OrganizationMember
            can_delete = OrganizationMember.objects.filter(
                user=request.user,
                organization=event.organization,
                role__in=['manager', 'admin', 'owner'],
                is_active=True
            ).exists()
        except Exception:
            pass
    if not can_delete:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour supprimer cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)

    if request.method == 'POST':
        event_name = event.title
        event.delete()
        messages.success(request, _("L'événement « {} » a été supprimé avec succès.").format(event_name))
        # Redirect to dashboard if coming from there, otherwise event list
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('competitions:events:event_list')
    
    return render(request, 'competitions/events/delete_event.html', {
        'event': event,
    })


@login_required
def archive_event(request, event_id):
    """Archiver un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not (request.user == event.created_by or request.user.is_staff):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour archiver cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        event.is_archived = True
        event.archived_at = timezone.now()
        event.save()
        messages.success(request, _("L'événement a été archivé avec succès."))
        return redirect('competitions:events:event_list')
    
    return render(request, 'competitions/events/archive_event.html', {
        'event': event,
    })


@login_required
def unarchive_event(request, event_id):
    """Désarchiver un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not (request.user == event.created_by or request.user.is_staff):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour désarchiver cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    event.is_archived = False
    event.archived_at = None
    event.save()
    messages.success(request, _("L'événement a été désarchivé avec succès."))
    return redirect('competitions:events:event_detail', event_id=event.id)


def public_register_for_event(request, event_id):
    """
    Inscription publique a un evenement (sans compte MartialComp).
    Permet aux visiteurs de s'inscrire a des stages, seminaires, etc.
    """
    event = get_object_or_404(Event, id=event_id)

    # Verifier si l'inscription est encore possible
    if event.registration_deadline and event.registration_deadline < timezone.now():
        messages.error(request, _("La date limite d'inscription est depassee."))
        return redirect('competitions:events:event_detail', event_id=event.id)

    # Verifier si l'evenement est complet
    if event.max_participants and event.participants.count() >= event.max_participants:
        messages.error(request, _("Cet evenement est complet."))
        return redirect('competitions:events:event_detail', event_id=event.id)

    # Si l'utilisateur est connecte, rediriger vers l'inscription normale
    if request.user.is_authenticated:
        return redirect('competitions:events:register_for_event', event_id=event.id)

    if request.method == 'POST':
        form = PublicEventRegistrationForm(request.POST, event=event)
        if form.is_valid():
            # Creer l'inscription guest
            registration = EventParticipant(
                event=event,
                is_guest=True,
                guest_first_name=form.cleaned_data['first_name'],
                guest_last_name=form.cleaned_data['last_name'],
                guest_email=form.cleaned_data['email'],
                guest_phone=form.cleaned_data.get('phone', ''),
                guest_club=form.cleaned_data.get('club', ''),
                guest_grade=form.cleaned_data.get('grade', ''),
                notes=form.cleaned_data.get('notes', ''),
                status='registered'
            )

            # Si l'evenement est plein, mettre sur liste d'attente
            if event.max_participants and event.participants.count() >= event.max_participants:
                registration.status = 'waitlist'
                messages.info(request, _(
                    "L'evenement est complet, vous avez ete ajoute a la liste d'attente."
                ))
            else:
                messages.success(request, _(
                    "Votre inscription a ete enregistree avec succes !"
                ))

            registration.save()
            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        form = PublicEventRegistrationForm(event=event)

    return render(request, 'competitions/events/public_register.html', {
        'event': event,
        'form': form,
    })


@login_required
def register_for_event(request, event_id):
    """Inscription Ã  un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier si l'inscription est encore possible
    if event.registration_deadline and event.registration_deadline < timezone.now():
        messages.error(request, _("La date limite d'inscription est dépassée."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'événement est complet
    if event.max_participants and event.participants.count() >= event.max_participants:
        messages.error(request, _("Cet événement est complet."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'utilisateur est déjÃ  inscrit
    if EventParticipant.objects.filter(event=event, user=request.user).exists():
        messages.info(request, _("Vous Ãªtes déjÃ  inscrit Ã  cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventParticipantForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.user = request.user
            
            # Si l'événement est plein, mettre sur liste d'attente
            if event.max_participants and event.participants.count() >= event.max_participants:
                registration.status = 'waitlist'
                messages.info(request, _("L'événement est complet, vous avez été ajouté Ã  la liste d'attente."))
            else:
                messages.success(request, _("Votre inscription a été enregistrée avec succès."))
            
            registration.save()
            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        form = EventParticipantForm()
    
    return render(request, 'competitions/events/register.html', {
        'event': event,
        'form': form,
    })


@login_required
def cancel_registration(request, event_id, registration_id):
    """Annulation d'une inscription Ã  un événement"""
    event = get_object_or_404(Event, id=event_id)
    registration = get_object_or_404(EventParticipant, id=registration_id, event=event)
    
    # Vérifier les permissions
    if not (
        registration.user == request.user or
        request.user == event.created_by or
        request.user.is_staff or
        (hasattr(request.user, 'userprofile') and 
         request.user.userprofile.role == 'club_admin' and
         request.user.userprofile.organization == event.organization)
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour annuler cette inscription."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        registration.delete()
        
        # Si une personne sur liste d'attente existe, la passer en "inscrite"
        if event.max_participants:
            waitlist = EventParticipant.objects.filter(event=event, status='waitlist').order_by('registered_at').first()
            if waitlist:
                waitlist.status = 'registered'
                waitlist.save()
                
                # Notification (Ã  implémenter selon les besoins)
                pass
        
        messages.success(request, _("L'inscription a été annulée avec succès."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    return render(request, 'competitions/events/cancel_registration.html', {
        'event': event,
        'registration': registration,
    })


@login_required
@club_required
def event_participants(request, event_id):
    """Gestion des participants Ã  un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérification des permissions
    if not (
        request.user == event.created_by or (
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role in ['club_admin', 'federation_admin'] and
            event.organization == getattr(request.user.userprofile, 'organization', None)
        )
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour gérer les participants."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Récupérer tous les participants
    participants = event.participants.all().select_related('user')
    
    context = {
        'event': event,
        'participants': participants,
        'can_edit': True,  # DéjÃ  vérifié par la condition ci-dessus
    }
    
    return render(request, 'competitions/events/participants.html', context)


@login_required
def submit_feedback(request, event_id):
    """Soumettre un feedback pour un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier si l'événement est terminé
    today = timezone.now().date()
    if event.end_date > today:
        messages.error(request, _("Vous ne pouvez pas soumettre un feedback pour un événement qui n'est pas encore terminé."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'utilisateur était inscrit Ã  l'événement
    if not EventParticipant.objects.filter(event=event, user=request.user).exists():
        messages.error(request, _("Vous devez Ãªtre inscrit Ã  cet événement pour soumettre un feedback."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'utilisateur a déjÃ  soumis un feedback
    if EventFeedback.objects.filter(event=event, submitted_by=request.user).exists():
        messages.info(request, _("Vous avez déjÃ  soumis un feedback pour cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventFeedbackForm(request.POST, event_type=event.event_type)
        if form.is_valid():
            # Créer et enregistrer le feedback
            feedback = EventFeedback(
                event=event,
                submitted_by=request.user,
                overall_satisfaction=form.cleaned_data['overall_satisfaction'],
                organization_rating=form.cleaned_data['organization_rating'],
                content_quality=form.cleaned_data['content_quality'],
                location_rating=form.cleaned_data['location_rating'],
                would_recommend=form.cleaned_data['would_recommend'],
                highlights=form.cleaned_data.get('highlights', ''),
                improvements=form.cleaned_data.get('improvements', ''),
                additional_comments=form.cleaned_data.get('additional_comments', ''),
                allow_testimonial=form.cleaned_data.get('allow_testimonial', False)
            )
            
            # Ajouter les champs conditionnels en fonction du type d'événement
            if 'value_for_money' in form.cleaned_data:
                feedback.value_for_money = form.cleaned_data['value_for_money']
                
            if 'competition_fairness' in form.cleaned_data:
                feedback.competition_fairness = form.cleaned_data['competition_fairness']
                
            if 'instructor_knowledge' in form.cleaned_data:
                feedback.instructor_knowledge = form.cleaned_data['instructor_knowledge']
                
            if 'material_usefulness' in form.cleaned_data:
                feedback.material_usefulness = form.cleaned_data['material_usefulness']
                
            if 'exam_difficulty' in form.cleaned_data:
                feedback.exam_difficulty = form.cleaned_data['exam_difficulty']
            
            feedback.save()
            
            messages.success(request, _("Merci pour votre feedback!"))
            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        form = EventFeedbackForm(event_type=event.event_type)
    
    return render(request, 'competitions/events/feedback_form.html', {
        'event': event,
        'form': form
    })


@login_required
def feedback_results(request, event_id):
    """Affiche les résultats des feedbacks pour un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not (
        request.user == event.created_by or
        request.user.is_staff or
        (hasattr(request.user, 'userprofile') and
         request.user.userprofile.role in ['club_admin', 'federation_admin'] and
         event.organization == getattr(request.user.userprofile, 'organization', None))
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour voir les feedbacks."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Récupérer tous les feedbacks
    feedbacks = EventFeedback.objects.filter(event=event).select_related('submitted_by')
    
    # Calculer les statistiques
    stats = {
        'count': feedbacks.count(),
        'averages': {
            'overall': 0,
            'organization': 0,
            'content': 0,
            'location': 0,
            'value': 0,
        },
        'would_recommend': {
            'yes': 0,
            'maybe': 0,
            'no': 0,
        }
    }
    
    if feedbacks:
        # Calculer les moyennes
        stats['averages']['overall'] = sum(f.overall_satisfaction for f in feedbacks) / feedbacks.count()
        stats['averages']['organization'] = sum(f.organization_rating for f in feedbacks) / feedbacks.count()
        stats['averages']['content'] = sum(f.content_quality for f in feedbacks) / feedbacks.count()
        stats['averages']['location'] = sum(f.location_rating for f in feedbacks) / feedbacks.count()
        
        # Value for money (facultatif)
        value_feedbacks = [f.value_for_money for f in feedbacks if f.value_for_money is not None]
        if value_feedbacks:
            stats['averages']['value'] = sum(value_feedbacks) / len(value_feedbacks)
        
        # Recommandations
        for rec in ['yes', 'maybe', 'no']:
            stats['would_recommend'][rec] = feedbacks.filter(would_recommend=rec).count()
    
    return render(request, 'competitions/events/feedback_results.html', {
        'event': event,
        'feedbacks': feedbacks,
        'stats': stats
    })


@login_required
def import_events(request):
    """Importer des événements depuis un fichier CSV"""
    # Vérifier les permissions (administrateur du club)
    if not (request.user.is_staff or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'club_admin')):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour importer des événements."))
        return redirect('competitions:events:event_list')
    
    if request.method == 'POST':
        form = EventImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Lire le fichier CSV
            try:
                # Détecter l'encodage
                csv_file_data = csv_file.read()
                csv_file.close()
                
                # Essayer d'abord UTF-8
                try:
                    decoded_data = csv_file_data.decode('utf-8')
                except UnicodeDecodeError:
                    # Si UTF-8 échoue, essayer ISO-8859-1
                    decoded_data = csv_file_data.decode('iso-8859-1')
                
                # Créer un reader CSV
                csv_reader = csv.DictReader(io.StringIO(decoded_data))
                
                events_created = 0
                events_failed = 0
                
                for row in csv_reader:
                    try:
                        # Récupérer le club si spécifié
                        club = None
                        club_id = row.get('club_id')
                        if club_id:
                            try:
                                club = Club.objects.get(id=club_id)
                            except Club.DoesNotExist:
                                pass
                        
                        # Créer l'événement
                        event = Event(
                            title=row.get('title', ''),
                            description=row.get('description', ''),
                            event_type=row.get('event_type', 'other'),
                            club=club,
                            start_date=parse_date(row.get('start_date')),
                            end_date=parse_date(row.get('end_date')),
                            location=row.get('location', ''),
                            created_by=request.user
                        )
                        
                        # Traiter les champs facultatifs
                        if 'registration_deadline' in row and row['registration_deadline']:
                            deadline_date = parse_date(row['registration_deadline'])
                            if deadline_date:
                                event.registration_deadline = timezone.datetime.combine(
                                    deadline_date,
                                    timezone.datetime.min.time()
                                )
                        
                        if 'max_participants' in row and row['max_participants']:
                            try:
                                event.max_participants = int(row['max_participants'])
                            except ValueError:
                                pass
                        
                        if 'price' in row and row['price']:
                            try:
                                event.price = float(row['price'])
                            except ValueError:
                                pass
                        
                        event.save()
                        events_created += 1
                        
                    except Exception as e:
                        # Enregistrer l'erreur pour le debug
                        print(f"Erreur lors de l'importation: {str(e)}")
                        events_failed += 1
                
                if events_created > 0:
                    messages.success(request, _("{} événements importés avec succès.").format(events_created))
                
                if events_failed > 0:
                    messages.warning(request, _("{} événements n'ont pas pu Ãªtre importés.").format(events_failed))
                
                return redirect('competitions:events:event_list')
                
            except Exception as e:
                messages.error(request, _("Erreur lors de l'importation: {}").format(str(e)))
    else:
        form = EventImportForm()
    
    return render(request, 'competitions/events/import_events.html', {
        'form': form,
    })


@login_required
def export_events(request):
    """Exporter des événements au format CSV"""
    # Vérifier les permissions
    if not (request.user.is_staff or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'club_admin')):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour exporter des événements."))
        return redirect('competitions:events:event_list')
    
    if request.method == 'POST':
        form = EventExportForm(request.POST)
        if form.is_valid():
            # Filtrer les événements
            events = get_organization_queryset(Event, request.user)
            
            if form.cleaned_data.get('start_date'):
                events = events.filter(start_date__gte=form.cleaned_data['start_date'])
            
            if form.cleaned_data.get('end_date'):
                events = events.filter(end_date__lte=form.cleaned_data['end_date'])
            
            if form.cleaned_data.get('event_type'):
                events = events.filter(event_type=form.cleaned_data['event_type'])
            
            if form.cleaned_data.get('organization'):
                events = events.filter(organization=form.cleaned_data['organization'])
            
            # Créer le fichier CSV
            response = JsonResponse({
                'success': True,
                'message': _("{} événements prÃªts Ã  Ãªtre exportés.").format(events.count()),
                'export_url': request.build_absolute_uri(reverse('competitions:events:download_export'))
            })
            
            # Stocker les IDs des événements Ã  exporter en session
            request.session['export_event_ids'] = [str(event.id) for event in events]
            
            return response
    else:
        form = EventExportForm()
    
    return render(request, 'competitions/events/export_events.html', {
        'form': form,
    })


@login_required
def event_notify(request, event_id):
    """Envoyer une notification aux participants d'un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not (
        request.user == event.created_by or
        request.user.is_staff or
        (hasattr(request.user, 'userprofile') and
         request.user.userprofile.role in ['club_admin', 'federation_admin'] and
         event.organization == getattr(request.user.userprofile, 'organization', None))
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour envoyer des notifications."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Récupérer les participants
    participants = event.participants.all().select_related('user')
    
    if not participants.exists():
        messages.warning(request, _("Cet événement n'a pas encore de participants."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventNotificationForm(request.POST)
        if form.is_valid():
            # Envoyer les notifications (Ã  implémenter selon vos besoins)
            # ...
            
            messages.success(request, _("Notification envoyée avec succès."))
            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        form = EventNotificationForm()
    
    return render(request, 'competitions/events/notify.html', {
        'form': form,
        'event': event,
        'participants': participants,
    })


# Fonction utilitaire pour parser les dates depuis un CSV
def parse_date(date_str):
    """Parse une date Ã  partir d'une chaÃ®ne de caractères"""
    if not date_str:
        return None
    
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']
    
    for fmt in formats:
        try:
            from datetime import datetime
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


@login_required
def edit_participant(request, event_id, participant_id):
    """
    Modifie les informations d'un participant Ã  un événement.
    """
    event = get_object_or_404(Event, id=event_id)
    participant = get_object_or_404(EventParticipant, id=participant_id, event=event)
    
    # Vérifier les permissions
    if not (
        request.user == event.created_by or (
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role in ['club_admin', 'federation_admin'] and
            event.organization == getattr(request.user.userprofile, 'organization', None)
        )
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier les participants."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            participant = form.save()
            messages.success(request, _("Les informations du participant ont été mises Ã  jour."))
            return redirect('competitions:events:event_participants', event_id=event_id)
    else:
        form = EventParticipantForm(instance=participant)
    
    return render(request, 'competitions/events/edit_participant.html', {
        'event': event,
        'participant': participant,
        'form': form
    })


@login_required
def remove_participant(request, event_id, participant_id):
    """
    Supprime un participant d'un événement.
    """
    event = get_object_or_404(Event, id=event_id)
    participant = get_object_or_404(EventParticipant, id=participant_id, event=event)
    
    # Vérifier les permissions
    if not (
        request.user == event.created_by or (
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role in ['club_admin', 'federation_admin'] and
            event.organization == getattr(request.user.userprofile, 'organization', None)
        )
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour supprimer des participants."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        participant.delete()
        messages.success(request, _("Le participant a été supprimé de l'événement."))
        return redirect('competitions:events:event_participants', event_id=event_id)
    
    return render(request, 'competitions/events/remove_participant.html', {
        'event': event,
        'participant': participant
    })


@login_required
def event_feedback(request, event_id):
    """
    Affiche le formulaire de feedback pour un événement.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier que l'utilisateur est participant Ã  l'événement
    if not EventParticipant.objects.filter(event=event, user=request.user).exists():
        messages.error(request, _("Vous devez Ãªtre inscrit Ã  l'événement pour donner votre avis."))
        return redirect('competitions:events:event_detail', event_id=event_id)
    
    # Vérifier si l'utilisateur a déjÃ  soumis un feedback
    if EventFeedback.objects.filter(event=event, submitted_by=request.user).exists():
        messages.info(request, _("Vous avez déjÃ  soumis un feedback pour cet événement."))
        return redirect('competitions:events:event_detail', event_id=event_id)
    
    if request.method == 'POST':
        form = EventFeedbackForm(request.POST, event=event, user=request.user)
        if form.is_valid():
            feedback = EventFeedback(
                event=event,
                submitted_by=request.user,
                overall_satisfaction=form.cleaned_data.get('overall_satisfaction'),
                organization_rating=form.cleaned_data.get('organization_rating'),
                content_quality=form.cleaned_data.get('content_quality'),
                location_rating=form.cleaned_data.get('location_rating'),
                value_for_money=form.cleaned_data.get('value_for_money'),
                would_recommend=form.cleaned_data.get('would_recommend'),
                highlights=form.cleaned_data.get('highlights', ''),
                improvements=form.cleaned_data.get('improvements', ''),
                additional_comments=form.cleaned_data.get('additional_comments', ''),
                allow_testimonial=form.cleaned_data.get('allow_testimonial', False),
            )
            
            # Ajouter les champs spécifiques au type d'événement si présents
            if 'competition_fairness' in form.cleaned_data:
                feedback.competition_fairness = form.cleaned_data.get('competition_fairness')
            if 'instructor_knowledge' in form.cleaned_data:
                feedback.instructor_knowledge = form.cleaned_data.get('instructor_knowledge')
            if 'material_usefulness' in form.cleaned_data:
                feedback.material_usefulness = form.cleaned_data.get('material_usefulness')
            if 'exam_difficulty' in form.cleaned_data:
                feedback.exam_difficulty = form.cleaned_data.get('exam_difficulty')
                
            feedback.save()
            messages.success(request, _("Merci pour votre feedback !"))
            return redirect('competitions:events:event_detail', event_id=event_id)
    else:
        form = EventFeedbackForm(event=event, user=request.user)

    return render(request, 'competitions/events/feedback_form.html', {
        'event': event,
        'form': form
    })


# =============================================================================
# VUES POUR LES OCCURRENCES D'ÉVÉNEMENTS RÉCURRENTS
# =============================================================================

@login_required
def recurrence_preview(request):
    """
    API pour prévisualiser les dates d'un événement récurrent.
    Utilisé en AJAX lors de la création d'un événement.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY, YEARLY, MO, TU, WE, TH, FR, SA, SU
        import json
        import calendar

        # Parser le JSON du body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            # Fallback sur request.POST pour compatibilité
            data = request.POST

        # Récupérer les paramètres
        start_date_str = data.get('start_date')
        start_time_str = data.get('start_time', '00:00')
        frequency = data.get('frequency')
        days = data.get('recurrence_days', data.get('days', []))
        end_type = data.get('end_type', 'never')
        end_after = data.get('end_after')
        end_date_str = data.get('end_date')

        # Options mensuelles avancées
        monthly_type = data.get('monthly_type', 'day_of_month')
        week_of_month = data.get('week_of_month')
        day_of_week = data.get('day_of_week')
        day_of_month = data.get('day_of_month')

        if not start_date_str or not frequency:
            return JsonResponse({'error': 'Missing parameters: start_date and frequency required'}, status=400)

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        # Mapping des jours (0=lundi, 6=dimanche pour Python)
        day_map = {'MO': 0, 'TU': 1, 'WE': 2, 'TH': 3, 'FR': 4, 'SA': 5, 'SU': 6}
        day_objects = {'MO': MO, 'TU': TU, 'WE': WE, 'TH': TH, 'FR': FR, 'SA': SA, 'SU': SU}

        # Générer les 10 prochaines dates
        dates = []
        current_date = start_date
        end_gen = start_date + relativedelta(months=6)
        max_dates = 10

        if end_type == 'after' and end_after:
            max_dates = min(int(end_after), 10)
        elif end_type == 'on_date' and end_date_str:
            end_gen = min(
                datetime.strptime(end_date_str, '%Y-%m-%d').date(),
                end_gen
            )

        # Utiliser dateutil.rrule pour générer les dates
        if frequency == 'daily':
            rule = rrule(DAILY, dtstart=start_date, until=end_gen, count=max_dates)
            dates = [d.strftime('%Y-%m-%d') for d in rule]

        elif frequency in ['weekly', 'biweekly']:
            interval = 2 if frequency == 'biweekly' else 1

            if days:
                # Jours spécifiques de la semaine
                byweekday = [day_map[d] for d in days if d in day_map]
                rule = rrule(
                    WEEKLY,
                    dtstart=start_date,
                    until=end_gen,
                    interval=interval,
                    byweekday=byweekday,
                    count=max_dates
                )
            else:
                rule = rrule(
                    WEEKLY,
                    dtstart=start_date,
                    until=end_gen,
                    interval=interval,
                    count=max_dates
                )
            dates = [d.strftime('%Y-%m-%d') for d in rule]

        elif frequency == 'monthly':
            if monthly_type == 'nth_weekday' and week_of_month and day_of_week:
                # N-ième jour de la semaine du mois (ex: 3ème dimanche)
                week_num = int(week_of_month)
                day_obj = day_objects.get(day_of_week, SU)

                # Pour dateutil.rrule, on utilise byweekday avec un positional
                # +1 = 1er, +2 = 2ème, +3 = 3ème, +4 = 4ème, -1 = dernier
                rule = rrule(
                    MONTHLY,
                    dtstart=start_date,
                    until=end_gen,
                    byweekday=day_obj(week_num),
                    count=max_dates
                )
                dates = [d.strftime('%Y-%m-%d') for d in rule]

            elif monthly_type == 'specific_day' and day_of_month:
                # Jour spécifique du mois (ex: le 15 de chaque mois)
                specific_day = int(day_of_month)
                rule = rrule(
                    MONTHLY,
                    dtstart=start_date,
                    until=end_gen,
                    bymonthday=specific_day,
                    count=max_dates
                )
                dates = [d.strftime('%Y-%m-%d') for d in rule]

            else:
                # Par défaut: même jour du mois que la date de début
                rule = rrule(
                    MONTHLY,
                    dtstart=start_date,
                    until=end_gen,
                    count=max_dates
                )
                dates = [d.strftime('%Y-%m-%d') for d in rule]

        elif frequency == 'yearly':
            rule = rrule(YEARLY, dtstart=start_date, until=end_gen, count=max_dates)
            dates = [d.strftime('%Y-%m-%d') for d in rule]

        else:
            # Fallback: hebdomadaire
            rule = rrule(WEEKLY, dtstart=start_date, until=end_gen, count=max_dates)
            dates = [d.strftime('%Y-%m-%d') for d in rule]

        return JsonResponse({
            'success': True,
            'dates': dates,
            'total_estimated': len(dates),
            'frequency': frequency,
            'monthly_type': monthly_type if frequency == 'monthly' else None
        })

    except Exception as e:
        import traceback
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)


@login_required
def occurrence_list(request, event_id):
    """Liste toutes les occurrences d'un événement récurrent."""
    event = get_object_or_404(Event, pk=event_id)

    # Vérifier les permissions
    if not (request.user.is_staff or
            request.user == event.created_by or
            (hasattr(request.user, 'userprofile') and
             request.user.userprofile.organization == event.organization)):
        raise PermissionDenied

    # Filtrer les occurrences
    status_filter = request.GET.get('status')
    date_from = request.GET.get('from')
    date_to = request.GET.get('to')

    occurrences = event.occurrences.all()

    if status_filter:
        occurrences = occurrences.filter(status=status_filter)
    if date_from:
        occurrences = occurrences.filter(start_datetime__date__gte=date_from)
    if date_to:
        occurrences = occurrences.filter(start_datetime__date__lte=date_to)

    # Pagination
    paginator = Paginator(occurrences, 20)
    page = request.GET.get('page', 1)
    occurrences_page = paginator.get_page(page)

    # Stats
    stats = {
        'total': event.occurrences.count(),
        'upcoming': event.occurrences.filter(
            start_datetime__gte=timezone.now()
        ).exclude(status=OccurrenceStatus.CANCELLED).count(),
        'completed': event.occurrences.filter(
            status=OccurrenceStatus.COMPLETED
        ).count(),
        'cancelled': event.occurrences.filter(
            status=OccurrenceStatus.CANCELLED
        ).count(),
    }

    return render(request, 'competitions/events/occurrence_list.html', {
        'event': event,
        'occurrences': occurrences_page,
        'stats': stats,
        'status_choices': OccurrenceStatus.choices,
    })


@login_required
def occurrence_detail(request, occurrence_id):
    """Détail d'une occurrence spécifique."""
    occurrence = get_object_or_404(
        EventOccurrence.objects.select_related('event'),
        pk=occurrence_id
    )
    event = occurrence.event

    # Vérifier les permissions
    if not (request.user.is_staff or
            request.user == event.created_by or
            (hasattr(request.user, 'userprofile') and
             request.user.userprofile.organization == event.organization)):
        raise PermissionDenied

    # Récupérer les présences
    attendances = occurrence.attendances.select_related('participant').all()

    # Stats
    attendance_stats = {
        'total': attendances.count(),
        'present': attendances.filter(status=AttendanceStatus.PRESENT).count(),
        'absent': attendances.filter(status=AttendanceStatus.ABSENT).count(),
        'excused': attendances.filter(status=AttendanceStatus.EXCUSED).count(),
    }

    return render(request, 'competitions/events/occurrence_detail.html', {
        'occurrence': occurrence,
        'event': event,
        'attendances': attendances,
        'attendance_stats': attendance_stats,
    })


@login_required
def occurrence_edit(request, occurrence_id):
    """Modifier une occurrence individuelle."""
    occurrence = get_object_or_404(
        EventOccurrence.objects.select_related('event'),
        pk=occurrence_id
    )
    event = occurrence.event

    # Vérifier les permissions
    if not (request.user.is_staff or
            request.user == event.created_by or
            (hasattr(request.user, 'userprofile') and
             request.user.userprofile.organization == event.organization)):
        raise PermissionDenied

    if request.method == 'POST':
        form = OccurrenceEditForm(request.POST, instance=occurrence)
        if form.is_valid():
            form.save()
            messages.success(request, _("L'occurrence a été modifiée."))
            return redirect('competitions:events:occurrence_detail',
                            occurrence_id=occurrence.id)
    else:
        form = OccurrenceEditForm(instance=occurrence)

    return render(request, 'competitions/events/occurrence_edit.html', {
        'occurrence': occurrence,
        'event': event,
        'form': form,
    })


@login_required
def occurrence_cancel(request, occurrence_id):
    """Annuler une occurrence."""
    occurrence = get_object_or_404(
        EventOccurrence.objects.select_related('event'),
        pk=occurrence_id
    )
    event = occurrence.event

    # Vérifier les permissions
    if not (request.user.is_staff or
            request.user == event.created_by or
            (hasattr(request.user, 'userprofile') and
             request.user.userprofile.organization == event.organization)):
        raise PermissionDenied

    if occurrence.status == OccurrenceStatus.CANCELLED:
        messages.warning(request, _("Cette occurrence est déjà annulée."))
        return redirect('competitions:events:occurrence_detail',
                        occurrence_id=occurrence.id)

    if request.method == 'POST':
        form = OccurrenceCancelForm(request.POST)
        if form.is_valid():
            occurrence.cancel(
                reason=form.cleaned_data.get('cancellation_reason', ''),
                cancelled_by=request.user
            )
            messages.success(request, _("L'occurrence a été annulée."))

            return redirect('competitions:events:occurrence_list',
                            event_id=event.id)
    else:
        form = OccurrenceCancelForm()

    return render(request, 'competitions/events/occurrence_cancel.html', {
        'occurrence': occurrence,
        'event': event,
        'form': form,
    })


@login_required
def occurrence_attendance(request, occurrence_id):
    """Pointage des présences pour une occurrence."""
    occurrence = get_object_or_404(
        EventOccurrence.objects.select_related('event'),
        pk=occurrence_id
    )
    event = occurrence.event

    # Vérifier les permissions
    if not (request.user.is_staff or
            request.user == event.created_by or
            (hasattr(request.user, 'userprofile') and
             request.user.userprofile.organization == event.organization)):
        raise PermissionDenied

    if request.method == 'POST':
        form = OccurrenceAttendanceForm(request.POST, occurrence=occurrence)
        if form.is_valid():
            form.save(checked_by=request.user)
            messages.success(request, _("Les présences ont été enregistrées."))
            return redirect('competitions:events:occurrence_detail',
                            occurrence_id=occurrence.id)
    else:
        form = OccurrenceAttendanceForm(occurrence=occurrence)

    # Récupérer les participants
    participants = event.participants.all()

    return render(request, 'competitions/events/occurrence_attendance.html', {
        'occurrence': occurrence,
        'event': event,
        'form': form,
        'participants': participants,
        'attendance_choices': AttendanceStatus.choices,
    })


@login_required
def generate_occurrences(request, event_id):
    """Générer manuellement les occurrences pour un événement récurrent."""
    event = get_object_or_404(Event, pk=event_id)

    # Vérifier les permissions
    if not (request.user.is_staff or request.user == event.created_by):
        raise PermissionDenied

    if not event.is_recurring:
        messages.error(request, _("Cet événement n'est pas récurrent."))
        return redirect('competitions:events:event_detail', event_id=event.id)

    if request.method == 'POST':
        months_ahead = int(request.POST.get('months', 6))
        occurrences = event.generate_occurrences(months_ahead=months_ahead)
        messages.success(
            request,
            _("{count} occurrences ont été générées.").format(
                count=len(occurrences)
            )
        )
        return redirect('competitions:events:occurrence_list', event_id=event.id)

    return render(request, 'competitions/events/generate_occurrences.html', {
        'event': event,
    })


@login_required
def event_duplicate(request, event_id):
    """Duplicate an event with all its configuration but without participant data."""
    source = get_object_or_404(Event, id=event_id)

    try:
        new_event = Event()
        # Copy configuration fields
        new_event.title = f"{source.title} (Copie)"
        new_event.description = source.description
        new_event.event_type = source.event_type
        new_event.organization = source.organization
        # Dates
        new_event.start_date = source.start_date
        new_event.end_date = source.end_date
        new_event.start_time = source.start_time
        new_event.end_time = source.end_time
        new_event.all_day = source.all_day
        # Location
        new_event.location = source.location
        new_event.address = source.address
        new_event.city = source.city
        new_event.postal_code = source.postal_code
        # Settings
        new_event.visibility = source.visibility
        new_event.is_public = source.is_public
        new_event.max_participants = source.max_participants
        new_event.registration_required = source.registration_required
        new_event.registration_deadline = source.registration_deadline
        # Details
        new_event.price = source.price
        new_event.contact_email = source.contact_email
        new_event.contact_phone = source.contact_phone
        new_event.color = source.color
        new_event.image = source.image
        # Online/hybrid
        new_event.event_format = source.event_format
        new_event.online_url = source.online_url
        new_event.online_platform = source.online_platform
        new_event.online_meeting_id = source.online_meeting_id
        new_event.online_password = source.online_password
        # Recurrence config
        new_event.is_recurring = source.is_recurring
        new_event.recurrence_frequency = source.recurrence_frequency
        new_event.recurrence_interval = source.recurrence_interval
        new_event.recurrence_days = source.recurrence_days
        new_event.recurrence_day_of_month = source.recurrence_day_of_month
        new_event.recurrence_week_of_month = source.recurrence_week_of_month
        new_event.recurrence_end_type = source.recurrence_end_type
        new_event.recurrence_end_after = source.recurrence_end_after
        new_event.recurrence_end_date = source.recurrence_end_date
        # Reset fields
        new_event.is_cancelled = False
        new_event.is_archived = False
        new_event.created_by = request.user
        new_event.contact_person = request.user

        new_event.save()

        messages.success(request, _("L'événement a été dupliqué avec succès."))
        return redirect('competitions:events:edit_event', event_id=new_event.id)

    except Exception as e:
        messages.error(request, _("Erreur lors de la duplication : {}").format(str(e)))
        return redirect('competitions:events:event_list')
