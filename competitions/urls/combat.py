"""
URLs pour le module de gestion des combats.
"""
from django.urls import path
from competitions.views import combat

app_name = 'combat'  # Définir le namespace pour les URLs de combat

urlpatterns = [
    # Configurations de combat
    path('configurations/', combat.liste_configurations, name='liste_configurations'),
    path('configurations/creer/', combat.creer_configuration, name='creer_configuration'),
    path('configurations/<int:config_id>/modifier/', combat.modifier_configuration, name='modifier_configuration'),
    path('configurations/<int:config_id>/supprimer/', combat.supprimer_configuration, name='supprimer_configuration'),
    
    # Gestion des équipes
    path('equipes/', combat.liste_equipes, name='liste_equipes'),
    path('equipes/competition/<int:competition_id>/', combat.liste_equipes, name='liste_equipes'),
    path('equipes/creer/', combat.creer_equipe, name='creer_equipe'),
    path('equipes/creer/competition/<int:competition_id>/', combat.creer_equipe, name='creer_equipe'),
    path('equipes/<int:equipe_id>/', combat.detail_equipe, name='detail_equipe'),
    path('equipes/<int:equipe_id>/modifier/', combat.modifier_equipe, name='modifier_equipe'),
    path('equipes/<int:equipe_id>/supprimer/', combat.supprimer_equipe, name='supprimer_equipe'),
    path('equipes/<int:equipe_id>/ajouter-membre/', combat.ajouter_membre_equipe, name='ajouter_membre_equipe'),
    
    # Gestion des membres d'équipe
    path('membres/<int:membre_id>/modifier/', combat.modifier_membre_equipe, name='modifier_membre_equipe'),
    path('membres/<int:membre_id>/supprimer/', combat.supprimer_membre_equipe, name='supprimer_membre_equipe'),
    
    # Gestion des poules
    path('competition/<int:competition_id>/poules/', combat.liste_poules, name='liste_poules'),
    path('competition/<int:competition_id>/poules/creer/', combat.creer_poule, name='creer_poule'),
    path('competition/<int:competition_id>/poules/generer/', combat.generer_poules, name='generer_poules'),
    path('poules/<int:poule_id>/', combat.detail_poule, name='detail_poule'),
    path('poules/<int:poule_id>/modifier/', combat.modifier_poule, name='modifier_poule'),
    path('poules/<int:poule_id>/supprimer/', combat.supprimer_poule, name='supprimer_poule'),
    
    # Gestion des combats
    path('combats/', combat.liste_combats, name='liste_combats'),
    path('competition/<int:competition_id>/combats/', combat.liste_combats, name='liste_combats'),
    path('poules/<int:poule_id>/combats/', combat.liste_combats, name='liste_combats'),
    path('combats/creer/', combat.creer_combat, name='creer_combat'),
    path('competition/<int:competition_id>/combats/creer/', combat.creer_combat, name='creer_combat'),
    path('poules/<int:poule_id>/combats/creer/', combat.creer_combat, name='creer_combat'),
    path('combats/<int:combat_id>/', combat.detail_combat, name='detail_combat'),
    path('combats/<int:combat_id>/modifier/', combat.modifier_combat, name='modifier_combat'),
    path('combats/<int:combat_id>/supprimer/', combat.supprimer_combat, name='supprimer_combat'),
    path('combats/<int:combat_id>/demarrer/', combat.demarrer_combat, name='demarrer_combat'),
    path('combats/<int:combat_id>/terminer/', combat.terminer_combat, name='terminer_combat'),
    path('combats/<int:combat_id>/annuler/', combat.annuler_combat, name='annuler_combat'),
    
    # Interface de combat
    path('combats/<int:combat_id>/interface/', combat.interface_combat, name='interface_combat'),
    path('combats/<int:combat_id>/affichage/', combat.affichage_combat, name='affichage_combat'),
    path('combats/<int:combat_id>/live/', combat.monitor_match, name='monitor_match'),
    
    # API pour les actions
    path('combats/<int:combat_id>/ajouter-action/', combat.ajouter_action, name='ajouter_action'),
    path('actions/<int:action_id>/annuler/', combat.annuler_action, name='annuler_action'),
    
    # API pour l'interface temps réel
    path('api/combats/<int:combat_id>/statut/', combat.api_statut_combat, name='api_statut_combat'),
    path('api/combats/<int:combat_id>/actions/', combat.api_liste_actions, name='api_liste_actions'),
]