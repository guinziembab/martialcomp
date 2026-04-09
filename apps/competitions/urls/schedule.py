# apps/competitions/urls/schedule.py
"""
URLs pour la programmation des catégories par tatami.
"""

from django.urls import path
from apps.competitions.views import schedule_api

app_name = 'schedule'

urlpatterns = [
    # Récupérer la programmation
    path(
        'competition/<int:competition_id>/',
        schedule_api.get_schedule,
        name='get_schedule'
    ),

    # Assignation aux tatamis
    path(
        'competition/<int:competition_id>/assign/',
        schedule_api.assign_category_to_tatami,
        name='assign'
    ),
    path(
        'competition/<int:competition_id>/unassign/',
        schedule_api.unassign_category,
        name='unassign'
    ),

    # Réordonnancement
    path(
        'competition/<int:competition_id>/move/',
        schedule_api.move_category,
        name='move'
    ),
    path(
        'competition/<int:competition_id>/reorder/',
        schedule_api.reorder_categories,
        name='reorder'
    ),

    # Mise à jour des horaires
    path(
        'competition/<int:competition_id>/update-time/',
        schedule_api.update_category_time,
        name='update_time'
    ),

    # Génération automatique
    path(
        'competition/<int:competition_id>/auto-generate/',
        schedule_api.auto_generate_schedule,
        name='auto_generate'
    ),
]
