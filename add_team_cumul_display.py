"""
Script pour ajouter l'affichage des scores cumulés d'équipe
"""
import os

# Patch à insérer après la div stats-row dans le template
TEAM_CUMUL_SECTION = '''
      {% if combat.type_combat == 'equipe' and combat.configuration.cumul_points_equipe %}
      <div class="team-cumul-score">
        <div class="cumul-display">
          <div class="cumul-label">Score Total Équipe</div>
          <div class="cumul-value" id="cumulRouge">{{ combat.score_cumule_rouge|default:0|floatformat:2 }}</div>
        </div>
      </div>
      {% endif %}'''

# CSS à ajouter pour le style
TEAM_CUMUL_CSS = '''
  /* Affichage des scores cumulés */
  .team-cumul-score {
    margin-top: 1.5rem;
    padding: 1rem;
    background-color: rgba(0,0,0,0.3);
    border-radius: 0.5rem;
    text-align: center;
  }
  
  .cumul-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
  
  .cumul-label {
    font-size: 0.9rem;
    text-transform: uppercase;
    opacity: 0.8;
    letter-spacing: 1px;
  }
  
  .cumul-value {
    font-size: 2.5rem;
    font-weight: bold;
    color: #ffc107;
    text-shadow: 0 0 10px rgba(255, 193, 7, 0.5);
  }
  
  .fighter-column.rouge .cumul-value {
    color: #ffffff;
  }
  
  .fighter-column.blanc .cumul-value {
    color: #212529;
  }'''

# JavaScript pour mettre à jour les scores cumulés
JS_UPDATE_CUMUL = '''
        // Mettre à jour les scores cumulés si disponibles
        if (data.score_cumule_rouge !== undefined) {
            document.getElementById('cumulRouge').textContent = data.score_cumule_rouge.toFixed(2);
        }
        if (data.score_cumule_blanc !== undefined) {
            document.getElementById('cumulBlanc').textContent = data.score_cumule_blanc.toFixed(2);
        }'''

print("=== AJOUT DE L'AFFICHAGE DES SCORES CUMULÉS ===")
print("\n1. Ajouter après chaque div.stats-row dans interface_combat_v2.html:")
print(TEAM_CUMUL_SECTION)

print("\n2. Ajouter dans la section CSS du template:")
print(TEAM_CUMUL_CSS)

print("\n3. Dans la fonction updateScores() du JavaScript, après la mise à jour des scores:")
print(JS_UPDATE_CUMUL)

print("\n4. Modifier combat.py pour importer et utiliser handle_team_cumul_scoring:")
print("""
# Au début du fichier
from .combat_team_cumul import handle_team_cumul_scoring

# Dans ajouter_action, après combat.refresh_from_db():
team_scores = handle_team_cumul_scoring(combat)

# Dans la réponse AJAX:
if request.is_ajax():
    response_data = {
        'success': True,
        'action_id': action.id,
        'score_rouge': float(combat.score_rouge),
        'score_blanc': float(combat.score_blanc)
    }
    if team_scores:
        response_data.update(team_scores)
    return JsonResponse(response_data)
""")

print("\n✅ Instructions pour implémenter le cumul des scores d'équipe générées!")