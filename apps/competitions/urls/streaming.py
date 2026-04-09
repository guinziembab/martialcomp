"""
URLs pour le streaming des compétitions.
"""

from django.urls import path

from apps.competitions.views.streaming import (
    CompetitionStreamingAPIView,
    StreamStatusAPIView,
    PublicStreamAPIView,
    CompetitionLiveView,
    StreamingConfigView,
)

app_name = 'streaming'

urlpatterns = [
    # =========================================================================
    # API ENDPOINTS
    # =========================================================================

    # Configuration du streaming (GET/POST)
    path(
        'api/<int:competition_id>/',
        CompetitionStreamingAPIView.as_view(),
        name='api_config'
    ),

    # Démarrer/Arrêter le stream
    path(
        'api/<int:competition_id>/<str:action>/',
        StreamStatusAPIView.as_view(),
        name='api_status'
    ),

    # Informations publiques du stream
    path(
        'api/<int:competition_id>/public/',
        PublicStreamAPIView.as_view(),
        name='api_public'
    ),

    # =========================================================================
    # PAGES HTML
    # =========================================================================

    # Page de streaming live (spectateurs)
    path(
        '<int:competition_id>/live/',
        CompetitionLiveView.as_view(),
        name='live'
    ),

    # Page de configuration (organisateurs)
    path(
        '<int:competition_id>/config/',
        StreamingConfigView.as_view(),
        name='config'
    ),
]
