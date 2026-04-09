from django.urls import path
from apps.competitions.views import combat
from apps.competitions.views.combat_debug import interface_combat_v2_debug
from apps.competitions.views.combat_test import interface_combat_v2_test
from apps.competitions.views.combat_extra import update_duree_combat, suivi_poule, classement_live, classement_live_pdf
from apps.competitions.views import aires_combat
from apps.competitions.views import podium_ceremony

app_name = 'combat'

urlpatterns = [
    path('', combat.liste_combats, name='liste_combats'),
    path('configurations/', combat.liste_configurations, name='liste_configurations'),
    path('configurations/creer/', combat.creer_configuration, name='creer_configuration'),
    path('configurations/<int:config_id>/modifier/', combat.modifier_configuration, name='modifier_configuration'),
    path('configurations/<int:config_id>/supprimer/', combat.supprimer_configuration, name='supprimer_configuration'),
    path('equipes/', combat.liste_equipes, name='liste_equipes'),
    path('equipes/competition/<int:competition_id>/', combat.liste_equipes, name='liste_equipes_competition'),
    path('equipes/par-categorie/', combat.liste_equipes_par_categorie, name='liste_equipes_par_categorie'),
    path('equipes/par-categorie/competition/<int:competition_id>/', combat.liste_equipes_par_categorie, name='liste_equipes_par_categorie_competition'),
    path('equipes/creer/', combat.creer_equipe, name='creer_equipe'),
    path('equipes/creer/competition/<int:competition_id>/', combat.creer_equipe, name='creer_equipe_competition'),
    path('equipes/<int:equipe_id>/', combat.detail_equipe, name='detail_equipe'),
    path('equipes/<int:equipe_id>/modifier/', combat.modifier_equipe, name='modifier_equipe'),
    path('equipes/<int:equipe_id>/supprimer/', combat.supprimer_equipe, name='supprimer_equipe'),
    path('equipes/<int:equipe_id>/ajouter-membre/', combat.ajouter_membre_equipe, name='ajouter_membre_equipe'),
    path('membres/<int:membre_id>/modifier/', combat.modifier_membre_equipe, name='modifier_membre_equipe'),
    path('membres/<int:membre_id>/supprimer/', combat.supprimer_membre_equipe, name='supprimer_membre_equipe'),
    # URLs des poules - patterns distincts pour éviter les conflits
    # Redirection pour les anciens URLs (compatibilité)
    path('poules/<int:id>/', combat.redirect_poule_legacy, name='redirect_poule_legacy'),
    path('poules/competition/<int:competition_id>/', combat.liste_poules, name='liste_poules'),
    path('poules/detail/<int:poule_id>/', combat.detail_poule, name='detail_poule'),
    path('poules/competition/<int:competition_id>/creer/', combat.creer_poule, name='creer_poule'),
    path('poules/detail/<int:poule_id>/modifier/', combat.modifier_poule, name='modifier_poule'),
    path('poules/detail/<int:poule_id>/supprimer/', combat.supprimer_poule, name='supprimer_poule'),
    path('poules/competition/<int:competition_id>/generer/', combat.generer_poules, name='generer_poules'),
    path('poules/competition/<int:competition_id>/reset/', combat.reset_poules, name='reset_poules'),
    path('poules/competition/<int:competition_id>/category/<int:category_id>/supprimer/', combat.supprimer_poules_categorie, name='supprimer_poules_categorie'),
    path('poules/competition/<int:competition_id>/reorganiser/', combat.reorganiser_poules, name='reorganiser_poules'),
    path('combats/', combat.liste_combats, name='liste_combats'),
    path('combats/competition/<int:competition_id>/', combat.liste_combats, name='liste_combats_competition'),
    path('combats/creer/', combat.creer_combat, name='creer_combat'),
    path('combats/creer/competition/<int:competition_id>/', combat.creer_combat, name='creer_combat_competition'),
    path('combats/creer/poule/<int:poule_id>/', combat.creer_combat, name='creer_combat_poule'),
    path('combats/<int:combat_id>/', combat.detail_combat, name='detail_combat'),
    path('combats/<int:combat_id>/modifier/', combat.modifier_combat, name='modifier_combat'),
    path('combats/<int:combat_id>/supprimer/', combat.supprimer_combat, name='supprimer_combat'),
    path('combats/<int:combat_id>/demarrer/', combat.demarrer_combat, name='demarrer_combat'),
    path('combats/<int:combat_id>/terminer/', combat.terminer_combat, name='terminer_combat'),
    path('combats/<int:combat_id>/annuler/', combat.annuler_combat, name='annuler_combat'),
    path('combats/<int:combat_id>/interface/', combat.interface_combat, name='interface_combat'),
    path('combats/<int:combat_id>/interface-v2/', combat.interface_combat_v2, name='interface_combat_v2'),
    path('combats/<int:combat_id>/interface-v2-debug/', interface_combat_v2_debug, name='interface_combat_v2_debug'),
    path('combats/<int:combat_id>/interface-v2-test/', interface_combat_v2_test, name='interface_combat_v2_test'),
    path('combats/<int:combat_id>/monitor/', combat.monitor_match, name='monitor_match'),
    path('combats/<int:combat_id>/affichage/', combat.affichage_combat, name='affichage_combat'),
    path('public/live/', combat.vue_publique_live, name='vue_publique_live'),
    path('combats/<int:combat_id>/ajouter-action/', combat.ajouter_action, name='ajouter_action'),
    path('actions/<int:action_id>/annuler/', combat.annuler_action, name='annuler_action'),
    path('combats/<int:combat_id>/api-statut/', combat.api_statut_combat, name='api_statut_combat'),
    path('combats/<int:combat_id>/api-actions/', combat.api_liste_actions, name='api_liste_actions'),
    path('combats/<int:combat_id>/api-timer-sync/', combat.api_timer_sync, name='api_timer_sync'),
    
    # Nouvelles routes pour les fonctionnalités avancées
    path('combats/<int:combat_id>/update-duree/', update_duree_combat, name='update_duree_combat'),
    path('poules/detail/<int:poule_id>/suivi/', suivi_poule, name='suivi_poule'),
    path('competitions/<int:competition_id>/classement-live/', classement_live, name='classement_live'),
    path('competitions/<int:competition_id>/classement-live/pdf/', classement_live_pdf, name='classement_live_pdf'),

    # FEATURE #9: Phase finale après poules
    path('competitions/<int:competition_id>/phase-finale/', combat.generer_phase_finale, name='generer_phase_finale'),

    # FEATURE #10: Phase finale PAR CATÉGORIE (demi-finales + finale automatiques)
    path('competitions/<int:competition_id>/category/<int:category_id>/phase-finale/', combat.generer_phase_finale_categorie, name='generer_phase_finale_categorie'),
    path('competitions/<int:competition_id>/category/<int:category_id>/promouvoir-finale/', combat.promouvoir_vainqueurs_finale, name='promouvoir_vainqueurs_finale'),

    # API pour charger les catégories d'une compétition
    path('api/competition/<int:competition_id>/categories/', combat.api_categories_competition, name='api_categories_competition'),

    # ==========================================================================
    # SPRINT 1-3: Nouvelles fonctionnalités équipes
    # ==========================================================================

    # Sprint 1: Configuration des équipes
    path('competitions/<int:competition_id>/team-config/', combat.team_configuration, name='team_configuration'),

    # Sprint 2: Gestion des Ententes (prêt de joueurs)
    path('competitions/<int:competition_id>/ententes/', combat.liste_ententes, name='liste_ententes'),
    path('competitions/<int:competition_id>/ententes/creer/', combat.creer_entente, name='creer_entente'),
    path('ententes/<int:entente_id>/approuver/', combat.approuver_entente, name='approuver_entente'),
    path('ententes/<int:entente_id>/refuser/', combat.refuser_entente, name='refuser_entente'),
    path('ententes/<int:entente_id>/annuler/', combat.annuler_entente, name='annuler_entente'),

    # Sprint 2: Gestion des Fusions d'équipes
    path('competitions/<int:competition_id>/fusions/', combat.liste_fusions, name='liste_fusions'),
    path('competitions/<int:competition_id>/fusions/creer/', combat.creer_fusion, name='creer_fusion'),
    path('fusions/<int:fusion_id>/approuver/', combat.approuver_fusion, name='approuver_fusion'),
    path('fusions/<int:fusion_id>/refuser/', combat.refuser_fusion, name='refuser_fusion'),
    path('fusions/<int:fusion_id>/executer/', combat.executer_fusion, name='executer_fusion'),
    path('fusions/<int:fusion_id>/annuler/', combat.annuler_fusion, name='annuler_fusion'),

    # Sprint 2: Basculement mode équipe/individuel
    path('competitions/<int:competition_id>/mode-switch/', combat.competition_mode_switch, name='competition_mode_switch'),

    # Sprint 3: Podium équipes
    path('competitions/<int:competition_id>/podium-equipes/', combat.podium_equipes, name='podium_equipes'),
    path('competitions/<int:competition_id>/export-podium/', combat.export_podium, name='export_podium'),

    # API pour les équipes d'un club
    path('api/clubs/<int:club_id>/equipes/', combat.api_equipes_club, name='api_equipes_club'),

    # Ajouter un combat dans une poule
    path('poules/<int:poule_id>/ajouter-combat/', combat.ajouter_combat_poule, name='ajouter_combat_poule'),

    # API drag & drop membre dans équipe
    path('api/equipes/<int:equipe_id>/add-member/', combat.api_add_member_to_team, name='api_add_member_to_team'),

    # API recherche pratiquants + ajout rapide catégorie
    path('api/competition/<int:competition_id>/search-practitioners/', combat.api_search_practitioners, name='api_search_practitioners'),
    path('api/competition/<int:competition_id>/quick-add-category/', combat.api_quick_add_to_category, name='api_quick_add_to_category'),

    # ==========================================================================
    # MODE KIOSQUE: Aires de Combat (Multi-Tatami)
    # ==========================================================================

    # Gestion des aires (manager)
    path('competitions/<int:competition_id>/aires/',
         aires_combat.liste_aires, name='liste_aires'),
    path('competitions/<int:competition_id>/aires/creer/',
         aires_combat.creer_aire, name='creer_aire'),
    path('aires/<int:aire_id>/',
         aires_combat.detail_aire, name='detail_aire'),
    path('aires/<int:aire_id>/modifier/',
         aires_combat.modifier_aire, name='modifier_aire'),
    path('aires/<int:aire_id>/supprimer/',
         aires_combat.supprimer_aire, name='supprimer_aire'),
    path('aires/<int:aire_id>/regenerer-pin/',
         aires_combat.regenerer_pin_aire, name='regenerer_pin_aire'),

    # Interface Kiosque (accès public protégé par PIN)
    path('kiosque/<uuid:token>/',
         aires_combat.aire_kiosque_login, name='aire_kiosque_login'),
    path('kiosque/<uuid:token>/interface/',
         aires_combat.aire_kiosque_interface, name='aire_kiosque_interface'),
    path('kiosque/<uuid:token>/logout/',
         aires_combat.aire_kiosque_logout, name='aire_kiosque_logout'),
    path('kiosque/<uuid:token>/combat/<int:combat_id>/',
         aires_combat.aire_kiosque_combat, name='aire_kiosque_combat'),

    # API Kiosque
    path('api/kiosque/<uuid:token>/combats/',
         aires_combat.api_kiosque_combats, name='api_kiosque_combats'),

    # ==========================================================================
    # CÉRÉMONIE PODIUM: Affichage cérémoniel avec révélation progressive
    # ==========================================================================

    # Vue principale cérémonie avec navigation entre catégories
    path('competitions/<int:competition_id>/podium-ceremony/',
         podium_ceremony.podium_ceremony, name='podium_ceremony'),

    # Écran d'affichage spectateurs (synchronisé avec pilotage)
    path('competitions/<int:competition_id>/podium-display/',
         podium_ceremony.podium_display, name='podium_display'),

    # Vue d'ensemble de tous les podiums
    path('competitions/<int:competition_id>/podium-overview/',
         podium_ceremony.podium_overview, name='podium_overview'),

    # API pour récupérer les données d'une catégorie spécifique (AJAX)
    path('api/competitions/<int:competition_id>/podium/category/<int:category_index>/',
         podium_ceremony.podium_category_api, name='podium_category_api'),

    # API pour la liste ordonnée des catégories
    path('api/competitions/<int:competition_id>/podium/categories/',
         podium_ceremony.podium_all_categories_api, name='podium_all_categories_api'),
] 
