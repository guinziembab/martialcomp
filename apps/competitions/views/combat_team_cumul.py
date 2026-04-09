"""
Extension de la fonction ajouter_action pour supporter le cumul des points d'équipe
"""

def handle_team_cumul_scoring(combat):
    """
    Gère le cumul des points pour les compétitions par équipe.
    
    Args:
        combat: L'instance du combat en cours
        
    Returns:
        dict: Dictionnaire avec les scores cumulés ou None si non applicable
    """
    # Vérifier si le cumul est activé
    if not combat.configuration:
        return None
        
    if not hasattr(combat.configuration, 'cumul_points_equipe'):
        return None
        
    if not combat.configuration.cumul_points_equipe:
        return None
    
    # Vérifier que c'est un combat par équipe
    if combat.type_combat != 'equipe':
        return None
        
    if not combat.equipe_rouge or not combat.equipe_blanc:
        return None
    
    # Calculer les scores cumulés
    from django.db.models import Sum
    from apps.competitions.models.combat import Combat
    
    # Score cumulé pour l'équipe rouge
    score_cumule_rouge = Combat.objects.filter(
        competition=combat.competition,
        equipe_rouge=combat.equipe_rouge,
        status='termine'
    ).aggregate(total=Sum('score_rouge'))['total'] or 0
    
    # Ajouter le score actuel si le combat est en cours
    if combat.status == 'en_cours':
        score_cumule_rouge += float(combat.score_rouge)
    
    # Score cumulé pour l'équipe blanc
    score_cumule_blanc = Combat.objects.filter(
        competition=combat.competition,
        equipe_blanc=combat.equipe_blanc,
        status='termine'
    ).aggregate(total=Sum('score_blanc'))['total'] or 0
    
    # Ajouter le score actuel si le combat est en cours
    if combat.status == 'en_cours':
        score_cumule_blanc += float(combat.score_blanc)
    
    # Mettre à jour les scores cumulés si les champs existent
    if hasattr(combat, 'score_cumule_rouge') and hasattr(combat, 'score_cumule_blanc'):
        combat.score_cumule_rouge = score_cumule_rouge
        combat.score_cumule_blanc = score_cumule_blanc
        combat.save(update_fields=['score_cumule_rouge', 'score_cumule_blanc'])
    
    return {
        'score_cumule_rouge': float(score_cumule_rouge),
        'score_cumule_blanc': float(score_cumule_blanc)
    }


# Pour intégrer dans la vue ajouter_action existante, ajouter après action.save():
"""
# Exemple d'intégration dans ajouter_action:

from .combat_team_cumul import handle_team_cumul_scoring

# Après action.save() et combat.refresh_from_db()
team_scores = handle_team_cumul_scoring(combat)

if request.is_ajax():
    response_data = {
        'success': True,
        'action_id': action.id,
        'score_rouge': float(combat.score_rouge),
        'score_blanc': float(combat.score_blanc)
    }
    
    # Ajouter les scores cumulés si disponibles
    if team_scores:
        response_data.update(team_scores)
    
    return JsonResponse(response_data)
"""