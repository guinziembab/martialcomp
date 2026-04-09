"""
Vues API pour la gestion du streaming des compétitions.
"""

import json
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from apps.competitions.models import Competition
from apps.competitions.forms.streaming import CompetitionStreamingForm


class CompetitionStreamingAPIView(View):
    """
    API pour gérer la configuration du streaming d'une compétition.
    GET: Récupérer les informations de streaming
    POST: Mettre à jour la configuration
    """

    @method_decorator(login_required)
    def get(self, request, competition_id):
        """Récupérer les informations de streaming."""
        competition = get_object_or_404(Competition, id=competition_id)

        # Vérifier les permissions (au minimum, doit pouvoir voir la compétition)
        # TODO: Ajouter une vraie vérification des permissions

        return JsonResponse({
            'success': True,
            'data': {
                'stream_enabled': competition.stream_enabled,
                'stream_platform': competition.stream_platform,
                'stream_url': competition.stream_url,
                'stream_embed_url': competition.stream_embed_url,
                'stream_chat_url': competition.generate_chat_url(),
                'stream_chat_enabled': competition.stream_chat_enabled,
                'is_live': competition.is_live,
                'stream_started_at': (
                    competition.stream_started_at.isoformat()
                    if competition.stream_started_at else None
                ),
                'stream_ended_at': (
                    competition.stream_ended_at.isoformat()
                    if competition.stream_ended_at else None
                ),
                'stream_viewer_count': competition.stream_viewer_count,
                'stream_replay_url': competition.stream_replay_url,
                'stream_replay_available': competition.stream_replay_available,
            }
        })

    @method_decorator(login_required)
    def post(self, request, competition_id):
        """Mettre à jour la configuration du streaming."""
        competition = get_object_or_404(Competition, id=competition_id)

        # Vérifier les permissions (organisateur uniquement)
        # TODO: Ajouter une vraie vérification des permissions

        # Parser le body JSON si Content-Type est application/json
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid JSON')
                }, status=400)
        else:
            data = request.POST

        form = CompetitionStreamingForm(data, instance=competition)

        if form.is_valid():
            competition = form.save()
            return JsonResponse({
                'success': True,
                'message': _('Configuration du streaming mise à jour'),
                'data': {
                    'stream_embed_url': competition.stream_embed_url,
                    'stream_chat_url': competition.generate_chat_url(),
                }
            })

        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


class StreamStatusAPIView(View):
    """
    API pour gérer le statut live du stream (démarrer/arrêter).
    """

    @method_decorator(login_required)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, competition_id, action):
        """Démarrer ou arrêter le stream."""
        competition = get_object_or_404(Competition, id=competition_id)

        # Vérifier les permissions
        # TODO: Ajouter une vraie vérification des permissions

        if action == 'start':
            if not competition.stream_enabled or not competition.stream_url:
                return JsonResponse({
                    'success': False,
                    'error': _('Le streaming doit être configuré avant de démarrer')
                }, status=400)

            competition.start_stream()
            return JsonResponse({
                'success': True,
                'message': _('Stream démarré'),
                'data': {
                    'is_live': True,
                    'started_at': competition.stream_started_at.isoformat()
                }
            })

        elif action == 'stop':
            competition.end_stream()
            return JsonResponse({
                'success': True,
                'message': _('Stream arrêté'),
                'data': {
                    'is_live': False,
                    'ended_at': competition.stream_ended_at.isoformat()
                }
            })

        return JsonResponse({
            'success': False,
            'error': _('Action invalide. Utilisez "start" ou "stop".')
        }, status=400)


class PublicStreamAPIView(View):
    """
    API publique pour les spectateurs.
    Retourne les informations de streaming sans authentification.
    """

    def get(self, request, competition_id):
        """Récupérer les informations de streaming public."""
        competition = get_object_or_404(
            Competition.objects.select_related('organizing_organization'),
            id=competition_id,
            stream_enabled=True
        )

        return JsonResponse({
            'success': True,
            'competition': {
                'id': competition.id,
                'name': competition.title,
                'organization': (
                    competition.organizing_organization.name
                    if competition.organizing_organization else None
                ),
                'start_date': competition.start_date.isoformat(),
                'end_date': competition.end_date.isoformat(),
            },
            'streaming': {
                'platform': competition.stream_platform,
                'embed_url': competition.stream_embed_url,
                'chat_url': (
                    competition.generate_chat_url()
                    if competition.stream_chat_enabled else None
                ),
                'is_live': competition.is_live,
                'replay_url': (
                    competition.stream_replay_url
                    if competition.stream_replay_available else None
                ),
                'viewer_count': competition.stream_viewer_count,
            }
        })


class CompetitionLiveView(View):
    """
    Vue pour afficher la page de streaming live d'une compétition.
    """

    def get(self, request, competition_id):
        """Afficher la page de streaming."""
        competition = get_object_or_404(
            Competition.objects.select_related('organizing_organization'),
            id=competition_id
        )

        context = {
            'competition': competition,
            'stream_chat_url': competition.generate_chat_url(),
        }

        return render(
            request,
            'competitions/streaming/live.html',
            context
        )


class StreamingConfigView(View):
    """
    Vue pour la page de configuration du streaming (organisateur).
    """

    @method_decorator(login_required)
    def get(self, request, competition_id):
        """Afficher le formulaire de configuration."""
        competition = get_object_or_404(Competition, id=competition_id)

        # TODO: Vérifier les permissions

        form = CompetitionStreamingForm(instance=competition)

        context = {
            'competition': competition,
            'form': form,
        }

        return render(
            request,
            'competitions/streaming/config.html',
            context
        )

    @method_decorator(login_required)
    def post(self, request, competition_id):
        """Enregistrer la configuration."""
        competition = get_object_or_404(Competition, id=competition_id)

        # TODO: Vérifier les permissions

        form = CompetitionStreamingForm(request.POST, instance=competition)

        if form.is_valid():
            form.save()
            return JsonResponse({
                'success': True,
                'message': _('Configuration sauvegardée')
            })

        context = {
            'competition': competition,
            'form': form,
        }

        return render(
            request,
            'competitions/streaming/config.html',
            context
        )
