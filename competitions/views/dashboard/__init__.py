from .base import dashboard
from .admin import admin_dashboard
from .club import club_dashboard
from .referee import referee_dashboard
from .participant import participant_dashboard
from .spectator import spectator_dashboard
from .pro import dashboard_pro
from .manager import manager_dashboard
from .federations import federation_dashboard
from .combat import combat_dashboard
from .coach_multidiscipline import coach_multidiscipline_dashboard

__all__ = [
    'dashboard',
    'admin_dashboard',
    'club_dashboard',
    'referee_dashboard',
    'participant_dashboard',
    'spectator_dashboard',
    'dashboard_pro',
    'manager_dashboard',
    'federation_dashboard',
    'combat_dashboard',
    'coach_multidiscipline_dashboard',
]