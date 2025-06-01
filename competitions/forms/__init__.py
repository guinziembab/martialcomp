# competitions/forms/__init__.py

# Importation de tous les formulaires pour les rendre disponibles depuis competitions.forms

# Définir la liste des formulaires disponibles à l'importation
__all__ = []

# Formulaires de base
from .competitions import CompetitionForm
from .categories import CompetitionCategoryForm, CategoryTemplateForm  
from .practitioners import PractitionerForm
from .judges import JudgeQualificationForm, JudgeCompetitionAssignmentForm, JudgeProfileForm
from .registrations import CompetitionRegistrationForm
from .qualification import PractitionerGradeForm
from .trainings import JudgeTrainingForm  # Changé de ".training" à ".trainings"
from .club_forms import ClubAffiliationForm
from .practitioner import (
    PractitionerProfileForm,  # Formulaire de profil pratiquant
    NotificationPreferenceForm,  # Formulaire de préférences de notification
    SupportTicketForm,  # Formulaire de ticket de support
    PersonalGoalForm,  # Formulaire d'objectif personnel
    TrainingReservationForm  # Formulaire de réservation d'entraînement
)

# Gestion des erreurs d'importation potentielles pour les formulaires d'authentification
try:
    from .auth import UserRegistrationForm
    __all__.append('UserRegistrationForm')
except ImportError:
    # Le module d'authentification n'existe pas ou n'a pas été correctement configuré
    pass

# Formulaires de notation technique
from .technical_scoring import (
    ScoringConfigurationForm,
    ScoringCriterionForm,
    ScoringCriterionFormSet,
    TechnicalScoreForm,
    JudgeAssignmentForm,
    PerformanceOrderForm,
    StartPerformanceForm,
    PerformanceResultsForm,
    JudgeSettingsForm,
    JudgeApplicationForm,
    ScoreForm
)

# Formulaires de gestion des événements
try:
    from .event_forms import EventForm, EventParticipantForm, EventFilterForm
    from .event_feedback import EventFeedbackForm
    from .event_import_export import EventImportForm, EventExportForm
    from .event_notifications import EventNotificationForm, EventInvitationForm
    from .event_planning import (
        EventPollForm, 
        PollOptionForm, 
        PollResponseForm, 
        BulkPollResponseForm,
        EventReminderForm,
        PollOptionFormSet
    )
except ImportError:
    # Les formulaires d'événement ne sont pas disponibles
    EventForm = None
    EventParticipantForm = None
    EventFilterForm = None
    EventFeedbackForm = None
    EventImportForm = None
    EventExportForm = None
    EventNotificationForm = None
    EventInvitationForm = None
    EventPollForm = None
    PollOptionForm = None
    PollResponseForm = None
    BulkPollResponseForm = None
    EventReminderForm = None
    PollOptionFormSet = None

# Formulaires de gestion des combats
try:
    from .combat_forms import (
        CombatConfigurationForm,
        EquipeForm,
        MembreEquipeForm,
        PouleForm,
        CombatForm,
        ActionCombatForm,
        GenerationPoulesForm,
        AttributionPointForm
    )
except ImportError:
    # Les formulaires de combat ne sont pas disponibles
    CombatConfigurationForm = None
    EquipeForm = None
    MembreEquipeForm = None
    PouleForm = None
    CombatForm = None
    ActionCombatForm = None
    GenerationPoulesForm = None
    AttributionPointForm = None

# Ajouter les formulaires importés à __all__
__all__.extend([
    # Formulaires de base
    'CompetitionForm',
    'CompetitionCategoryForm',
    'CategoryTemplateForm',
    'PractitionerForm',
    'PractitionerProfileForm',
    'NotificationPreferenceForm',
    'SupportTicketForm',
    'PersonalGoalForm',
    'TrainingReservationForm',
    'JudgeQualificationForm',
    'JudgeCompetitionAssignmentForm',
    'JudgeProfileForm',
    'CompetitionRegistrationForm',
    'PractitionerGradeForm',
    'JudgeTrainingForm',
    
    # Formulaires de notation technique
    'ScoringConfigurationForm',
    'ScoringCriterionForm',
    'ScoringCriterionFormSet',
    'TechnicalScoreForm',
    'JudgeAssignmentForm',
    'PerformanceOrderForm',
    'StartPerformanceForm',
    'PerformanceResultsForm',
    'JudgeSettingsForm',
    'JudgeApplicationForm',
    'ScoreForm'
])

# Ajouter conditionnellement les formulaires d'événement
if EventForm is not None:
    __all__.extend([
        'EventForm',
        'EventParticipantForm',
        'EventFilterForm',
        'EventFeedbackForm',
        'EventImportForm',
        'EventExportForm',
        'EventNotificationForm',
        'EventInvitationForm',
        'EventPollForm',
        'PollOptionForm',
        'PollResponseForm',
        'BulkPollResponseForm',
        'EventReminderForm',
        'PollOptionFormSet'
    ])

# Ajouter conditionnellement les formulaires de combat
if CombatConfigurationForm is not None:
    __all__.extend([
        'CombatConfigurationForm',
        'EquipeForm',
        'MembreEquipeForm',
        'PouleForm',
        'CombatForm',
        'ActionCombatForm',
        'GenerationPoulesForm',
        'AttributionPointForm'
    ])