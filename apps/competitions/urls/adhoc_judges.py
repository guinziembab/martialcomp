# apps/competitions/urls/adhoc_judges.py
"""
URLs pour la gestion des juges ad-hoc (temporaires/bénévoles).
"""

from django.urls import path
from apps.competitions.views import adhoc_judges

app_name = 'adhoc_judges'

urlpatterns = [
    # API pour les gestionnaires de compétition
    path(
        'competition/<int:competition_id>/list/',
        adhoc_judges.adhoc_judges_list,
        name='list'
    ),
    path(
        'competition/<int:competition_id>/eligible/',
        adhoc_judges.eligible_practitioners,
        name='eligible'
    ),
    path(
        'competition/<int:competition_id>/recruit/',
        adhoc_judges.recruit_adhoc_judge,
        name='recruit'
    ),

    # API pour la gestion individuelle des juges ad-hoc
    path(
        '<int:adhoc_id>/update/',
        adhoc_judges.update_adhoc_judge,
        name='update'
    ),
    path(
        '<int:adhoc_id>/activate/',
        adhoc_judges.activate_adhoc_judge,
        name='activate'
    ),
    path(
        '<int:adhoc_id>/deactivate/',
        adhoc_judges.deactivate_adhoc_judge,
        name='deactivate'
    ),
    path(
        '<int:adhoc_id>/briefing/',
        adhoc_judges.mark_briefing_completed,
        name='briefing'
    ),
    path(
        '<int:adhoc_id>/rate/',
        adhoc_judges.rate_adhoc_judge,
        name='rate'
    ),
    path(
        '<int:adhoc_id>/delete/',
        adhoc_judges.delete_adhoc_judge,
        name='delete'
    ),

    # API pour le pratiquant (voir ses assignations)
    path(
        'my-assignments/',
        adhoc_judges.my_adhoc_assignments,
        name='my_assignments'
    ),

    # API pour les affectations de juges aux catégories (drag & drop)
    path(
        'competition/<int:competition_id>/assign-category/',
        adhoc_judges.assign_judge_to_category,
        name='assign_category'
    ),
    path(
        'competition/<int:competition_id>/remove-category/',
        adhoc_judges.remove_judge_from_category,
        name='remove_category'
    ),
    path(
        'competition/<int:competition_id>/category/<int:category_id>/judges/',
        adhoc_judges.get_category_judges,
        name='category_judges'
    ),
]
