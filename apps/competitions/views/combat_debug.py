"""
Vue temporaire pour débugger le problème d'accès aux combats
"""
from django.shortcuts import render
from django.http import HttpResponse
from apps.competitions.models.combat import Combat, ActionCombat

def interface_combat_v2_debug(request, combat_id):
    """
    Vue de debug sans get_object_or_404
    """
    try:
        # Essayer différentes méthodes pour récupérer le combat
        combat = None
        
        # Méthode 1: Direct
        try:
            combat = Combat.objects.get(id=combat_id)
            method = "Direct Combat.objects.get()"
        except Combat.DoesNotExist:
            pass
        
        # Méthode 2: Filter
        if not combat:
            combat = Combat.objects.filter(id=combat_id).first()
            if combat:
                method = "Combat.objects.filter().first()"
        
        # Méthode 3: Sans manager
        if not combat:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM competitions_combat WHERE id = %s", [combat_id])
                row = cursor.fetchone()
                if row:
                    method = f"SQL direct - Row exists with ID {row[0]}"
                else:
                    method = "SQL direct - No row found"
        
        if combat:
            # Mode simulation
            simulation_mode = combat.status != 'en_cours' or request.GET.get('simulation') == '1'
            
            # Récupérer les actions
            actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:20]
            
            context = {
                'combat': combat,
                'actions': actions,
                'simulation_mode': simulation_mode,
                'is_judge': hasattr(request.user, 'judge'),
                'can_edit': request.user.is_staff if request.user.is_authenticated else False,
                'debug_info': {
                    'method': method,
                    'user': str(request.user),
                    'is_authenticated': request.user.is_authenticated,
                    'combat_id': combat_id,
                    'combat_exists': True
                }
            }
            
            if combat.configuration:
                context['valeurs_points'] = combat.configuration.valeurs_points
                context['valeurs_penalites'] = combat.configuration.valeurs_penalites
            
            return render(request, 'competitions/combat/interface_combat_v2.html', context)
        else:
            # Combat non trouvé - afficher des infos de debug
            from apps.competitions.models import Competition
            
            debug_info = {
                'combat_id': combat_id,
                'method_tried': method,
                'all_combat_ids': list(Combat.objects.values_list('id', flat=True)),
                'user': str(request.user),
                'is_authenticated': request.user.is_authenticated,
                'is_superuser': request.user.is_superuser if request.user.is_authenticated else False,
                'competitions': list(Competition.objects.values_list('id', 'title'))
            }
            
            return HttpResponse(f"""
                <h1>Combat {combat_id} non trouvé</h1>
                <h2>Informations de debug:</h2>
                <pre>{debug_info}</pre>
                <h3>Combats existants: {debug_info['all_combat_ids']}</h3>
                <h3>Méthode essayée: {debug_info['method_tried']}</h3>
                <p><a href="/en/competitions/combat/combats/">Retour à la liste des combats</a></p>
            """)
            
    except Exception as e:
        import traceback
        return HttpResponse(f"""
            <h1>Erreur lors de l'accès au combat {combat_id}</h1>
            <h2>Exception: {type(e).__name__}: {e}</h2>
            <pre>{traceback.format_exc()}</pre>
        """)