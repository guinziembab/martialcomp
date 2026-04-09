from django.urls import path
from django.shortcuts import redirect
from apps.competitions.views.dashboard import (
    admin, base, club, coach, coach_multidiscipline, combat,
    documentation, external_organizer, federations, federation_seasons, finance,
    manager, participant, participant_enhanced, pro, referee, spectator, coach_emergency, coach_fixed, coach_functions, club_tabbed, club_anti_scroll,
    role_switch, tutorials
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
    
    # Mise à jour du logo de l'organisation
    path('club/update-logo/', club.update_organization_logo, name='update_organization_logo'),

    # Mise à jour des paramètres du club (nom, disciplines, etc.)
    path('club/update-settings/', club.update_club_settings, name='update_club_settings'),

    # Dashboard club - résultats
    path('club/results/', club.club_results, name='club_results'),
    path('club/my-results/', club.my_results, name='my_results'),

    # Dashboard club - analyse des combats (retour instructeur)
    path('club/combat-analysis/', club.combat_analysis, name='combat_analysis'),

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
    
    # Tutoriels
    path('tutorials/', tutorials.tutorial_center, name='tutorial_center'),
    path('tutorials/<int:tutorial_id>/', tutorials.tutorial_detail, name='tutorial_detail'),
    path('tutorials/search/', tutorials.tutorial_search_api, name='tutorial_search_api'),

    # Dashboard organisateur externe
    path('external-organizer/', external_organizer.dashboard_external_organizer, name='external_organizer'),
    
    # Dashboard fédérations
    path('federations/', federations.federations_list, name='federations'),
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

    # Dashboard participant - calendrier unifié (Prompt 4)
    path('participant/calendar/', participant.participant_calendar, name='participant_calendar'),
    
    # Dashboard participant - profil
    path('participant/profile/', participant.participant_profile, name='participant_profile'),

    # Mise à jour de la photo de profil du participant
    path('participant/update-photo/', participant.update_participant_photo, name='update_photo'),

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
    path('coach/site-config/', coach_functions.coach_site_config, name='coach_site_config'),
    
    # URLs pour la bascule entre rôles (PROMPT 7)
    path('switch-to-judge/', role_switch.switch_to_judge, name='switch_to_judge'),
    path('switch-to-participant/', role_switch.switch_to_participant, name='switch_to_participant'),
    path('toggle-mode/', role_switch.toggle_dashboard_mode, name='toggle_dashboard_mode'),
    path('apply-as-judge/', role_switch.apply_as_judge, name='apply_as_judge'),

    # Dashboard juge technique (PROMPT 7)
    path('judge/', role_switch.judge_technical_dashboard, name='judge_technical'),

    # Pages additionnelles du menu juge (PROMPT 8)
    path('judge/assignments/', role_switch.judge_assignments, name='judge_assignments'),
    path('judge/performances/', role_switch.judge_performances, name='judge_performances'),
    path('judge/history/', role_switch.judge_history, name='judge_history'),
    path('judge/settings/', role_switch.judge_settings_view, name='judge_settings'),

    # Aires de combat pour juges (accès restreint)
    path('judge/combat-areas/', role_switch.judge_combat_areas, name='judge_combat_areas'),

    # Gestion des saisons sportives (fédération)
    path('federation/<int:federation_id>/seasons/',
         federation_seasons.manage_seasons, name='federation_seasons'),
    path('federation/<int:federation_id>/seasons/create/',
         federation_seasons.create_season, name='federation_create_season'),
    path('federation/<int:federation_id>/seasons/<int:season_id>/edit/',
         federation_seasons.edit_season, name='federation_edit_season'),
    path('federation/<int:federation_id>/seasons/<int:season_id>/fees/',
         federation_seasons.manage_fees, name='federation_manage_fees'),

    # Demandes de renouvellement d'affiliation
    path('federation/<int:federation_id>/renewal-requests/',
         federation_seasons.renewal_requests, name='federation_renewal_requests'),
    path('federation/<int:federation_id>/renewal-requests/<int:request_id>/process/',
         federation_seasons.process_renewal_request, name='federation_process_renewal'),

    # Factures d'affiliation
    path('federation/<int:federation_id>/affiliation-invoices/',
         federation_seasons.affiliation_invoices, name='federation_affiliation_invoices'),
    path('federation/<int:federation_id>/affiliation-invoices/<int:period_id>/generate/',
         federation_seasons.generate_invoice, name='federation_generate_invoice'),
    path('federation/<int:federation_id>/affiliation-invoices/<int:period_id>/payment/',
         federation_seasons.record_affiliation_payment, name='federation_record_payment'),

    # Historique des périodes d'affiliation
    path('federation/<int:federation_id>/affiliations/<int:affiliation_id>/periods/',
         federation_seasons.affiliation_periods, name='federation_affiliation_periods'),
]

