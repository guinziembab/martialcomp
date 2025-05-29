# Dans competitions/urls/dashboard.py
from django.urls import path, include
from django.views.generic.base import RedirectView
from competitions.views.dashboard import (
    federations, spectator, admin, club, participant, referee, manager, base, pro, finance, combat,
    coach_multidiscipline, documentation
)

app_name = 'dashboard'

urlpatterns = [
    path('', base.dashboard, name='index'),
    path('admin/', admin.admin_dashboard, name='admin'),
    path('club/', club.club_dashboard, name='club'),
    path('federations/', federations.federation_index, name='federations'),
    path('federation/', RedirectView.as_view(url='/dashboard/federations/', permanent=True)),
    path('manager/', manager.manager_dashboard, name='manager'),
    
    # Participant dashboard routes
    path('participant/', participant.participant_dashboard, name='participant'),
    path('participant/competitions/', participant.participant_competitions, name='participant_competitions'),
    path('participant/profile/', participant.participant_profile, name='participant_profile'),
    path('participant/results/', participant.participant_results, name='participant_results'),
    
    path('referee/', referee.referee_dashboard, name='referee'),
    path('spectator/', spectator.spectator_dashboard, name='spectator'),
    path('pro/', coach_multidiscipline.coach_multidiscipline_dashboard, name='pro'),  # Redirection vers le nouveau dashboard
    path('coach-multidiscipline/', coach_multidiscipline.coach_multidiscipline_dashboard, name='coach_multidiscipline'),  # Nouvelle route explicite
    path('combat/', combat.combat_dashboard, name='combat'),  # Combat dashboard route
    # Intégration du module de notation technique
    path('technical-scoring/', include('competitions.urls.technical_scoring')),
    
    # Intégration du module financier
    path('federation/<int:federation_id>/finance/', finance.federation_finance_dashboard, name='federation_finance'),
    
    # Documentation des dashboards
    path('documentation/', documentation.dashboard_documentation, name='documentation'),
    path('documentation/<str:dashboard_type>/', documentation.dashboard_documentation, name='dashboard_documentation'),
    path('documentation/<str:dashboard_type>/guide/', documentation.dashboard_guide, name='dashboard_guide'),
]