# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
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

from competitions.models.event import Event, EventParticipant
from competitions.models.event_feedback import EventFeedback
from competitions.models.club import Club
from competitions.models.practitioners import Practitioner
from competitions.forms.event_forms import EventForm, EventFilterForm, EventParticipantForm
from competitions.forms.event_feedback import EventFeedbackForm
from competitions.forms.event_import_export import EventImportForm, EventExportForm
from competitions.forms.event_notifications import EventNotificationForm
from competitions.utils.decorators import club_required, federation_required


@login_required
def event_list(request):
    """Liste tous les événements disponibles avec filtres"""
    # Logique d'affichage des événements selon les permissions
    try:
        # Déterminer les événements à afficher selon le rôle
        if request.user.is_staff or request.user.is_superuser:
            # Staff/Admin : voir tous les événements non archivés
            events = Event.objects.filter(is_archived=False)
            
            # Inclure les événements archivés si demandé
            if request.GET.get('include_archived'):
                events = Event.objects.all()
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
                    events = events.union(org_events).distinct()
        except:
            pass
            
    except Exception as e:
        # En cas d'erreur, retourner une liste vide avec message d'erreur
        events = Event.objects.none()
        messages.error(request, _("Erreur lors du chargement des événements. Veuillez contacter l'administrateur."))
        print(f"Erreur dans event_list: {e}")  # Pour debug
    
    # user_organization déjà défini ci-dessus
    
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
    from organizations.models import Organization
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
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer un événement. Rôles autorisés : Responsable de club, Responsable de fédération, Coach."))
        return redirect('competitions:events:event_list')
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            
            # Assigner l'organisation de l'utilisateur si pas spécifiée
            if not event.organization and user_club and user_club is not True:  # Vérifier que user_club est un objet Club
                event.organization = user_club
                
            event.save()
            # Rafraîchir l'objet depuis la base de données pour s'assurer que l'UUID est bien généré
            event.refresh_from_db()
            
            # Debug: vérifier le type et la valeur de l'ID
            print(f"DEBUG: Event ID = {event.id}, Type = {type(event.id)}")
            
            messages.success(request, _("L'événement a été créé avec succès."))
            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        # Pré-remplir l'organisation si l'utilisateur en a une
        initial = {}
        if user_club and user_club is not True:  # Vérifier que user_club est un objet Club
            initial['organization'] = user_club
            
        form = EventForm(initial=initial)
    
    context = {
        'form': form,
        'is_new': True,
    }
    
    return render(request, 'competitions/events/event_form.html', context)


@login_required
def event_detail(request, event_id):
    """Affiche les détails d'un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier si l'utilisateur est déjà inscrit
    user_registration = None
    
    try:
        user_registration = EventParticipant.objects.filter(
            event=event,
            user=request.user
        ).first()
    except:
        pass
    
    # Vérifier si l'utilisateur est l'organisateur
    is_organizer = (request.user == event.created_by)
    
    # Vérifier si l'utilisateur est admin du club de l'événement
    is_club_admin = False
    if hasattr(request.user, 'userprofile') and event.organization:
        is_club_admin = (
            request.user.userprofile.role == 'club_admin' and
            request.user.userprofile.organization == event.organization
        )
    
    can_edit = is_organizer or is_club_admin or request.user.is_staff
    
    context = {
        'event': event,
        'user_registration': user_registration,
        'can_edit': can_edit,
        'can_register': not user_registration and event.registration_required,
        'registration_closed': event.registration_deadline and event.registration_deadline < timezone.now(),
    }
    
    return render(request, 'competitions/events/event_detail.html', context)


@login_required
def edit_event(request, event_id):
    """Modifier un événement existant"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier les permissions
    if not (
        request.user == event.created_by or
        request.user.is_staff or
        (hasattr(request.user, 'userprofile') and
         request.user.userprofile.role == 'club_admin' and
         request.user.userprofile.organization == event.organization)
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save()
            messages.success(request, _("L'événement a été mis à jour avec succès."))
            return redirect('competitions:events:event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
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
    
    # Vérifier les permissions
    if not (request.user == event.created_by or request.user.is_staff):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour supprimer cet événement."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, _("L'événement a été supprimé avec succès."))
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


@login_required
def register_for_event(request, event_id):
    """Inscription à un événement"""
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier si l'inscription est encore possible
    if event.registration_deadline and event.registration_deadline < timezone.now():
        messages.error(request, _("La date limite d'inscription est dépassée."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'événement est complet
    if event.max_participants and event.participants.count() >= event.max_participants:
        messages.error(request, _("Cet événement est complet."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'utilisateur est déjà inscrit
    if EventParticipant.objects.filter(event=event, user=request.user).exists():
        messages.info(request, _("Vous êtes déjà inscrit à cet événement."))
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
                messages.info(request, _("L'événement est complet, vous avez été ajouté à la liste d'attente."))
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
    """Annulation d'une inscription à un événement"""
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
                
                # Notification (à implémenter selon les besoins)
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
    """Gestion des participants à un événement"""
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
        'can_edit': True,  # Déjà vérifié par la condition ci-dessus
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
    
    # Vérifier si l'utilisateur était inscrit à l'événement
    if not EventParticipant.objects.filter(event=event, user=request.user).exists():
        messages.error(request, _("Vous devez être inscrit à cet événement pour soumettre un feedback."))
        return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Vérifier si l'utilisateur a déjà soumis un feedback
    if EventFeedback.objects.filter(event=event, submitted_by=request.user).exists():
        messages.info(request, _("Vous avez déjà soumis un feedback pour cet événement."))
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
                    messages.warning(request, _("{} événements n'ont pas pu être importés.").format(events_failed))
                
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
            events = Event.objects.all()
            
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
                'message': _("{} événements prêts à être exportés.").format(events.count()),
                'export_url': request.build_absolute_uri(reverse('competitions:events:download_export'))
            })
            
            # Stocker les IDs des événements à exporter en session
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
            # Envoyer les notifications (à implémenter selon vos besoins)
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
    """Parse une date à partir d'une chaîne de caractères"""
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
    Modifie les informations d'un participant à un événement.
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
            messages.success(request, _("Les informations du participant ont été mises à jour."))
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
    
    # Vérifier que l'utilisateur est participant à l'événement
    if not EventParticipant.objects.filter(event=event, user=request.user).exists():
        messages.error(request, _("Vous devez être inscrit à l'événement pour donner votre avis."))
        return redirect('competitions:events:event_detail', event_id=event_id)
    
    # Vérifier si l'utilisateur a déjà soumis un feedback
    if EventFeedback.objects.filter(event=event, submitted_by=request.user).exists():
        messages.info(request, _("Vous avez déjà soumis un feedback pour cet événement."))
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