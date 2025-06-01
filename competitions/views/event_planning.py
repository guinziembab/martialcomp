# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, F, Sum, Case, When, Value, IntegerField
from django.db import transaction
from django.core.exceptions import PermissionDenied

from competitions.models.event_planning import (
    EventPoll, PollOption, PollResponse, EventReminder, EventStatistics, PollQuestion, PollQuestionResponse
)
from competitions.models.event import Event, EventParticipant
from competitions.forms.event_planning import (
    EventPollForm, PollOptionFormSet, PollResponseForm, BulkPollResponseForm, EventReminderForm
)

# Import conditionnel pour PollQuestionFormSet
try:
    from competitions.forms.event_planning import PollQuestionFormSet
    POLL_QUESTIONS_AVAILABLE = True
except ImportError:
    PollQuestionFormSet = None
    POLL_QUESTIONS_AVAILABLE = False
from organizations.models import Organization, OrganizationMember
from competitions.utils.decorators import club_admin_required, federation_admin_required


def is_poll_questions_feature_available():
    """Vérifie si la fonctionnalité des questions personnalisées est disponible."""
    if not POLL_QUESTIONS_AVAILABLE or PollQuestionFormSet is None:
        return False
    
    try:
        from django.db import connection
        from django.db.utils import ProgrammingError
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM competitions_pollquestion LIMIT 1")
        return True
    except (ProgrammingError, Exception):
        return False


@login_required
def poll_list(request):
    """
    Affiche la liste des sondages disponibles pour l'utilisateur.
    """
    # Sondages créés par l'utilisateur
    created_polls = EventPoll.objects.filter(
        created_by=request.user
    ).select_related('organization', 'event').order_by('-created_at')
    
    # Sondages auxquels l'utilisateur a répondu
    responded_polls = EventPoll.objects.filter(
        options__responses__user=request.user
    ).distinct().select_related('organization', 'event').order_by('-created_at')
    
    # Sondages actifs de ses organisations (clubs, fédérations)
    user_organizations = Organization.objects.filter(
        members__user=request.user
    ).values_list('id', flat=True)
    
    organization_polls = EventPoll.objects.filter(
        organization_id__in=user_organizations,
        status='active',
    ).exclude(
        id__in=responded_polls.values_list('id', flat=True)
    ).select_related('organization', 'event').order_by('-created_at')
    
    # Sondages des événements auxquels l'utilisateur participe
    events_participating = Event.objects.filter(
        participants__user=request.user
    ).values_list('id', flat=True)
    
    event_polls = EventPoll.objects.filter(
        event_id__in=events_participating,
        status='active',
    ).exclude(
        id__in=responded_polls.values_list('id', flat=True)
    ).select_related('organization', 'event').order_by('-created_at')
    
    # Regrouper les polls pour éviter les doublons
    organization_polls = organization_polls.exclude(id__in=event_polls.values_list('id', flat=True))
    
    context = {
        'created_polls': created_polls,
        'responded_polls': responded_polls,
        'organization_polls': organization_polls,
        'event_polls': event_polls,
    }
    
    return render(request, 'competitions/event_planning/poll_list.html', context)


