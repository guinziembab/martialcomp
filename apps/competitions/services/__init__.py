# Services module for competitions app
from .judge_service import JudgeService
from .license_service import LicenseNumberGenerator

# Sprint 2: Services pour compétitions par équipes
from .entente_service import EntenteService
from .team_merge_service import TeamMergeService
from .competition_mode_service import CompetitionModeService

# Grade Tracking: Service d'éligibilité de grade (Prompt 5)
from .grade_eligibility import GradeEligibilityService, EligibilityResult, RequirementStatus

# Prompt 3: Service de résultats et palmarès
from .results_service import (
    ResultsService,
    ResultsDashboardData,
    MedalCount,
    CompetitionStats,
    DisciplinePoints,
)

# Prompt 4: Service calendrier unifié
from .calendar_service import CalendarService, CalendarEvent

# Prompt 5: Service clôture compétition
from .competition_closure_service import CompetitionClosureService

# Service statistiques membres par catégorie d'âge/genre
from .member_statistics_service import (
    calculate_member_statistics,
    get_grade_distribution,
    AGE_CATEGORIES,
)

__all__ = [
    'JudgeService',
    'LicenseNumberGenerator',
    # Sprint 2
    'EntenteService',
    'TeamMergeService',
    'CompetitionModeService',
    # Grade Tracking
    'GradeEligibilityService',
    'EligibilityResult',
    'RequirementStatus',
    # Prompt 3: Palmarès
    'ResultsService',
    'ResultsDashboardData',
    'MedalCount',
    'CompetitionStats',
    'DisciplinePoints',
    # Prompt 4: Calendrier
    'CalendarService',
    'CalendarEvent',
    # Prompt 5: Clôture compétition
    'CompetitionClosureService',
    # Statistiques membres
    'calculate_member_statistics',
    'get_grade_distribution',
    'AGE_CATEGORIES',
]
