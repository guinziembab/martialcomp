from django.core.exceptions import PermissionDenied
# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Avg
from django.db import transaction
from django.core.paginator import Paginator
from django.urls import reverse

from apps.competitions.models.event import Event, EventSurvey, SurveyQuestion, SurveyResponse, QuestionResponse
from apps.competitions.models.practitioners import Practitioner
from apps.competitions.utils.decorators import club_required, federation_required
from apps.organizations.models import Organization, OrganizationMember
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Importation future des formulaires
# from apps.competitions.forms.event_surveys import (
#     EventSurveyForm, SurveyQuestionFormSet, SurveyResponseForm
# )


@login_required
def survey_list(request):
    """Liste des sondages disponibles pour l'utilisateur."""
    
    # Sondages de tous les événements créés par l'utilisateur
    created_surveys = EventSurvey.objects.filter(
        event__created_by=request.user
    ).select_related('event').order_by('-created_at')
    
    # Sondages que l'utilisateur a créés directement
    created_surveys = created_surveys | EventSurvey.objects.filter(
        created_by=request.user
    ).select_related('event').order_by('-created_at')
    
    # Sondages auxquels l'utilisateur a répondu
    responded_surveys = EventSurvey.objects.filter(
        responses__participant=request.user
    ).distinct().select_related('event').order_by('-created_at')
    
    # Sondages des événements auxquels l'utilisateur participe
    # et auxquels il n'a pas encore répondu
    try:
        practitioner = Practitioner.objects.get(user=request.user)
        events_participating = Event.objects.filter(
            participants__practitioner=practitioner
        ).values_list('id', flat=True)
        
        active_surveys = EventSurvey.objects.filter(
            event_id__in=events_participating,
            is_active=True
        ).exclude(
            responses__participant=request.user
        ).select_related('event').order_by('-created_at')
    except Practitioner.DoesNotExist:
        active_surveys = EventSurvey.objects.none()
    
    # Sondages des événements des clubs/fédérations de l'utilisateur
    user_organizations = Organization.objects.filter(
        members__user=request.user
    ).values_list('id', flat=True)
    
    organization_surveys = EventSurvey.objects.filter(
        event__organization_id__in=user_organizations,
        is_active=True
    ).exclude(
        id__in=responded_surveys.values_list('id', flat=True)
    ).exclude(
        id__in=active_surveys.values_list('id', flat=True)
    ).select_related('event').order_by('-created_at')
    
    context = {
        'created_surveys': created_surveys,
        'responded_surveys': responded_surveys,
        'active_surveys': active_surveys,
        'organization_surveys': organization_surveys,
    }
    
    return render(request, 'competitions/events/surveys/survey_list.html', context)


@login_required
@club_required
def create_survey(request, event_id=None):
    """Création d'un nouveau sondage pour un événement."""
    event = None
    if event_id:
        event = get_object_or_404(Event, id=event_id)
        
        # Vérifier que l'utilisateur a le droit de créer un sondage pour cet événement
        if request.user != event.created_by and not (
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role in ['club_admin', 'federation_admin'] and
            event.club == getattr(request.user.userprofile, 'club', None)
        ):
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour créer un sondage pour cet événement."))
            return redirect('competitions:events:event_detail', event_id=event.id)
    
    # Initialiser les formulaires
    # form = EventSurveyForm(initial={'event': event})
    # formset = SurveyQuestionFormSet()
    
    # if request.method == 'POST':
    #     form = EventSurveyForm(request.POST)
    #     if form.is_valid():
    #         with transaction.atomic():
    #             survey = form.save(commit=False)
    #             survey.created_by = request.user
    #             if event:
    #                 survey.event = event
    #             survey.save()
    #             
    #             formset = SurveyQuestionFormSet(request.POST, instance=survey)
    #             if formset.is_valid():
    #                 formset.save()
    #                 messages.success(request, _("Le sondage a été créé avec succès."))
    #                 return redirect('competitions:events:surveys:survey_detail', survey_id=survey.id)
    
    context = {
        'event': event,
        # 'form': form,
        # 'formset': formset,
        'is_creation': True,
    }
    
    return render(request, 'competitions/events/surveys/survey_form.html', context)


