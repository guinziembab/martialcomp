# -*- coding: utf-8 -*-
"""
URL routing pour l'API de gestion des présences et absences.
"""

from django.urls import path
from .attendance_api import (
    TrainingSlotsListView,
    DeclarationListCreateView,
    DeclarationDetailView,
    PendingDeclarationsView,
    AcknowledgeDeclarationView,
    RollCallSessionsView,
    RollCallView,
    AttendanceStatisticsView,
    PractitionerAttendanceView,
)

app_name = 'attendance_api'

urlpatterns = [
    # Créneaux d'entraînement
    path('training-slots/', TrainingSlotsListView.as_view(), name='training_slots'),

    # Déclarations d'absence (pour pratiquants/parents)
    path('declarations/', DeclarationListCreateView.as_view(), name='declarations_list'),
    path('declarations/pending/', PendingDeclarationsView.as_view(), name='declarations_pending'),
    path('declarations/<uuid:declaration_uuid>/', DeclarationDetailView.as_view(), name='declaration_detail'),
    path('declarations/<uuid:declaration_uuid>/acknowledge/', AcknowledgeDeclarationView.as_view(), name='declaration_acknowledge'),

    # Feuilles d'appel (pour instructeurs)
    path('sessions/<str:session_date>/', RollCallSessionsView.as_view(), name='sessions_list'),
    path('sessions/<str:session_date>/<int:slot_id>/roll-call/', RollCallView.as_view(), name='roll_call'),

    # Statistiques
    path('statistics/', AttendanceStatisticsView.as_view(), name='statistics'),
    path('practitioners/<int:practitioner_id>/', PractitionerAttendanceView.as_view(), name='practitioner_attendance'),
]
