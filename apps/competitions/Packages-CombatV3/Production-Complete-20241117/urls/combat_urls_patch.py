# Patch pour apps/competitions/urls/combat.py
# IMPORTANT: Inverser l'ordre des URLs detail_poule et liste_poules

# AVANT (incorrect):
# path('poules/<int:competition_id>/', combat.liste_poules, name='liste_poules'),
# path('poules/<int:poule_id>/', combat.detail_poule, name='detail_poule'),

# APRÈS (correct):
# IMPORTANT: detail_poule doit être AVANT liste_poules car les deux patterns sont identiques
# Django matche dans l'ordre, donc on met le plus spécifique en premier
path('poules/<int:poule_id>/', combat.detail_poule, name='detail_poule'),
path('poules/<int:competition_id>/', combat.liste_poules, name='liste_poules'),