@login_required
def survey_detail(request, survey_id):
    """Affiche les détails d'un sondage et permet d'y répondre."""
    survey = get_object_or_404(EventSurvey, id=survey_id)
    
    # Vérifier si le sondage est actif
    if not survey.is_active and not (
        request.user == survey.created_by or
        (survey.event and request.user == survey.event.created_by)
    ):
        messages.error(request, _("Ce sondage n'est plus actif."))
        return redirect('competitions:events:surveys:survey_list')
    
    # Vérifier si l'utilisateur a déjÃ  répondu
    user_response = None
    has_responded = False
    
    if request.user.is_authenticated:
        user_response = SurveyResponse.objects.filter(
            survey=survey,
            participant=request.user
        ).first()
        has_responded = user_response is not None
    
    # Si l'utilisateur a déjÃ  répondu et que les soumissions multiples ne sont pas autorisées
    if has_responded and not survey.allow_multiple_submissions:
        messages.info(request, _("Vous avez déjÃ  répondu Ã  ce sondage."))
        return redirect('competitions:events:surveys:response_detail', response_id=user_response.id)
    
    # Récupérer les questions du sondage
    questions = SurveyQuestion.objects.filter(survey=survey).order_by('order')
    
    # # Initialiser le formulaire de réponse
    # if request.method == 'POST':
    #     form = SurveyResponseForm(request.POST, survey=survey)
    #     if form.is_valid():
    #         response = form.save(commit=False)
    #         response.survey = survey
    #         response.participant = request.user
    #         response.ip_address = request.META.get('REMOTE_ADDR')
    #         response.save()
    #         
    #         # Enregistrer les réponses aux questions
    #         for question in questions:
    #             answer_key = f'question_{question.id}'
    #             if answer_key in form.cleaned_data:
    #                 answer = form.cleaned_data[answer_key]
    #                 
    #                 question_response = QuestionResponse(
    #                     response=response,
    #                     question=question
    #                 )
    #                 
    #                 # Enregistrer la réponse selon le type de question
    #                 if question.question_type in ['text', 'textarea']:
    #                     question_response.text_response = answer
    #                 elif question.question_type in ['single_choice', 'multiple_choice']:
    #                     question_response.choice_response = answer
    #                 elif question.question_type in ['rating', 'scale']:
    #                     question_response.numeric_response = answer
    #                 elif question.question_type == 'date':
    #                     question_response.date_response = answer
    #                 
    #                 question_response.save()
    #         
    #         messages.success(request, _("Votre réponse a été enregistrée avec succès."))
    #         return redirect('competitions:events:surveys:response_detail', response_id=response.id)
    # else:
    #     form = SurveyResponseForm(survey=survey)
    
    # Déterminer si l'utilisateur peut modifier le sondage
    can_edit = (
        request.user == survey.created_by or
        (survey.event and request.user == survey.event.created_by)
    )
    
    context = {
        'survey': survey,
        'questions': questions,
        'has_responded': has_responded,
        # 'form': form,
        'can_edit': can_edit,
    }
    
    return render(request, 'competitions/events/surveys/survey_detail.html', context)


