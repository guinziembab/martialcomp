from django.urls import path
from . import views

urlpatterns = [
    path('onboarding/organisateur-non-membre/', views.onboarding_organisateur_non_membre, name='onboarding_organisateur_non_membre'),
    path('dashboard/organisateur-non-membre/', views.dashboard_organisateur_non_membre, name='dashboard_organisateur_non_membre'),
] 