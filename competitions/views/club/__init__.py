"""
Module pour la gestion des clubs et de leurs membres.
"""

from .practitioners import (
    practitioners_list, practitioner_form, practitioner_create, 
    practitioner_update, practitioner_detail, practitioner_delete,
    create_user_for_practitioner, link_user_to_practitioner
)

from .registrations import (
    registrations_list, register_practitioner, available_competitions,
    register_multiple_practitioners, competition_registration_form,
    club_bulk_registration, select_practitioner_for_registration,
    cancel_registration
)

from .qualifications import (
    qualification_form, judges_list, delete_qualification
)

from .import_export import (
    import_export_data
)

from .profiles import (
    user_profile, practitioner_profile, update_practitioner_profile
)
from .competitions import club_competitions, club_competition_detail # ou remplacez par le nom correct du fichier où vous avez placé la fonction
from .judges import judges_list, judge_assignments, judge_add
from .technical_scoring import technical_scoring, competition_scoring, performance_detail
from .utils import (
    club_settings,  # Import existant
    create_custom_category,  # Nouvel import
)
from .settings import manage_club_disciplines, join_federation, manage_requests

# Alias pour la compatibilité avec l'ancien code
club_practitioners = practitioners_list