@login_required
@club_required
def edit_survey(request, survey_id):
    """Modification d'un sondage existant."""
    survey = get_object_or_404(EventSurvey, id=survey_id)
    
    # Vérifier que l'utilisateur a le droit de modifier ce sondage
    if request.user != survey.created_by and not (
        survey.event and 
        request.user == survey.event.created_by
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier ce sondage."))
        return redirect('competitions:events:surveys:survey_detail', survey_id=survey.id)
    
    # # Initialiser les formulaires avec l'instance existante
    # form = EventSurveyForm(instance=survey)
    # formset = SurveyQuestionFormSet(instance=survey)
    # 
    # if request.method == 'POST':
    #     form = EventSurveyForm(request.POST, instance=survey)
    #     if form.is_valid():
    #         with transaction.atomic():
    #             survey = form.save()
    #             
    #             formset = SurveyQuestionFormSet(request.POST, instance=survey)
    #             if formset.is_valid():
    #                 formset.save()
    #                 messages.success(request, _("Le sondage a été mis Ã  jour avec succès."))
    #                 return redirect('competitions:events:surveys:survey_detail', survey_id=survey.id)
    
    context = {
        'survey': survey,
        # 'form': form,
        # 'formset': formset,
        'is_creation': False,
    }
    
    return render(request, 'competitions/events/surveys/survey_form.html', context)


@login_required
def response_detail(request, response_id):
    """Affiche les détails d'une réponse Ã  un sondage."""
    response = get_object_or_404(SurveyResponse, id=response_id)
    survey = response.survey
    
    # Vérifier que l'utilisateur a le droit de voir cette réponse
    if request.user != response.participant and request.user != survey.created_by and not (
        survey.event and request.user == survey.event.created_by
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour voir cette réponse."))
        return redirect('competitions:events:surveys:survey_list')
    
    # Récupérer les questions et les réponses
    questions = SurveyQuestion.objects.filter(survey=survey).order_by('order')
    question_responses = QuestionResponse.objects.filter(response=response).select_related('question')
    
    # Organiser les réponses par question
    responses_by_question = {qr.question.id: qr for qr in question_responses}
    
    context = {
        'survey': survey,
        'response': response,
        'questions': questions,
        'responses_by_question': responses_by_question,
    }
    
    return render(request, 'competitions/events/surveys/response_detail.html', context)


@login_required
@club_required
def survey_results(request, survey_id):
    """Affiche les résultats d'un sondage."""
    survey = get_object_or_404(EventSurvey, id=survey_id)
    
    # Vérifier que l'utilisateur a le droit de voir les résultats
    if request.user != survey.created_by and not (
        survey.event and request.user == survey.event.created_by
    ):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour voir les résultats de ce sondage."))
        return redirect('competitions:events:surveys:survey_list')
    
    # Récupérer toutes les réponses
    responses = SurveyResponse.objects.filter(survey=survey).select_related('participant')
    total_responses = responses.count()
    
    # Récupérer les questions avec le nombre de réponses pour chaque
    questions = SurveyQuestion.objects.filter(survey=survey).order_by('order').annotate(
        response_count=Count('responses')
    )
    
    # Préparer les statistiques pour chaque question
    question_stats = {}
    for question in questions:
        question_responses = QuestionResponse.objects.filter(question=question)
        
        stats = {
            'total': question_responses.count(),
        }
        
        # Statistiques spécifiques au type de question
        if question.question_type in ['single_choice', 'multiple_choice']:
            # Compter les occurrences de chaque choix
            choice_counts = {}
            for qr in question_responses:
                choices = qr.choice_response
                if isinstance(choices, list):
                    for choice in choices:
                        if choice in choice_counts:
                            choice_counts[choice] += 1
                        else:
                            choice_counts[choice] = 1
                elif choices:  # Single choice
                    if choices in choice_counts:
                        choice_counts[choices] += 1
                    else:
                        choice_counts[choices] = 1
            
            stats['choice_counts'] = choice_counts
            
        elif question.question_type in ['rating', 'scale']:
            # Calculer la moyenne et la distribution
            avg_rating = question_responses.aggregate(avg=Avg('numeric_response'))['avg']
            
            # Distribution des notes
            rating_distribution = {}
            for qr in question_responses:
                if qr.numeric_response is not None:
                    rating = qr.numeric_response
                    if rating in rating_distribution:
                        rating_distribution[rating] += 1
                    else:
                        rating_distribution[rating] = 1
            
            stats['avg_rating'] = avg_rating
            stats['rating_distribution'] = rating_distribution
            
        elif question.question_type == 'date':
            # Regrouper par date
            date_counts = {}
            for qr in question_responses:
                if qr.date_response:
                    date_str = qr.date_response.isoformat()
                    if date_str in date_counts:
                        date_counts[date_str] += 1
                    else:
                        date_counts[date_str] = 1
            
            stats['date_counts'] = date_counts
            
        question_stats[question.id] = stats
    
    context = {
        'survey': survey,
        'questions': questions,
        'total_responses': total_responses,
        'question_stats': question_stats,
        'responses': responses,
    }
    
    return render(request, 'competitions/events/surveys/survey_results.html', context)


@login_required
@require_POST
def toggle_survey_status(request, survey_id):
    """Active ou désactive un sondage."""
    survey = get_object_or_404(EventSurvey, id=survey_id)
    
    # Vérifier que l'utilisateur a le droit de modifier ce sondage
    if request.user != survey.created_by and not (
        survey.event and request.user == survey.event.created_by
    ):
        return JsonResponse({
            'success': False,
            'message': _("Vous n'avez pas les permissions nécessaires pour modifier ce sondage.")
        }, status=403)
    
    # Inverser le statut
    survey.is_active = not survey.is_active
    survey.save()
    
    return JsonResponse({
        'success': True,
        'is_active': survey.is_active,
        'message': _("Le sondage a été {}").format(
            _("activé") if survey.is_active else _("désactivé")
        )
    })


@login_required
@require_POST
def delete_survey(request, survey_id):
    """Supprime un sondage."""
    survey = get_object_or_404(EventSurvey, id=survey_id)
    
    # Vérifier que l'utilisateur a le droit de supprimer ce sondage
    if request.user != survey.created_by and not (
        survey.event and request.user == survey.event.created_by
    ):
        return JsonResponse({
            'success': False,
            'message': _("Vous n'avez pas les permissions nécessaires pour supprimer ce sondage.")
        }, status=403)
    
    event_id = survey.event.id if survey.event else None
    survey.delete()
    
    return JsonResponse({
        'success': True,
        'message': _("Le sondage a été supprimé avec succès."),
        'redirect_url': reverse('competitions:events:event_detail', kwargs={'event_id': event_id}) if event_id else reverse('competitions:events:surveys:survey_list')
    })

