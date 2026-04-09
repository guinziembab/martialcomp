# competitions/urls/role_switch.py
"""
URLs pour le switch de contexte/rôle.
"""

from django.urls import path
from apps.competitions.views import role_switch

app_name = 'role_switch'

urlpatterns = [
    # API pour obtenir les contextes disponibles
    path('contexts/', role_switch.get_available_contexts, name='get_contexts'),

    # API pour changer de contexte
    path('contexts/switch/', role_switch.switch_context, name='switch_context'),

    # Partial HTML pour le context switcher (AJAX)
    path('contexts/partial/', role_switch.context_switcher_partial, name='context_partial'),
]
