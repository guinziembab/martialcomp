# Fonctions modifiées dans apps/competitions/views/combat.py
# À intégrer dans le fichier existant

# ============================================================================
# FONCTION: interface_combat_v2 (modifiée pour utiliser V3)
# ============================================================================
# Remplacer la ligne de return dans la fonction interface_combat_v2 :
# 
# AVANT:
# return render(request, 'competitions/combat/interface_combat_v2.html', context)
#
# APRÈS:
# # Utiliser le nouveau template V3 si disponible, sinon V2
# return render(request, 'competitions/combat/interface_combat_v3.html', context)

# ============================================================================
# FONCTION: detail_poule (améliorée avec statistiques)
# ============================================================================
@login_required
def detail_poule(request, poule_id):
    """
    Affiche les détails d'une poule, y compris les équipes/participants et les combats.
    Version améliorée avec calcul des statistiques côté serveur.
    """
    from django.shortcuts import get_object_or_404, render
    from apps.competitions.models import Poule, Combat
    
    poule = get_object_or_404(Poule, id=poule_id)
    combats = Combat.objects.filter(poule=poule).order_by('date_planifiee')
    
    # Calculer les statistiques
    total_combats = combats.count()
    combats_termines = combats.filter(status='termine').count()
    combats_en_cours = combats.filter(status='en_cours').count()
    combats_planifies = combats.filter(status='planifie').count()
    
    return render(request, 'competitions/combat/detail_poule.html', {
        'poule': poule,
        'combats': combats,
        'equipes': poule.equipes.all(),
        'pratiquants': poule.pratiquants.all(),
        'total_combats': total_combats,
        'combats_termines': combats_termines,
        'combats_en_cours': combats_en_cours,
        'combats_planifies': combats_planifies,
    })
