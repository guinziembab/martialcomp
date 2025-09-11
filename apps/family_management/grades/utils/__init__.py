# Utilitaires IA pour l'import/export intelligent

# Importer les fonctions du module utils principal pour compatibilité
from ..utils_module import get_grades_for_discipline, get_practitioner_grade_history, get_next_grade, get_user_club, get_user_federation, check_grade_eligibility

__all__ = [
    'get_grades_for_discipline',
    'get_practitioner_grade_history', 
    'get_next_grade',
    'get_user_club',
    'get_user_federation',
    'check_grade_eligibility'
]

