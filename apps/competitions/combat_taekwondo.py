"""
URLs pour le module de gestion des combats de Taekwondo.
"""
from django.urls import path

from apps.competitions.views import combat_taekwondo

app_name = 'combat_taekwondo'

urlpatterns = [
    # Liste des combats
    path('liste/', 
         combat_taekwondo.liste_combats_taekwondo, 
         name='liste_combats'),
    path('liste/<int:competition_id>/', 
         combat_taekwondo.liste_combats_taekwondo, 
         name='liste_combats_competition'),
    
    # Détail d'un combat
    path('combats/<int:combat_id>/', 
         combat_taekwondo.detail_combat_taekwondo, 
         name='detail_combat'),
    
    # Interface d'arbitrage
    path('combats/<int:combat_id>/interface/', 
         combat_taekwondo.interface_combat_taekwondo, 
         name='interface_combat'),
    
    # Actions de gestion du combat
    path('combats/<int:combat_id>/demarrer/', 
         combat_taekwondo.demarrer_combat_taekwondo, 
         name='demarrer_combat'),
    path('combats/<int:combat_id>/terminer/', 
         combat_taekwondo.terminer_combat_taekwondo, 
         name='terminer_combat'),
    
    # API pour les actions
    path('combats/<int:combat_id>/ajouter-action/', 
         combat_taekwondo.ajouter_action_taekwondo, 
         name='ajouter_action'),
    path('actions/<int:action_id>/annuler/', 
         combat_taekwondo.annuler_action_taekwondo, 
         name='annuler_action'),
    
    # API pour le statut du combat (temps réel)
    path('api/combats/<int:combat_id>/statut/', 
         combat_taekwondo.api_statut_combat_taekwondo, 
         name='api_statut_combat'),
]

