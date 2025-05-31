from django.urls import path
from . import views, views_admin

app_name = 'family_management'

urlpatterns = [
    # Dashboard principal
    path('', views.family_dashboard, name='dashboard'),
    
    # Gestion des familles
    path('family/<uuid:family_id>/', views.family_detail, name='family_detail'),
    path('family/<uuid:family_id>/calendar/', views.family_calendar, name='family_calendar'),
    path('family/<uuid:family_id>/calendar/api/', views.family_calendar_api, name='family_calendar_api'),
    path('family/<uuid:family_id>/members/', views.family_members_management, name='family_members'),
    path('family/<uuid:family_id>/payments/', views.family_payments, name='family_payments'),
    
    # Actions sur les membres
    path('family/<uuid:family_id>/members/add/', views.add_family_member, name='add_family_member'),
    
    # === FONCTIONNALITÉS ADMINISTRATIVES CENTRALISÉES ===
    
    # Inscriptions groupées
    path('family/<uuid:family_id>/registrations/', views_admin.family_group_registration, name='group_registration'),
    path('family/<uuid:family_id>/registrations/process/', views_admin.process_group_registration, name='process_group_registration'),
    path('family/<uuid:family_id>/registrations/eligibility/', views_admin.check_competition_eligibility, name='check_eligibility'),
    
    # Centre de paiements familiaux
    path('family/<uuid:family_id>/payment-center/', views_admin.family_payment_center, name='payment_center'),
    path('family/<uuid:family_id>/payment-groups/create/', views_admin.create_payment_group, name='create_payment_group'),
    path('family/<uuid:family_id>/payment-groups/<int:payment_group_id>/process/', views_admin.process_payment, name='process_payment'),
    
    # Gestion des événements familiaux
    path('family/<uuid:family_id>/events/', views_admin.family_event_management, name='event_management'),
    path('family/<uuid:family_id>/events/create/', views_admin.create_family_event, name='create_family_event'),
    
    # Statistiques et rapports
    path('family/<uuid:family_id>/statistics/', views_admin.family_statistics, name='family_statistics'),
    path('family/<uuid:family_id>/export/', views_admin.export_family_data, name='export_family_data'),
    
    # === CALENDRIER ET NOTIFICATIONS ===
    
    # Création d'événements familiaux
    path('family/<uuid:family_id>/events/create/', views.create_family_event, name='create_family_event'),
    
    # Notifications familiales
    path('family/<uuid:family_id>/notifications/', views.family_notifications_center, name='notifications_center'),
    path('family/<uuid:family_id>/notifications/send/', views.send_family_notification, name='send_family_notification'),
    path('family/<uuid:family_id>/notifications/weekly-summary/', views.family_weekly_summary, name='family_weekly_summary'),
    
    # Outils de planification
    path('family/<uuid:family_id>/availability/', views.family_availability_check, name='family_availability_check'),
    path('family/<uuid:family_id>/suggest-time/', views.suggest_optimal_time, name='suggest_optimal_time'),
]