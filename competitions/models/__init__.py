# competitions/models/__init__.py

# Réorganisation des importations pour éviter les dépendances circulaires

# 1. D'abord les modèles fondamentaux (sans dépendances)
from .discipline import Discipline

from organizations.models import Organization, OrganizationMember, OrganizationRole
from .club import Club
from .federations import Federation

# 2. Ensuite les modèles liés aux utilisateurs
from .users import UserProfile
from .practitioners import Practitioner, create_user_for_practitioner
from .qualifications import PractitionerQualification, PractitionerDiscipline
from .medical import MedicalRecord, MedicalCertificate
from .membership import Membership, License

# Modèles pour les coaches multi-disciplines
try:
    from .coach_profile import CoachProfile, DisciplineExpertise, TeachingSchedule, CoachAchievement
except ImportError:
    CoachProfile = None
    DisciplineExpertise = None
    TeachingSchedule = None
    CoachAchievement = None

# 3. Puis les modèles de compétition
from .competitions import Competition, CompetitionType, CompetitionRole

# 4. Import des modèles de catégories
from .categories import CategoryTemplate, CompetitionCategory

# Import tardif pour éviter les imports circulaires
# Les modèles grades seront importés quand nécessaire dans les vues/formulaires

# 5. Les modèles de registration
from .registrations import CompetitionRegistration, JudgeCompetitionAssignment

# 6. Puis les modèles de participation qui dépendent des catégories
try:
    from .competitions import ParticipantCategoryRegistration
except ImportError:
    ParticipantCategoryRegistration = None

# 7. Ensuite les modèles de juges
try:
    from .judges import Judge, JudgeQualification, QUALIFICATION_LEVELS, JudgeTechnicalApplication, JudgeAssignment
except ImportError:
    # Import ce qui est disponible
    try:
        from .judges import Judge, JudgeQualification, QUALIFICATION_LEVELS, JudgeTechnicalApplication
        JudgeAssignment = None
    except ImportError:
        Judge = None
        JudgeQualification = None
        QUALIFICATION_LEVELS = None
        JudgeTechnicalApplication = None
        JudgeAssignment = None

# 8. Import du modèle JudgeTraining pour les formations
# Note: Ces modèles semblent être dans un autre fichier
try:
    from .judge_training import JudgeTraining, JudgeTrainingRegistration
except ImportError:
    JudgeTraining = None
    JudgeTrainingRegistration = None

from .administrators import FederationAdministrator, ClubAdministrator

# 9. Les modèles de match
from .match import Match

# 9.1 Les modèles de combat
try:
    from .combat import (
        CombatConfiguration,
        Equipe,
        MembreEquipe,
        Poule,
        Combat,
        ActionCombat
    )
except ImportError:
    CombatConfiguration = None
    Equipe = None
    MembreEquipe = None
    Poule = None
    Combat = None
    ActionCombat = None

# 10. Les modèles de notation technique
try:
    from .technical_scoring import (
        ScoringCriterion, 
        Performance, 
        Score, 
        JudgeSubmissionStatus,
        JudgeSettings,
        JudgeApplication,
        TechnicalPerformance,
        ScoringConfiguration,
        TechnicalScore,
        CompetitionRanking
    )
    
    # Import des modèles renommés de scoring_results pour éviter les conflits
    try:
        from .scoring_results import (
            TechnicalPerformanceResult, 
            TechnicalScoreResult, 
            JudgeSubmissionStatusResult,
            CompetitionResult,
            PerformanceResult,
            CategoryRanking,
            RankingEntry
        )
    except ImportError:
        TechnicalPerformanceResult = None
        TechnicalScoreResult = None
        JudgeSubmissionStatusResult = None
        CompetitionResult = None
        PerformanceResult = None
        CategoryRanking = None
        RankingEntry = None
except ImportError:
    try:
        from .technical_scoring import (
            ScoringCriterion, 
            Performance, 
            Score, 
            JudgeSubmissionStatus,
            JudgeSettings,
            JudgeApplication,
            TechnicalPerformance,
            ScoringConfiguration,
            TechnicalScore
        )
        CompetitionRanking = None
        TechnicalPerformanceResult = None
        TechnicalScoreResult = None
        JudgeSubmissionStatusResult = None
        CompetitionResult = None
    except ImportError:
        ScoringCriterion = None
        Performance = None
        Score = None
        JudgeSubmissionStatus = None
        JudgeSettings = None
        JudgeApplication = None
        TechnicalPerformance = None
        ScoringConfiguration = None
        TechnicalScore = None
        CompetitionRanking = None

