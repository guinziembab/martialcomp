from django.urls import path
from apps.competitions.views.onboarding.role import handle_role_selection
from apps.competitions.views.onboarding.final import handle_final_setup

app_name = 'onboarding'

urlpatterns = [
    path('role/', handle_role_selection, name='role_selection'),
    path('final/', handle_final_setup, name='final_setup'),
    # Ajouter d'autres URLs selon vos vues d'onboarding
]
