from django.urls import path
from ..views.onboarding import (
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
    coach_profile_simplified
)

app_name = 'onboarding'

urlpatterns = [
    path('', onboarding_start, name='start'),
    path('role/', handle_role_selection, name='role_selection'),
    path('federations/', handle_federation_creation, name='federation'),
    path('club/creation/', handle_club_creation, name='club_creation'),
    path('club/details/', handle_club_details, name='club_details'),
    path('categories/setup/', handle_categories_setup, name='categories_setup'),
    path('judge/', handle_judge_profile, name='judge_profile'),
    path('participant/', handle_participant_profile, name='participant_profile'),
    path('coach/simplified/', handle_coach_simplified, name='coach_simplified'),
    path('coach/profile-simplified/', coach_profile_simplified, name='coach_profile_simplified'),
    path('spectator/', handle_final_setup, name='spectator_profile'),
    path('external-organizer/', handle_final_setup, name='external_organizer_profile'),
    path('final/', handle_final_setup, name='final_setup'),
]