# 11. Les modèles de notification
try:
    from .notifications import Notification, NotificationPreference
except ImportError:
    Notification = None
    NotificationPreference = None

# 12. Les modèles de support
try:
    from .support import SupportTicket, SupportMessage, FAQ
except ImportError:
    SupportTicket = None
    SupportMessage = None
    FAQ = None

# 13. Les modèles d'événements
try:
    from .event import Event, EventParticipant
    # Importer le modèle de feedback d'événement
    try:
        from .event_feedback import EventFeedback
    except ImportError:
        EventFeedback = None
except ImportError:
    Event = None
    EventParticipant = None

# 14. Les modèles de planification d'événements
try:
    from .event_planning import EventPoll, PollOption, PollResponse, EventReminder, EventStatistics
except ImportError:
    EventPoll = None
    PollOption = None
    PollResponse = None
    EventReminder = None
    EventStatistics = None

# 12. Références aux modèles de grades de l'application 'grades'
# Note: Nous avons déjà essayé d'importer ces modèles plus haut, donc pas besoin de répéter
GradeSystem = GradingSystem if 'GradingSystem' in locals() else None  # Alias pour compatibilité
GradeHistory = PractitionerGrade if 'PractitionerGrade' in locals() else None  # Alias pour compatibilité

# 13. La gestion des certifications
try:
    from .certifications import CertificationRegistration
    # Suppression de l'import de JudgeCertification qui semble être problématique
except ImportError:
    CertificationRegistration = None

try:
    from .categories import CategoryGrade
except ImportError:
    CategoryGrade = None

try:
    from .club_requests import AffiliationRequest
except ImportError:
    AffiliationRequest = None

# SUPPRIMER les références à ClubRole et UserClubRole qui semblent ne plus exister
# Ces classes ont peut-être été remplacées par ClubAdministrator

# Exportez les modèles pour qu'ils soient disponibles via competitions.models
__all__ = [
    # Modèles fondamentaux
    'Discipline', 'Club', 'Federation',
    
    # Modèles liés aux utilisateurs
    'UserProfile', 'Practitioner', 'create_user_for_practitioner',
    
    # Modèles de qualification et médical
    'PractitionerQualification', 'PractitionerDiscipline',
    'MedicalRecord', 'MedicalCertificate',
    'Membership', 'License',
    
    # Modèles de compétition
    'Competition', 'CompetitionType', 'CompetitionRole',
    
    # Modèles de catégories
    'CategoryTemplate', 'CompetitionCategory',
    
    # Modèles de registration
    'CompetitionRegistration', 'JudgeCompetitionAssignment',
    
    # Modèles d'administration
    'FederationAdministrator', 'ClubAdministrator',
    
    # Modèles de match
    'Match',
    
    # Modèles de combat (ajoutés conditionnellement ci-dessous),
]

# Ajout conditionnel des modèles qui pourraient ne pas exister
if CategoryGrade is not None:
    __all__.append('CategoryGrade')

if AffiliationRequest is not None:
    __all__.append('AffiliationRequest')

# Retirer JudgeCertification de __all__ car il semble ne plus exister
if CertificationRegistration is not None:
    __all__.append('CertificationRegistration')

if ParticipantCategoryRegistration is not None:
    __all__.append('ParticipantCategoryRegistration')

if Judge is not None:
    __all__.append('Judge')
    
if JudgeQualification is not None:
    __all__.append('JudgeQualification')
    
if QUALIFICATION_LEVELS is not None:
    __all__.append('QUALIFICATION_LEVELS')
    
if JudgeTechnicalApplication is not None:
    __all__.append('JudgeTechnicalApplication')

if JudgeAssignment is not None:
    __all__.append('JudgeAssignment')

# Ajout des modèles de formation
if JudgeTraining is not None:
    __all__.append('JudgeTraining')

if JudgeTrainingRegistration is not None:
    __all__.append('JudgeTrainingRegistration')

# Ajout conditionnel des modèles de notation technique
if ScoringCriterion is not None:
    __all__.extend([
        'ScoringCriterion', 
        'Performance',
        'Score',
        'JudgeSubmissionStatus',
        'JudgeSettings',
        'JudgeApplication',
        'TechnicalPerformance',
        'ScoringConfiguration',
        'TechnicalScore'
    ])

