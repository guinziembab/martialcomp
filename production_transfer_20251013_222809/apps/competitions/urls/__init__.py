from django.urls import path, include

from apps.competitions.views.welcome import welcome
from apps.competitions.views.auth import login_view, logout_view 
from apps.competitions.views.csrf_views import refresh_csrf_token
from apps.competitions.views.auth_emergency import emergency_login, quick_login_coach1, quick_login_coach2
from apps.competitions.views.emergency_home import emergency_home
from apps.competitions.views.competitions import get_competition_types
from apps.competitions.views.websocket_test import websocket_test_view

app_name = 'competitions'

urlpatterns = [
    path('qr-management/', include('apps.competitions.urls.qr_management', namespace='qr_management')),
    path('', welcome, name='welcome'),
    
    # URLs Onboarding (SOLUTION AU PROBLÈME 404)
    path('onboarding/', include('apps.competitions.urls.onboarding', namespace='onboarding')),
    
    # URLs Dashboard
    path('dashboard/', include('apps.competitions.urls.dashboard', namespace='dashboard')),
    
    # URLs Club
    path('club/', include('apps.competitions.urls.club', namespace='club')),
    
    # URLs Compétitions
    path('competitions/', include('apps.competitions.urls.competitions', namespace='competitions')),
    
    # URLs Types de Compétition
    path('competition-types/', include('apps.competitions.urls.competition_types', namespace='competition_types')),
    
    # URLs Fédérations (SOLUTION AU PROBLÈME 404) - Temporairement désactivé
    # path('federations/', include('apps.competitions.urls.federations', namespace='federations')),
    
    # URLs Événements
    path('events/', include('apps.competitions.urls.events', namespace='events')),
    
    # URLs Planification d'événements
    path('event-planning/', include('apps.competitions.urls.event_planning', namespace='event_planning')),
    
    # URLs QR Scanner
    path('qr/', include('apps.competitions.urls.qr', namespace='qr')),
    
    # URLs pour le module de combat
    path('combat/', include('apps.competitions.urls.combat', namespace='combat')),
    
    # URLs pour les pratiquants
    path('practitioner/', include('apps.competitions.urls.practitioner', namespace='practitioner')),
    
    # URLs pour les notifications
    path('notifications/', include('apps.competitions.urls.notifications', namespace='notifications')),
    
    # URLs pour les licences
    path('licences/', include('apps.competitions.urls.licences', namespace='licences')),
    
    # URLs pour les organisateurs externes
    path('external-organizer/', include('apps.competitions.urls.external_organizer', namespace='external_organizer')),
    
    # URLs pour la notation technique
    path('technical-scoring/', include('apps.competitions.urls.technical_scoring', namespace='technical_scoring')),
    
    # URLs pour la gestion CSRF
    path('csrf/refresh/', refresh_csrf_token, name='refresh_csrf'),
    
    # API pour les types de compétition
    path('api/competition-types/', get_competition_types, name='get_competition_types'),
    
    # URL de déconnexion
    path('logout/', logout_view, name='logout'),
    
    # URLs d'urgence pour contourner les problèmes CSRF
    path('emergency-login/', emergency_login, name='emergency_login'),
    path('quick-coach1/', quick_login_coach1, name='quick_coach1'),
    path('quick-coach2/', quick_login_coach2, name='quick_coach2'),
    path('emergency/', emergency_home, name='emergency_home'),
    
    # URL de test WebSocket
    path('websocket-test/', websocket_test_view, name='websocket_test'),
]