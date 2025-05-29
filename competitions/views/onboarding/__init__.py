from .base import onboarding_start
from .role import handle_role_selection
from .federations import handle_federation_creation
from .club import handle_club_creation, handle_club_details
from .categories import handle_categories_setup
from .judge import handle_judge_profile
from .participant import handle_participant_profile
from .final import handle_final_setup
from .coach_simplified import handle_coach_simplified
from .coach_simplified_profile import coach_profile_simplified

__all__ = [
    'onboarding_start',
    'handle_role_selection',
    'handle_federation_creation',
    'handle_club_creation',
    'handle_club_details',
    'handle_categories_setup',
    'handle_judge_profile',
    'handle_participant_profile',
    'handle_final_setup',
    'handle_coach_simplified',
    'coach_profile_simplified',
]