"""
URLs configuration pour l'API Combat
MartialComp - Interface de Combat V3
"""

from django.urls import path
from . import combat_api_views as api_views

app_name = 'combat_api'

urlpatterns = [
    # ============================================================================
    # ENDPOINTS PRINCIPAUX
    # ============================================================================
    
    # Mise à jour des scores en temps réel
    path(
        'combat/<int:combat_id>/update/',
        api_views.update_combat_scores,
        name='update_combat_scores'
    ),
    
    # Récupérer l'état actuel d'un combat
    path(
        'combat/<int:combat_id>/status/',
        api_views.get_combat_status,
        name='get_combat_status'
    ),
]
