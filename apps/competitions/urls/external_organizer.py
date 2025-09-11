from django.urls import path
from apps.competitions.views.external_organizer import (
    external_organizer_participants,
    external_organizer_add_participant,
    external_organizer_bulk_add_participants,
    external_organizer_edit_participant,
    external_organizer_delete_participant,
    external_organizer_export_participants,
    external_organizer_results, 
    external_organizer_reports,
    external_organizer_profile,
    external_organizer_support
)

app_name = 'external_organizer'

urlpatterns = [
    # Participants management
    path('participants/', external_organizer_participants, name='participants'),
    path('participants/add/', external_organizer_add_participant, name='add_participant'),
    path('participants/bulk-add/', external_organizer_bulk_add_participants, name='bulk_add_participants'),
    path('participants/edit/<int:participant_id>/', external_organizer_edit_participant, name='edit_participant'),
    path('participants/delete/<int:participant_id>/', external_organizer_delete_participant, name='delete_participant'),
    path('participants/export/', external_organizer_export_participants, name='export_participants'),
    
    # Results management  
    path('results/', external_organizer_results, name='results'),
    
    # Reports and analytics
    path('reports/', external_organizer_reports, name='reports'),
    
    # Profile management
    path('profile/', external_organizer_profile, name='profile'),
    
    # Support
    path('support/', external_organizer_support, name='support'),
]