@login_required
def poll_detail(request, poll_id):
    """
    Affiche les détails d'un sondage et permet d'y répondre.
    """
    poll = get_object_or_404(EventPoll, id=poll_id)
    
    # Vérifier si l'utilisateur a accès à ce sondage
    can_view = (
        poll.created_by == request.user or
        PollResponse.objects.filter(option__poll=poll, user=request.user).exists() or
        OrganizationMember.objects.filter(organization=poll.organization, user=request.user).exists() or
        (poll.event and EventParticipant.objects.filter(event=poll.event, user=request.user).exists())
    )
    
    if not can_view and not poll.share_url_code:
        return HttpResponseForbidden(_("Vous n'avez pas accès à ce sondage."))
    
    # Récupérer les options du sondage avec les statistiques
    options = PollOption.objects.filter(poll=poll).annotate(
        yes_votes=Count('responses', filter=Q(responses__response='yes')),
        maybe_votes=Count('responses', filter=Q(responses__response='maybe')),
        no_votes=Count('responses', filter=Q(responses__response='no')),
        total_votes=Count('responses'),
        score=Sum(Case(
            When(responses__response='yes', then=Value(2)),
            When(responses__response='maybe', then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        ))
    ).order_by('-score', 'date', 'start_time')
    
    # Récupérer les réponses de l'utilisateur actuel
    user_responses = {
        str(resp.option.id): resp
        for resp in PollResponse.objects.filter(
            option__poll=poll, 
            user=request.user
        ).select_related('option')
    } if request.user.is_authenticated else {}
    
    # Récupérer les participants pour chaque option
    participants = {}
    if poll.show_participants:
        for option in options:
            participants[str(option.id)] = list(PollResponse.objects.filter(
                option=option, 
                is_anonymous=False
            ).select_related('user').values('user__username', 'user__first_name', 'user__last_name', 'response'))
    
    # Préparer le formulaire de réponse globale
    form = BulkPollResponseForm(
        poll=poll, 
        user=request.user if request.user.is_authenticated else None
    )
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = BulkPollResponseForm(
            request.POST, 
            poll=poll, 
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, _("Vos réponses ont été enregistrées avec succès."))
            
            # Rediriger pour éviter le problème de resoumission de formulaire
            return redirect('competitions:event_planning:poll_detail', poll_id=poll_id)
    
    # Vérifier si l'utilisateur a le droit de finaliser ce sondage
    can_finalize = (
        poll.created_by == request.user or
        OrganizationMember.objects.filter(
            organization=poll.organization, 
            user=request.user,
            role__in=['admin', 'manager']
        ).exists()
    )
    
    context = {
        'poll': poll,
        'options': options,
        'user_responses': user_responses,
        'participants': participants,
        'form': form,
        'can_finalize': can_finalize,
        'can_edit': poll.created_by == request.user,
    }
    
    return render(request, 'competitions/event_planning/poll_detail.html', context)


@login_required
def create_poll(request, event_id=None):
    """
    Création d'un nouveau sondage d'événement.
    Peut être associé à un événement existant si event_id est fourni.
    """
    event = None
    organization = None
    
    if event_id:
        event = get_object_or_404(Event, id=event_id)
        organization = event.organization
        
        # Vérifier que l'utilisateur a le droit de créer un sondage pour cet événement
        if event.created_by != request.user and not OrganizationMember.objects.filter(
            organization=organization, 
            user=request.user,
            role__in=['admin', 'manager']
        ).exists():
            return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de créer un sondage pour cet événement."))
    else:
        # Récupérer les organisations de l'utilisateur avec des rôles administratifs
        user_organizations = Organization.objects.filter(
            members__user=request.user,
            members__is_active=True
        ).filter(
            Q(members__role__in=['owner', 'admin', 'manager']) |
            Q(members__can_manage_competitions=True)
        ).distinct()
        
        # Si aucune organisation trouvée via les memberships, vérifier via UserProfile
        if not user_organizations.exists() and hasattr(request.user, 'profile'):
            profile_admin_roles = ['club_manager', 'federation_admin', 'coach']
            if request.user.profile.role in profile_admin_roles:
                # Essayer de récupérer l'organisation via le profil
                if hasattr(request.user.profile, 'organization') and request.user.profile.organization:
                    # Si l'organisation du profil est un Club, créer une organisation correspondante
                    try:
                        # Récupérer ou créer l'organisation correspondante
                        club = request.user.profile.organization
                        org, created = Organization.objects.get_or_create(
                            old_club_id=club.id,
                            defaults={
                                'name': club.name,
                                'organization_type': 'club',
                                'description': club.description or '',
                                'email': club.email or '',
                                'phone': club.phone or '',
                                'address': club.address or '',
                                'city': club.city or '',
                                'country': club.country or '',
                                'created_by': request.user,
                            }
                        )
                        # Créer le membership si nécessaire
                        membership, created = OrganizationMember.objects.get_or_create(
                            user=request.user,
                            organization=org,
                            defaults={
                                'role': 'admin',
                                'can_manage_competitions': True,
                                'can_edit_organization': True,
                                'can_manage_members': True,
                            }
                        )
                        user_organizations = Organization.objects.filter(id=org.id)
                    except Exception as e:
                        print(f"Erreur lors de la création de l'organisation: {e}")
        
        if not user_organizations.exists():
            messages.error(request, _("Vous devez être administrateur, manager ou propriétaire d'une organisation pour créer un sondage."))
            return redirect('competitions:event_planning:poll_list')
        
        # Si une seule organisation, on la sélectionne par défaut
        if user_organizations.count() == 1:
            organization = user_organizations.first()
    
    # Création du formulaire initial
    form = EventPollForm(
        user=request.user,
        initial={
            'organization': organization.id if organization else None,
            'title': event.title if event else '',
            'description': event.description if event else '',
            'event_type': event.event_type if event else None,
        }
    )
    
    # Création du formset pour les options de date
    formset = PollOptionFormSet(instance=EventPoll())
    
    # Création du formset pour les questions personnalisées
    question_formset = None
    if is_poll_questions_feature_available():
        try:
            question_formset = PollQuestionFormSet(instance=EventPoll())
        except Exception as e:
            print(f"Erreur lors de la création du formset: {e}")
            question_formset = None
    
    if request.method == 'POST':
        form = EventPollForm(request.POST, user=request.user)
        
        if form.is_valid():
            with transaction.atomic():
                # Créer l'instance de sondage sans sauvegarder immédiatement
                poll = form.save(commit=False)
                
                # Associer l'événement si fourni
                if event:
                    poll.event = event
                
                # Sauvegarder le sondage
                poll.save()
                
                # Attacher les formsets au sondage nouvellement créé
                formset = PollOptionFormSet(request.POST, instance=poll)
                
                # Gérer le question_formset seulement si la fonctionnalité est disponible
                question_formset_valid = True  # Par défaut valide
                if is_poll_questions_feature_available() and question_formset is not None:
                    try:
                        question_formset = PollQuestionFormSet(request.POST, instance=poll)
                        question_formset_valid = question_formset.is_valid()
                    except Exception as e:
                        print(f"Erreur avec question_formset: {e}")
                        question_formset = None
                        question_formset_valid = True
                
                if formset.is_valid() and question_formset_valid:
                    formset.save()
                    if question_formset:
                        question_formset.save()
                    
                    messages.success(request, _("Le sondage a été créé avec succès."))
                    return redirect('competitions:event_planning:poll_detail', poll_id=poll.id)
                else:
                    # Annuler la transaction si un formset n'est pas valide
                    transaction.set_rollback(True)
        else:
            # Recréer les formsets avec les données du POST
            formset = PollOptionFormSet(request.POST)
            if is_poll_questions_feature_available() and question_formset is not None:
                try:
                    question_formset = PollQuestionFormSet(request.POST)
                except Exception as e:
                    print(f"Erreur lors de la recréation du question_formset: {e}")
                    question_formset = None
    
    # Liste des organisations pour le formulaire (utiliser la même logique que ci-dessus)
    organizations = user_organizations
    
    context = {
        'form': form,
        'formset': formset,
        'question_formset': question_formset,
        'event': event,
        'organizations': organizations,
        'poll_questions_available': is_poll_questions_feature_available(),
    }
    
    return render(request, 'competitions/event_planning/create_poll_simple.html', context)


@login_required
def edit_poll(request, poll_id):
    """
    Édition d'un sondage existant.
    """
    poll = get_object_or_404(EventPoll, id=poll_id)
    
    # Vérifier que l'utilisateur a le droit de modifier ce sondage
    if poll.created_by != request.user and not OrganizationMember.objects.filter(
        organization=poll.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de modifier ce sondage."))
    
    # Ne pas permettre l'édition des sondages finalisés ou annulés
    if poll.status in ['finalized', 'cancelled']:
        messages.error(request, _("Ce sondage ne peut plus être modifié car il a été finalisé ou annulé."))
        return redirect('competitions:event_planning:poll_detail', poll_id=poll.id)
    
    # Création du formulaire avec l'instance existante
    form = EventPollForm(instance=poll, user=request.user)
    
    # Création du formset pour les options de date
    formset = PollOptionFormSet(instance=poll)
    
    if request.method == 'POST':
        form = EventPollForm(request.POST, instance=poll, user=request.user)
        
        if form.is_valid():
            with transaction.atomic():
                # Mettre à jour le sondage
                poll = form.save()
                
                # Mise à jour des options
                formset = PollOptionFormSet(request.POST, instance=poll)
                
                if formset.is_valid():
                    formset.save()
                    
                    messages.success(request, _("Le sondage a été mis à jour avec succès."))
                    return redirect('competitions:event_planning:poll_detail', poll_id=poll.id)
                else:
                    # Annuler la transaction si le formset n'est pas valide
                    transaction.set_rollback(True)
    
    context = {
        'form': form,
        'formset': formset,
        'poll': poll,
        'edit_mode': True,
    }
    
    return render(request, 'competitions/event_planning/edit_poll.html', context)


@login_required
@require_POST
def poll_respond(request, option_id):
    """
    Soumet une réponse individuelle à une option de sondage.
    """
    option = get_object_or_404(PollOption, id=option_id)
    poll = option.poll
    
    # Vérifier que le sondage est actif
    if poll.status != 'active':
        return JsonResponse({
            'success': False,
            'message': _("Ce sondage n'est plus actif.")
        }, status=400)
    
    # Vérifier s'il y a déjà une réponse pour cette option et cet utilisateur
    try:
        response = PollResponse.objects.get(
            option=option,
            user=request.user
        )
        # Si le vote multiple n'est pas autorisé et que la réponse existe déjà,
        # on renvoie une erreur
        if not poll.allow_multiple_votes:
            return JsonResponse({
                'success': False,
                'message': _("Vous avez déjà répondu à cette option.")
            }, status=400)
    except PollResponse.DoesNotExist:
        response = PollResponse(
            option=option,
            user=request.user
        )
    
    # Traiter la réponse
    form = PollResponseForm(request.POST, instance=response, user=request.user, option=option)
    
    if form.is_valid():
        form.save()
        
        # Retourner les statistiques mises à jour pour cette option
        yes_votes = PollResponse.objects.filter(option=option, response='yes').count()
        maybe_votes = PollResponse.objects.filter(option=option, response='maybe').count()
        no_votes = PollResponse.objects.filter(option=option, response='no').count()
        total_votes = yes_votes + maybe_votes + no_votes
        
        return JsonResponse({
            'success': True,
            'message': _("Votre réponse a été enregistrée."),
            'stats': {
                'yes_votes': yes_votes,
                'maybe_votes': maybe_votes,
                'no_votes': no_votes,
                'total_votes': total_votes
            }
        })
    else:
        # Retourner les erreurs du formulaire
        return JsonResponse({
            'success': False,
            'message': _("Erreur lors de l'enregistrement de votre réponse."),
            'errors': form.errors
        }, status=400)


@login_required
@require_POST
def finalize_poll(request, poll_id, option_id):
    """
    Finalise un sondage avec l'option sélectionnée.
    """
    poll = get_object_or_404(EventPoll, id=poll_id)
    option = get_object_or_404(PollOption, id=option_id, poll=poll)
    
    # Vérifier que l'utilisateur a le droit de finaliser ce sondage
    if poll.created_by != request.user and not OrganizationMember.objects.filter(
        organization=poll.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return JsonResponse({
            'success': False, 
            'message': _("Vous n'avez pas l'autorisation de finaliser ce sondage.")
        }, status=403)
    
    # Vérifier que le sondage n'est pas déjà finalisé ou annulé
    if poll.status in ['finalized', 'cancelled']:
        return JsonResponse({
            'success': False, 
            'message': _("Ce sondage est déjà finalisé ou annulé.")
        }, status=400)
    
    try:
        # Finaliser le sondage avec l'option choisie
        event = poll.finalize_with_option(option)
        
        return JsonResponse({
            'success': True,
            'message': _("Le sondage a été finalisé avec succès."),
            'event_id': str(event.id) if event else None,
            'redirect_url': reverse('competitions:events:event_detail', kwargs={'event_id': event.id}) if event else reverse('competitions:event_planning:poll_detail', kwargs={'poll_id': poll.id})
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def cancel_poll(request, poll_id):
    """
    Annule un sondage.
    """
    poll = get_object_or_404(EventPoll, id=poll_id)
    
    # Vérifier que l'utilisateur a le droit d'annuler ce sondage
    if poll.created_by != request.user and not OrganizationMember.objects.filter(
        organization=poll.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return JsonResponse({
            'success': False, 
            'message': _("Vous n'avez pas l'autorisation d'annuler ce sondage.")
        }, status=403)
    
    # Vérifier que le sondage n'est pas déjà finalisé ou annulé
    if poll.status in ['finalized', 'cancelled']:
        return JsonResponse({
            'success': False, 
            'message': _("Ce sondage est déjà finalisé ou annulé.")
        }, status=400)
    
    try:
        # Marquer le sondage comme annulé
        poll.status = 'cancelled'
        poll.save()
        
        return JsonResponse({
            'success': True,
            'message': _("Le sondage a été annulé avec succès.")
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def poll_results(request, poll_id):
    """
    Affiche les résultats détaillés d'un sondage.
    """
    poll = get_object_or_404(EventPoll, id=poll_id)
    
    # Vérifier que l'utilisateur a le droit de voir les résultats
    if poll.created_by != request.user and not OrganizationMember.objects.filter(
        organization=poll.organization, 
        user=request.user
    ).exists() and not PollResponse.objects.filter(option__poll=poll, user=request.user).exists():
        return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de voir les résultats de ce sondage."))
    
    # Récupérer les options avec les statistiques
    options = PollOption.objects.filter(poll=poll).annotate(
        yes_votes=Count('responses', filter=Q(responses__response='yes')),
        maybe_votes=Count('responses', filter=Q(responses__response='maybe')),
        no_votes=Count('responses', filter=Q(responses__response='no')),
        total_votes=Count('responses'),
        score=Sum(Case(
            When(responses__response='yes', then=Value(2)),
            When(responses__response='maybe', then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        ))
    ).order_by('-score', 'date', 'start_time')
    
    # Récupérer les statistiques des réponses
    stats = {
        'total_participants': PollResponse.objects.filter(option__poll=poll).values('user').distinct().count(),
        'total_responses': PollResponse.objects.filter(option__poll=poll).count(),
        'response_types': {
            'yes': PollResponse.objects.filter(option__poll=poll, response='yes').count(),
            'maybe': PollResponse.objects.filter(option__poll=poll, response='maybe').count(),
            'no': PollResponse.objects.filter(option__poll=poll, response='no').count(),
        }
    }
    
    # Récupérer les participants et leurs réponses
    if poll.show_participants:
        participants = {}
        for user in PollResponse.objects.filter(
            option__poll=poll, 
            is_anonymous=False
        ).values('user').distinct():
            user_id = user['user']
            participants[user_id] = {
                'user': get_object_or_404(get_user_model(), id=user_id),
                'responses': {}
            }
            
            for response in PollResponse.objects.filter(
                option__poll=poll, 
                user_id=user_id,
                is_anonymous=False
            ).select_related('option'):
                participants[user_id]['responses'][str(response.option.id)] = {
                    'response': response.response,
                    'comment': response.comment
                }
    else:
        participants = None
    
    context = {
        'poll': poll,
        'options': options,
        'stats': stats,
        'participants': participants,
    }
    
    return render(request, 'competitions/event_planning/poll_results.html', context)


@login_required
def public_poll(request, share_code):
    """
    Accède à un sondage via son code de partage public.
    """
    poll = get_object_or_404(EventPoll, share_url_code=share_code)
    
    # Rediriger vers la vue détaillée du sondage
    return redirect('competitions:event_planning:poll_detail', poll_id=poll.id)


@login_required
def event_reminders(request, event_id):
    """
    Gère les rappels pour un événement.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier que l'utilisateur a le droit de gérer les rappels
    if event.created_by != request.user and not OrganizationMember.objects.filter(
        organization=event.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de gérer les rappels pour cet événement."))
    
    # Récupérer les rappels existants
    reminders = EventReminder.objects.filter(event=event).order_by('-created_at')
    
    context = {
        'event': event,
        'reminders': reminders,
    }
    
    return render(request, 'competitions/event_planning/event_reminders.html', context)


@login_required
def create_reminder(request, event_id):
    """
    Crée un nouveau rappel pour un événement.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier que l'utilisateur a le droit de créer des rappels
    if event.created_by != request.user and not OrganizationMember.objects.filter(
        organization=event.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de créer des rappels pour cet événement."))
    
    # Participants à l'événement pour le champ des destinataires
    participants = list(
        get_user_model().objects.filter(
            event_participations__event=event,
            event_participations__status__in=['registered', 'confirmed']
        ).distinct()
    )
    
    # Créer le formulaire
    form = EventReminderForm(
        user=request.user,
        event=event,
        initial={
            'title': f"Rappel : {event.title}",
            'message': _(f"N'oubliez pas l'événement \"{event.title}\" qui aura lieu le {event.start_date.strftime('%d/%m/%Y')}.")
        }
    )
    
    if request.method == 'POST':
        form = EventReminderForm(request.POST, user=request.user, event=event)
        
        if form.is_valid():
            reminder = form.save()
            
            messages.success(request, _("Le rappel a été créé avec succès."))
            return redirect('competitions:event_planning:event_reminders', event_id=event.id)
    
    context = {
        'form': form,
        'event': event,
        'participants': participants,
    }
    
    return render(request, 'competitions/event_planning/create_reminder.html', context)


@login_required
def edit_reminder(request, reminder_id):
    """
    Modifie un rappel existant.
    """
    reminder = get_object_or_404(EventReminder, id=reminder_id)
    event = reminder.event
    
    # Vérifier que l'utilisateur a le droit de modifier ce rappel
    if reminder.created_by != request.user and not OrganizationMember.objects.filter(
        organization=event.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de modifier ce rappel."))
    
    # Ne pas permettre l'édition des rappels déjà envoyés
    if reminder.is_sent:
        messages.error(request, _("Ce rappel a déjà été envoyé et ne peut plus être modifié."))
        return redirect('competitions:event_planning:event_reminders', event_id=event.id)
    
    # Participants à l'événement pour le champ des destinataires
    participants = list(
        get_user_model().objects.filter(
            event_participations__event=event,
            event_participations__status__in=['registered', 'confirmed']
        ).distinct()
    )
    
    # Créer le formulaire avec l'instance existante
    form = EventReminderForm(instance=reminder, user=request.user, event=event)
    
    if request.method == 'POST':
        form = EventReminderForm(request.POST, instance=reminder, user=request.user, event=event)
        
        if form.is_valid():
            form.save()
            
            messages.success(request, _("Le rappel a été mis à jour avec succès."))
            return redirect('competitions:event_planning:event_reminders', event_id=event.id)
    
    context = {
        'form': form,
        'reminder': reminder,
        'event': event,
        'participants': participants,
    }
    
    return render(request, 'competitions/event_planning/edit_reminder.html', context)


@login_required
@require_POST
def delete_reminder(request, reminder_id):
    """
    Supprime un rappel existant.
    """
    reminder = get_object_or_404(EventReminder, id=reminder_id)
    event = reminder.event
    
    # Vérifier que l'utilisateur a le droit de supprimer ce rappel
    if reminder.created_by != request.user and not OrganizationMember.objects.filter(
        organization=event.organization, 
        user=request.user,
        role__in=['admin', 'manager']
    ).exists():
        return JsonResponse({
            'success': False, 
            'message': _("Vous n'avez pas l'autorisation de supprimer ce rappel.")
        }, status=403)
    
    # Ne pas permettre la suppression des rappels déjà envoyés
    if reminder.is_sent:
        return JsonResponse({
            'success': False, 
            'message': _("Ce rappel a déjà été envoyé et ne peut pas être supprimé.")
        }, status=400)
    
    try:
        # Supprimer le rappel
        reminder.delete()
        
        return JsonResponse({
            'success': True,
            'message': _("Le rappel a été supprimé avec succès.")
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def event_statistics(request, event_id):
    """
    Affiche les statistiques pour un événement.
    """
    event = get_object_or_404(Event, id=event_id)
    
    # Vérifier que l'utilisateur a le droit de voir les statistiques
    if event.created_by != request.user and not OrganizationMember.objects.filter(
        organization=event.organization, 
        user=request.user
    ).exists():
        return HttpResponseForbidden(_("Vous n'avez pas l'autorisation de voir les statistiques de cet événement."))
    
    # Récupérer ou créer les statistiques
    try:
        stats = EventStatistics.objects.get(event=event)
    except EventStatistics.DoesNotExist:
        stats = EventStatistics(event=event)
        stats.update_from_event(event)
    
    # Récupérer les participants
    participants = EventParticipant.objects.filter(event=event).select_related('user')
    
    # Si l'événement a un sondage associé
    poll_stats = None
    poll_options = None
    if hasattr(event, 'poll'):
        poll = event.poll
        
        # Récupérer les statistiques du sondage
        try:
            poll_stats = EventStatistics.objects.get(poll=poll)
        except EventStatistics.DoesNotExist:
            poll.create_statistics()
            poll_stats = poll.statistics
        
        # Récupérer les options du sondage avec les statistiques
        poll_options = PollOption.objects.filter(poll=poll).annotate(
            yes_votes=Count('responses', filter=Q(responses__response='yes')),
            maybe_votes=Count('responses', filter=Q(responses__response='maybe')),
            no_votes=Count('responses', filter=Q(responses__response='no')),
            total_votes=Count('responses')
        ).order_by('-is_selected', 'date', 'start_time')
    
    context = {
        'event': event,
        'stats': stats,
        'participants': participants,
        'poll_stats': poll_stats,
        'poll_options': poll_options,
    }
    
    return render(request, 'competitions/event_planning/event_statistics.html', context)