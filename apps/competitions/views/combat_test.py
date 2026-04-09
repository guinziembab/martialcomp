"""
Vue de test pour débugger l'interface de combat sans filtrage
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import json

@login_required
def interface_combat_v2_test(request, combat_id):
    """
    Vue de test qui contourne tous les filtres
    """
    # Import direct pour éviter tout filtrage
    from apps.competitions.models.combat import Combat as CombatModel
    from apps.competitions.models.combat import ActionCombat
    
    # Utiliser directement le modèle sans manager
    from django.db import connection
    
    # Requête SQL directe pour contourner tout filtrage Django
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, status, score_rouge, score_blanc, competition_id, 
                   pratiquant_rouge_id, pratiquant_blanc_id, configuration_id
            FROM competitions_combat 
            WHERE id = %s
        """, [combat_id])
        row = cursor.fetchone()
        
    if not row:
        return HttpResponse(f"""
            <h1>Combat {combat_id} introuvable dans la base de données</h1>
            <p>Requête SQL directe n'a rien trouvé.</p>
            <p><a href="/en/competitions/combat/combats/">Retour à la liste</a></p>
        """)
    
    # Créer un objet combat factice avec les données
    class FakeCombat:
        def __init__(self, data):
            self.id = data[0]
            self.status = data[1]
            self.score_rouge = float(data[2])
            self.score_blanc = float(data[3])
            self.competition_id = data[4]
            self.pratiquant_rouge_id = data[5]
            self.pratiquant_blanc_id = data[6]
            self.configuration_id = data[7]
            self.type_combat = 'individuel'
            
            # Charger les relations
            if self.pratiquant_rouge_id:
                from apps.competitions.models import Practitioner
                try:
                    self.pratiquant_rouge = Practitioner.objects.get(id=self.pratiquant_rouge_id)
                except:
                    self.pratiquant_rouge = None
            else:
                self.pratiquant_rouge = None
                
            if self.pratiquant_blanc_id:
                from apps.competitions.models import Practitioner
                try:
                    self.pratiquant_blanc = Practitioner.objects.get(id=self.pratiquant_blanc_id)
                except:
                    self.pratiquant_blanc = None
            else:
                self.pratiquant_blanc = None
                
            if self.configuration_id:
                from apps.competitions.models.combat import CombatConfiguration
                try:
                    self.configuration = CombatConfiguration.objects.get(id=self.configuration_id)
                except:
                    self.configuration = None
            else:
                self.configuration = None
                
            if self.competition_id:
                from apps.competitions.models import Competition
                try:
                    self.competition = Competition.objects.get(id=self.competition_id)
                except:
                    self.competition = None
            else:
                self.competition = None
    
    combat = FakeCombat(row)
    
    # Mode simulation
    simulation_mode = True  # Toujours en simulation pour le test
    
    # Actions vides pour le test
    actions = []
    
    context = {
        'combat': combat,
        'actions': actions,
        'simulation_mode': simulation_mode,
        'is_judge': False,
        'can_edit': True,
        'test_mode': True,
        'debug_info': {
            'combat_id': combat_id,
            'user': str(request.user),
            'raw_data': row
        }
    }
    
    if combat.configuration:
        context['valeurs_points'] = combat.configuration.valeurs_points
        context['valeurs_penalites'] = combat.configuration.valeurs_penalites
    
    return render(request, 'competitions/combat/interface_combat_v2.html', context)