if CompetitionRanking is not None:
    __all__.append('CompetitionRanking')
    
# Ajout des modèles renommés pour éviter les conflits
if 'TechnicalPerformanceResult' in locals():
    __all__.append('TechnicalPerformanceResult')
    
if 'TechnicalScoreResult' in locals():
    __all__.append('TechnicalScoreResult')
    
if 'JudgeSubmissionStatusResult' in locals():
    __all__.append('JudgeSubmissionStatusResult')
    
if 'CompetitionResult' in locals():
    __all__.append('CompetitionResult')
    
# Ajout des autres entités de scoring_results.py
if 'PerformanceResult' in locals():
    __all__.append('PerformanceResult')
    
if 'CategoryRanking' in locals():
    __all__.append('CategoryRanking')
    
if 'RankingEntry' in locals():
    __all__.append('RankingEntry')

if Notification is not None:
    __all__.append('Notification')
    
if NotificationPreference is not None:
    __all__.append('NotificationPreference')
    
# Ajout des modèles de support
if SupportTicket is not None:
    __all__.append('SupportTicket')
    
if SupportMessage is not None:
    __all__.append('SupportMessage')
    
if FAQ is not None:
    __all__.append('FAQ')
    
# Ajout des modèles d'événements
if Event is not None:
    __all__.append('Event')
    
if EventParticipant is not None:
    __all__.append('EventParticipant')

if EventFeedback is not None:
    __all__.append('EventFeedback')

# Ajout des modèles de planification d'événements
if EventPoll is not None:
    __all__.append('EventPoll')
    
if PollOption is not None:
    __all__.append('PollOption')
    
if PollResponse is not None:
    __all__.append('PollResponse')
    
if EventReminder is not None:
    __all__.append('EventReminder')
    
if EventStatistics is not None:
    __all__.append('EventStatistics')

# Ajout des modèles de combat
if CombatConfiguration is not None:
    __all__.append('CombatConfiguration')

if Equipe is not None:
    __all__.append('Equipe')

if MembreEquipe is not None:
    __all__.append('MembreEquipe')
    
if Poule is not None:
    __all__.append('Poule')
    
if Combat is not None:
    __all__.append('Combat')
    
if ActionCombat is not None:
    __all__.append('ActionCombat')

# 14. Les modèles d'entraînement et formation
try:
    from .training import (
        TrainingSlot,
        TrainingSession,
        TrainingReservation,
        Attendance,
        TrainingProgram,
        TrainingModule,
        TrainingExercise,
        PractitionerProgress,
        ProgramEnrollment,
        PersonalGoal
    )
except ImportError:
    TrainingSlot = None
    TrainingSession = None
    TrainingReservation = None
    Attendance = None
    TrainingProgram = None
    TrainingModule = None
    TrainingExercise = None
    PractitionerProgress = None
    ProgramEnrollment = None
    PersonalGoal = None

# 15. Les modèles de communication
try:
    from .communication import (
        Conversation,
        ConversationParticipant,
        Message,
        MessageTemplate
    )
except ImportError:
    Conversation = None
    ConversationParticipant = None
    Message = None
    MessageTemplate = None

# 16. Les modèles de gestion documentaire (déplacés vers le module documents)
# Ces modèles ont été déplacés vers l'application 'documents' pour éviter les conflits
DocumentCategory = None
Document = None  
DocumentAccess = None
DocumentShare = None

# Ajout des modèles d'entraînement
if TrainingSlot is not None:
    __all__.extend([
        'TrainingSlot',
        'TrainingSession',
        'TrainingReservation',
        'Attendance',
        'TrainingProgram',
        'TrainingModule',
        'TrainingExercise',
        'PractitionerProgress',
        'ProgramEnrollment',
        'PersonalGoal'
    ])

# Ajout des modèles de communication
if Conversation is not None:
    __all__.extend([
        'Conversation',
        'ConversationParticipant',
        'Message',
        'MessageTemplate'
    ])

# Ajout des modèles de documents
if DocumentCategory is not None:
    __all__.extend([
        'DocumentCategory',
        'Document',
        'DocumentAccess',
        'DocumentShare'
    ])

# 17. Les modèles de QR code
try:
    from .qr_code import PractitionerQRCode, QRCodeScan
except ImportError:
    PractitionerQRCode = None
    QRCodeScan = None

# Ajout des modèles de QR code
if PractitionerQRCode is not None:
    __all__.extend([
        'PractitionerQRCode',
        'QRCodeScan'
    ])