"""
URLs d'onboarding pour l'application competitions
"""
from django.urls import path
from apps.competitions.views.onboarding import (
    base,
    role,
    club,
    categories,
    federations,
    participant,
    judge,
    final,
    coach,
    external_organizer
)
from apps.competitions.views.onboarding.coach_simplified_profile import coach_profile_simplified
from apps.competitions.views.onboarding.emergency_views import (
    safe_club_creation,
    safe_federation_creation,
    onboarding_error,
    onboarding_complete
)

app_name = 'onboarding'

urlpatterns = [
    # Page de démarrage de l'onboarding
    path('', base.onboarding_start, name='start'),
    
    # Sélection du rôle
    path('role/', role.handle_role_selection, name='role_selection'),
    
    # Configuration du club
    # path('club/creation/', club.handle_club_creation, name='club_creation'),  # ANCIEN - DESACTIVE
    path('club/creation/', safe_club_creation, name='club_creation'),  # NOUVEAU - PATCH SECURISE
    path('club/details/', club.handle_club_details, name='club_details'),
    
    # Configuration des catégories
    path('categories/setup/', categories.handle_categories_setup, name='categories_setup'),
    
    # Configuration des fédérations
    # path('federation/', federations.handle_federation_creation, name='federation'),  # ANCIEN - DESACTIVE
    path('federation/', safe_federation_creation, name='federation'),  # NOUVEAU - PATCH SECURISE
    
    # Profils spécialisés
    path('participant/', participant.handle_participant_profile, name='participant_profile'),
    path('judge/', judge.handle_judge_profile, name='judge_profile'),
    path('coach/', coach.coach_profile, name='coach_profile'),
    path('coach/profile-simple/', coach_profile_simplified, name='coach_profile_simplified'),
    path('coach/disciplines/', coach.coach_disciplines, name='coach_disciplines'),
    path('coach/availability/', coach.coach_availability, name='coach_availability'),
    path('external-organizer/', external_organizer.handle_external_organizer_profile, name='external_organizer_profile'),
    
    # Finalisation
    path('final/', final.handle_final_setup, name='final_setup'),
    
    # Routes d'urgence (PATCH TEMPORAIRE)
    path('club/creation/safe/', safe_club_creation, name='safe_club_creation'),
    path('federation/safe/', safe_federation_creation, name='safe_federation_creation'),
    path('error/', onboarding_error, name='error'),
    path('complete/', onboarding_complete, name='complete'),
]
