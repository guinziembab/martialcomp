from django.urls import path, include
from competitions.views import (
    home,
    auth,
    dashboard,
    competitions,
    management,
    club,
    federations,
    onboarding,
    practitioner_dashboard,  # Ajout des vues pratiquant
    practitioner_extra,  # Vues supplémentaires pratiquant
    api,  # API views
)

app_name = 'competitions'

urlpatterns = [
    # Page d'accueil
    path('', home.welcome, name='home'),
    
    # Authentification
    path('auth/', include('competitions.urls.auth')),
    
    # Dashboard (tableau de bord principal)
    path('dashboard/', include('competitions.urls.dashboard')),
    
    # Onboarding
    path('onboarding/', include('competitions.urls.onboarding')),
    
    # Pages de compétitions
    path('competitions/', include([
        path('', competitions.competition_list, name='competition_list'),
        path('<int:pk>/', competitions.competition_detail, name='competition_detail'),
        path('create/', competitions.competition_create, name='competition_create'),
        path('<int:pk>/edit/', competitions.competition_edit, name='competition_edit'),
        path('<int:pk>/register/', competitions.competition_register, name='competition_register'),
    ])),
    
    # Gestion des compétitions
    path('management/', include('competitions.urls.management')),
    
    # Clubs
    path('clubs/', include([
        path('', club.import_export.club_list, name='club_list'),
        path('<int:pk>/', club.import_export.club_detail, name='club_detail'),
        path('create/', club.import_export.club_create, name='club_create'),
        path('<int:pk>/edit/', club.import_export.club_edit, name='club_edit'),
    ])),
    
    # Fédérations
    path('federations/', include('competitions.urls.federations')),
    
    # Catégories
    path('categories/', include('competitions.urls.categories')),
    
    # Grades (délégué à l'app grades)
    path('grades/', include('competitions.urls.grades')),
    
    # Technique scoring
    path('scoring/', include('competitions.urls.technical_scoring')),
    
    # Scoring autonome
    path('standalone-scoring/', include('competitions.urls.standalone_scoring')),
    
    # Combat
    path('combat/', include('competitions.urls.combat')),
    
    # Événements et planification
    path('events/', include('competitions.urls.events'), name='events'),
    
    # QR codes et parrainages
    path('qr-management/', include('competitions.urls.qr_management')),
    
    # Scanner QR code
    path('qr/', include('competitions.urls.qr_scanner')),
    
    # Espace pratiquant
    path('practitioner/', include([
        path('', practitioner_dashboard.practitioner_dashboard, name='practitioner_dashboard'),
        path('profile/', practitioner_dashboard.practitioner_profile, name='practitioner_profile'),
        path('activities/', practitioner_dashboard.practitioner_activities, name='practitioner_activities'),
        path('grades/', practitioner_dashboard.practitioner_grades, name='practitioner_grades'),
        path('competitions/', practitioner_dashboard.practitioner_competitions, name='practitioner_competitions'),
        path('memberships/', practitioner_dashboard.practitioner_memberships, name='practitioner_memberships'),
        path('statistics/', practitioner_dashboard.practitioner_statistics, name='practitioner_statistics'),
        # Fonctionnalités supplémentaires
        path('orders/', practitioner_extra.practitioner_orders, name='practitioner_orders'),
        path('order/<uuid:order_id>/', practitioner_extra.practitioner_order_detail, name='practitioner_order_detail'),
        path('notifications/', practitioner_extra.practitioner_notifications, name='practitioner_notifications'),
        path('notifications/preferences/', practitioner_extra.practitioner_notification_preferences, name='practitioner_notification_preferences'),
        path('notifications/<int:notification_id>/mark-read/', practitioner_extra.practitioner_notification_mark_read, name='practitioner_notification_mark_read'),
        path('support/', practitioner_extra.practitioner_support, name='practitioner_support'),
        path('support/create/', practitioner_extra.practitioner_create_ticket, name='practitioner_create_ticket'),
        path('support/<uuid:ticket_id>/', practitioner_extra.practitioner_support_detail, name='practitioner_support_detail'),
        path('events/', practitioner_extra.practitioner_events, name='practitioner_events'),
        path('events/<int:event_id>/', practitioner_extra.practitioner_event_detail, name='practitioner_event_detail'),
        path('events/<int:event_id>/register/', practitioner_extra.practitioner_event_register, name='practitioner_event_register'),
        path('calendar/', practitioner_extra.practitioner_calendar, name='practitioner_calendar'),
        path('calendar/api/', practitioner_extra.practitioner_calendar_api, name='practitioner_calendar_api'),
    ])),
    # API endpoints
    path("api/grades/disciplines/", api.get_grades_for_disciplines, name="api_grades_for_disciplines"),
]