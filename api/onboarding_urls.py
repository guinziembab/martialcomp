# -*- coding: utf-8 -*-
"""
URLs pour l'API d'onboarding mobile.
"""
from django.urls import path
from .onboarding_api import (
    OnboardingStatusView,
    AvailableRolesView,
    SelectRoleView,
    CreateClubView,
    CreateFederationView,
    CoachSetupView,
    CompleteOnboardingView,
    DisciplinesListView,
)

app_name = 'onboarding'

urlpatterns = [
    # Statut
    path('status/', OnboardingStatusView.as_view(), name='status'),

    # Rôles
    path('roles/', AvailableRolesView.as_view(), name='roles'),
    path('select-role/', SelectRoleView.as_view(), name='select_role'),

    # Configuration par rôle
    path('create-club/', CreateClubView.as_view(), name='create_club'),
    path('create-federation/', CreateFederationView.as_view(), name='create_federation'),
    path('coach-setup/', CoachSetupView.as_view(), name='coach_setup'),

    # Finalisation
    path('complete/', CompleteOnboardingView.as_view(), name='complete'),

    # Données
    path('disciplines/', DisciplinesListView.as_view(), name='disciplines'),
]
