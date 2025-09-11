"""
URLs pour le module de gestion des combats.
"""
from django.urls import path
from apps.competitions.views.dashboard.combat import combat_dashboard

app_name = 'combat'

urlpatterns = [
    path('', combat_dashboard, name='dashboard'),
]
