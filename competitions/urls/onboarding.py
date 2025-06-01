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
    handle_final_setup
)
from ..views.onboarding.coach import coach_disciplines, coach_availability
from ..views.onboarding.coach_simplified import handle_coach_simplified
from ..views.onboarding.coach_simplified_profile import coach_profile_simplified
from ..views.onboarding.coach_fix import coach_profile_fix
from ..views.onboarding.coach_simple_direct import coach_direct_registration

app_name = 'onboarding'  # Ajout de l'app_name manquant

urlpatterns = [
    path('', onboarding_start, name='start'),
    path('role/', handle_role_selection, name='role_selection'),
    path('federations/', handle_federation_creation, name='federation'),
    path('club/creation/', handle_club_creation, name='club_creation'),
    path('club/details/', handle_club_details, name='club_details'),
    path('categories/setup/', handle_categories_setup, name='categories_setup'),
    path('judge/', handle_judge_profile, name='judge_profile'),
    
    # Route directe pour coach sans formset - approche sécurisée
    path('coach/profile/', coach_direct_registration, name='coach_profile'),
    
    # Anciennes routes pour référence (désactivées pour éviter les problèmes)
    # path('coach/disciplines/', coach_disciplines, name='coach_disciplines'),
    # path('coach/availability/', coach_availability, name='coach_availability'),
    # path('coach/simplified/', handle_coach_simplified, name='coach_simplified'),
    # path('coach/profile-simple/', coach_profile_simplified, name='coach_profile_simplified'),
    
    path('participant/', handle_participant_profile, name='participant_profile'),
    path('final/', handle_final_setup, name='final_setup'),
]
