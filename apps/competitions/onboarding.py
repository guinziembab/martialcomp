from apps.competitions.views.onboarding import (
    onboarding_start,
    handle_role_selection,
    handle_federation_creation,
    handle_club_creation,
    handle_club_details,
    handle_categories_setup,
    handle_judge_profile,
    handle_participant_profile,
    handle_final_setup,
    handle_coach_simplified,
    coach_profile_simplified,
)

from apps.competitions.views.onboarding.external_organizer import handle_external_organizer_profile

from django.urls import path

app_name = 'onboarding'

urlpatterns = [
    # Route de base d'onboarding
    path('', onboarding_start, name='start'),
    
    # Ã‰tapes d'onboarding principales
    path('role/', handle_role_selection, name='role_selection'),
    path('role_selection/', handle_role_selection, name='role_selection_alias'),
    path('federations/', handle_federation_creation, name='federation'),
    path('club/creation/', handle_club_creation, name='club_creation'),
    path('club/details/', handle_club_details, name='club_details'),
    path('categories/setup/', handle_categories_setup, name='categories_setup'),
    path('judge/', handle_judge_profile, name='judge_profile'),
    path('participant/', handle_participant_profile, name='participant_profile'),
    path('final/', handle_final_setup, name='final_setup'),
    
    # Routes pour coach
    path('coach/simplified/', handle_coach_simplified, name='coach_simplified'),
    path('coach/profile-simple/', coach_profile_simplified, name='coach_profile_simplified'),
    path('external_organizer/', handle_external_organizer_profile, name='external_organizer_profile'),
]
