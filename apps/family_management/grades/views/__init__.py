from django.core.exceptions import PermissionDenied
"""
Initialisation des vues de l'application grades.
Ce fichier importe et expose les vues principales pour faciliter l'importation.
"""

# Importer les vues principales du tableau de bord
from apps.grades.views.dashboard import grades_dashboard

# Importer les vues d'historique des grades
from apps.grades.views.history import (
    practitioner_grade_history,
    export_grade_history
)

# Importer les vues de gestion des grades
from apps.grades.views.management import (
    update_practitioner_grade,
    promote_practitioner,
    revoke_grade
)

# Importer les vues d'opérations en masse
from apps.grades.views.bulk import (
    batch_update_grades,
    bulk_grade_assignment_form,
    import_grades_from_excel
)

# Importer les vues de gestion des systèmes de grades
from apps.grades.views.systems import (
    grade_systems_list,
    grade_system_detail,
    add_grade_category,
    edit_grade_category,
    add_grade,
    edit_grade,
    delete_grade,
    reorder_grades
)

# Importer les vues API
from apps.grades.views.api import (
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
    get_grades_by_disciplines,
    create_grade_for_discipline,
    search_grades
)

# Définir les vues exposées publiquement
__all__ = [
    'grades_dashboard',
    'practitioner_grade_history',
    'export_grade_history',
    'update_practitioner_grade',
    'promote_practitioner',
    'revoke_grade',
    'batch_update_grades',
    'bulk_grade_assignment_form',
    'import_grades_from_excel',
    'grade_systems_list',
    'grade_system_detail',
    'add_grade_category',
    'edit_grade_category',
    'add_grade',
    'edit_grade',
    'delete_grade',
    'reorder_grades',
    'get_grades_by_disciplines',
    'get_grades_by_disciplines',
    'create_grade_for_discipline',
    'search_grades'
]

