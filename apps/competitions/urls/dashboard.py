from django.urls import path
from django.shortcuts import redirect
from apps.competitions.views.dashboard import (
    admin, base, club, coach, coach_multidiscipline, combat,
    documentation, external_organizer, federations, finance,
    manager, participant, participant_enhanced, pro, referee, spectator, coach_emergency, coach_fixed, coach_functions, club_tabbed, club_anti_scroll
)

app_name = 'dashboard'

urlpatterns = [
    # Dashboard principal
    path('', base.dashboard, name='dashboard'),
    
    # Alias pour compatibilité
    path('home/', base.dashboard, name='home'),
    path('index/', base.dashboard, name='index'),
    
    # Dashboard admin
    path('admin/', admin.admin_dashboard, name='admin'),
    
    # Dashboard club (version originale restaurée)
    path('club/', club.club_dashboard, name='club'),
    
    # Dashboard club avec onglets (nouvelle version)
    path('club/tabbed/', club_tabbed.club_dashboard_tabbed, name='club_tabbed'),
    
    # Dashboard club avec onglets simples (test)
    path('club/tabs/', club_tabbed.club_dashboard_simple_tabs, name='club_simple_tabs'),
    
    # Test de diagnostic
    path('club/test-tabbed/', club_tabbed.club_dashboard_tabbed_test, name='club_tabbed_test'),
    
    # Dashboard club anti-scroll (nouvelle version complète)
    path('club/anti-scroll/', club_anti_scroll.club_dashboard_anti_scroll, name='club_anti_scroll'),
    
    # Dashboard coach - VERSION CORRIGÉE
    path('coach/', coach_fixed.coach_dashboard, name='coach'),
    
    # Dashboard coach multidiscipline
    path('coach/multidiscipline/', coach_multidiscipline.coach_multidiscipline_dashboard, name='coach_multidiscipline'),
    
    # Dashboard combat
    path('combat/', combat.combat_dashboard, name='combat'),
    
    # Dashboard documentation
    path('documentation/', documentation.dashboard_documentation, name='documentation'),
    path('documentation/<str:dashboard_type>/', documentation.dashboard_documentation, name='dashboard_documentation'),
    path('documentation/<str:dashboard_type>/guide/', documentation.dashboard_guide, name='dashboard_guide'),
    
    # Dashboard organisateur externe
    path('external-organizer/', external_organizer.dashboard_external_organizer, name='external_organizer'),
    
    # Dashboard fédérations
    path('federation/<int:federation_id>/', federations.federation_dashboard, name='federation'),
    
    # Dashboard finance
    path('finance/', finance.federation_finance_dashboard, name='finance'),
    
    # Dashboard manager
    path('manager/', manager.manager_dashboard, name='manager'),
    
    # Dashboard participant
    path('participant/', participant.participant_dashboard, name='participant'),
    
    # Dashboard participant - compétitions
    path('participant/competitions/', participant.participant_competitions, name='participant_competitions'),
    
    # Dashboard participant - résultats
    path('participant/results/', participant.participant_results, name='participant_results'),
    
    # Dashboard participant - profil
    path('participant/profile/', participant.participant_profile, name='participant_profile'),
    
    # Dashboard participant amélioré
    path('participant/enhanced/', participant_enhanced.participant_dashboard_enhanced, name='participant_enhanced'),
    
    # Dashboard pro
    path('pro/', pro.dashboard_pro, name='pro'),
    
    # Dashboard arbitre
    path('referee/', referee.referee_dashboard, name='referee'),
    
    # Dashboard spectateur
    path('spectator/', spectator.spectator_dashboard, name='spectator'),
    
    # URLs fonctionnelles pour le coach
    path('coach/students/', coach_functions.coach_students, name='coach_students'),
    path('coach/disciplines/', coach_functions.coach_disciplines, name='coach_disciplines'),
    path('coach/planning/', coach_functions.coach_planning, name='coach_planning'),
    path('coach/programs/', coach_functions.coach_programs, name='coach_programs'),
    path('coach/competitions/', coach_functions.coach_competitions, name='coach_competitions'),
    path('coach/stats/', coach_functions.coach_stats, name='coach_stats'),
    path('coach/finances/', coach_functions.coach_finances, name='coach_finances'),
    path('coach/testimonials/', coach_functions.coach_testimonials, name='coach_testimonials'),
    path('coach/clients/', coach_functions.coach_clients, name='coach_clients'),
    path('coach/seminars/', coach_functions.coach_seminars, name='coach_seminars'),
]

