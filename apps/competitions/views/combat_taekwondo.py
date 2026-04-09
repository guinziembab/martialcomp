from django.core.exceptions import PermissionDenied
"""
Vues spécialisées pour la gestion des combats de Taekwondo.
Ce module fournit une interface adaptée aux règles spécifiques du Taekwondo,
avec un système de notation et de pénalités conforme aux standards WTF.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json
import logging

# Importation de notre helper de permission personnalisé
from apps.competitions.utils.permission_helpers import manual_check_competition_permission

from apps.competitions.models.combat import (
    CombatConfiguration, 
    Poule, 
    Combat, 
    ActionCombat
)

# Logger pour déboguer
logger = logging.getLogger(__name__)

# Constantes spécifiques au Taekwondo
TAEKWONDO_POINT_VALUES = {
    'punch_body': 1,     # Poing au tronc
    'kick_body': 2,      # Coup de pied au tronc
    'kick_head': 3,      # Coup de pied Ã  la tÃªte
    'turning_kick_body': 4,  # Coup de pied retourné au tronc
    'turning_kick_head': 5,  # Coup de pied retourné Ã  la tÃªte
}

TAEKWONDO_PENALTIES = {
    'kyong_go': -0.5,    # Kyong-go (avertissement)
    'gam_jeom': -1,      # Gam-jeom (déduction de point)
}

@login_required
def liste_combats_taekwondo(request, competition_id=None):
    """
    Affiche la liste des combats de Taekwondo, filtrés par compétition si spécifié.
    """
    from apps.competitions.models import Competition
    
    context = {
        'title': _("Combats de Taekwondo")
    }
    
    if competition_id:
        competition = get_object_or_404(Competition, id=competition_id)
        # Filtrer les combats avec configuration de Taekwondo
        combats = Combat.objects.filter(
            competition=competition,
            configuration__system='taekwondo'
        ).order_by('-date_planifiee')
        
        context['competition'] = competition
    else:
        # Tous les combats de Taekwondo
        combats = Combat.objects.filter(
            configuration__system='taekwondo'
        ).order_by('-date_planifiee')
    
    context['combats'] = combats
    return render(request, 'competitions/combat_taekwondo/liste_combats.html', context)

@login_required
def detail_combat_taekwondo(request, combat_id):
    """
    Affiche les détails d'un combat de Taekwondo, y compris les actions et les scores.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    
    # Vérifier que c'est bien un combat de Taekwondo
    if not combat.configuration or combat.configuration.system != 'taekwondo':
        messages.warning(request, _("Ce combat n'utilise pas les règles du Taekwondo."))
        return redirect('competitions:combat:detail_combat', combat_id=combat.id)
    
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')
    
    # Regrouper les pénalités par couleur et type
    kyong_go_rouge = actions.filter(couleur='rouge', type_action='avertissement', description='kyong_go').count()
    kyong_go_blanc = actions.filter(couleur='blanc', type_action='avertissement', description='kyong_go').count()
    gam_jeom_rouge = actions.filter(couleur='rouge', type_action='penalite', description='gam_jeom').count()
    gam_jeom_blanc = actions.filter(couleur='blanc', type_action='penalite', description='gam_jeom').count()
    
    context = {
        'combat': combat,
        'actions': actions,
        'kyong_go_rouge': kyong_go_rouge,
        'kyong_go_blanc': kyong_go_blanc,
        'gam_jeom_rouge': gam_jeom_rouge,
        'gam_jeom_blanc': gam_jeom_blanc,
        'can_start': combat.status == 'planifie',
        'can_end': combat.status == 'en_cours',
    }
    
    return render(request, 'competitions/combat_taekwondo/detail_combat.html', context)

@login_required
def interface_combat_taekwondo(request, combat_id):
    """
    Interface spécialisée pour l'arbitrage de combats de Taekwondo.
    """
    combat = get_object_or_404(Combat, id=combat_id)
    
    # Vérifier que c'est bien un combat de Taekwondo
    if not combat.configuration or combat.configuration.system != 'taekwondo':
        messages.warning(request, _("Ce combat n'utilise pas les règles du Taekwondo."))
        return redirect('competitions:combat:interface_combat', combat_id=combat.id)
    
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')
    
    # Regrouper les pénalités par couleur et type
    kyong_go_rouge = actions.filter(couleur='rouge', type_action='avertissement', description='kyong_go').count()
    kyong_go_blanc = actions.filter(couleur='blanc', type_action='avertissement', description='kyong_go').count()
    gam_jeom_rouge = actions.filter(couleur='rouge', type_action='penalite', description='gam_jeom').count()
    gam_jeom_blanc = actions.filter(couleur='blanc', type_action='penalite', description='gam_jeom').count()
    
    # Déterminer si un concurrent doit Ãªtre disqualifié (10 Kyong-go ou 5 Gam-jeom)
    disqualify_rouge = kyong_go_rouge >= 10 or gam_jeom_rouge >= 5
    disqualify_blanc = kyong_go_blanc >= 10 or gam_jeom_blanc >= 5
    
    # Vérifier si l'écart de points est suffisant pour une victoire automatique (20+ points)
    point_gap_victory = abs(float(combat.score_rouge) - float(combat.score_blanc)) >= 20
    
    context = {
        'combat': combat,
        'actions': actions,
        'kyong_go_rouge': kyong_go_rouge,
        'kyong_go_blanc': kyong_go_blanc,
        'gam_jeom_rouge': gam_jeom_rouge,
        'gam_jeom_blanc': gam_jeom_blanc,
        'disqualify_rouge': disqualify_rouge,
        'disqualify_blanc': disqualify_blanc,
        'point_gap_victory': point_gap_victory,
        'point_values': TAEKWONDO_POINT_VALUES,
        'penalty_values': TAEKWONDO_PENALTIES,
        'is_judge': hasattr(request.user, 'judge'),
    }
    
    return render(request, 'competitions/combat_taekwondo/interface_combat.html', context)

@login_required
@csrf_exempt
def ajouter_action_taekwondo(request, combat_id):
    """
    API pour ajouter une action Ã  un combat de Taekwondo.
    Supporte les types de points et pénalités spécifiques au Taekwondo.
    """
    # Vérifier manuellement les permissions
    if not manual_check_competition_permission(request.user, 'competitions.add_actioncombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.status != 'en_cours':
        return JsonResponse({
            'success': False, 
            'error': _("Combat non actif")
        }, status=400)
    
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                type_action = data.get('type_action')
                couleur = data.get('couleur')
                description = data.get('description', '')
                
                # Déterminer la valeur en fonction du type d'action
                if type_action == 'point':
                    technique = data.get('technique', '')
                    if technique in TAEKWONDO_POINT_VALUES:
                        valeur = TAEKWONDO_POINT_VALUES[technique]
                    else:
                        return JsonResponse({
                            'success': False, 
                            'error': _("Technique non reconnue")
                        }, status=400)
                elif type_action == 'penalite' or type_action == 'avertissement':
                    penalty_type = data.get('penalty_type', '')
                    if penalty_type in TAEKWONDO_PENALTIES:
                        valeur = TAEKWONDO_PENALTIES[penalty_type]
                        description = penalty_type  # Stocker le type de pénalité
                    else:
                        return JsonResponse({
                            'success': False, 
                            'error': _("Type de pénalité non reconnu")
                        }, status=400)
                else:
                    valeur = 0
                
                # Créer l'action
                action = ActionCombat(
                    combat=combat,
                    type_action=type_action,
                    couleur=couleur,
                    valeur=valeur,
                    description=description
                )
                
                # Ajouter l'arbitre si possible
                if hasattr(request.user, 'judge'):
                    action.arbitre = request.user.judge
                
                action.save()
                
                # Mettre Ã  jour et rafraÃ®chir le combat
                combat.refresh_from_db()
                
                # Vérifier les conditions de fin de combat (20+ points d'écart)
                point_gap_victory = abs(float(combat.score_rouge) - float(combat.score_blanc)) >= 20
                
                # Compter les pénalités pour vérifier les disqualifications
                kyong_go_rouge = ActionCombat.objects.filter(
                    combat=combat, 
                    couleur='rouge', 
                    type_action='avertissement', 
                    description='kyong_go'
                ).count()
                
                kyong_go_blanc = ActionCombat.objects.filter(
                    combat=combat, 
                    couleur='blanc', 
                    type_action='avertissement', 
                    description='kyong_go'
                ).count()
                
                disqualify_rouge = kyong_go_rouge >= 10
                disqualify_blanc = kyong_go_blanc >= 10
                
                # Préparer la réponse
                response_data = {
                    'success': True, 
                    'action_id': action.id,
                    'score_rouge': float(combat.score_rouge),
                    'score_blanc': float(combat.score_blanc),
                    'point_gap_victory': point_gap_victory,
                    'kyong_go_rouge': kyong_go_rouge,
                    'kyong_go_blanc': kyong_go_blanc,
                    'disqualify_rouge': disqualify_rouge,
                    'disqualify_blanc': disqualify_blanc
                }
                
                return JsonResponse(response_data)
                
            except json.JSONDecodeError:
                return JsonResponse({
                    'success': False, 
                    'error': _("Format JSON invalide")
                }, status=400)
        else:
            messages.error(request, _("RequÃªte non AJAX non supportée pour cette action"))
            return redirect('competitions:combat_taekwondo:detail_combat', combat_id=combat.id)
    
    return JsonResponse({
        'success': False, 
        'error': _("Méthode non autorisée")
    }, status=405)

@login_required
def annuler_action_taekwondo(request, action_id):
    """
    Permet d'annuler une action de combat de Taekwondo.
    """
    # Vérifier manuellement les permissions
    if not manual_check_competition_permission(request.user, 'competitions.delete_actioncombat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    action = get_object_or_404(ActionCombat, id=action_id)
    combat = action.combat
    
    if combat.status != 'en_cours':
        messages.error(request, _("Impossible d'annuler une action d'un combat qui n'est pas en cours."))
        return redirect('competitions:combat_taekwondo:detail_combat', combat_id=combat.id)
    
    # Inverser l'effet de l'action sur le score
    if action.type_action in ['point', 'penalite']:
        if action.couleur == 'rouge':
            combat.score_rouge -= action.valeur
        elif action.couleur == 'blanc':
            combat.score_blanc -= action.valeur
        
        combat.save()
    
    # Supprimer l'action
    action.delete()
    
    messages.success(request, _("L'action a été annulée."))
    return redirect('competitions:combat_taekwondo:interface_combat', combat_id=combat.id)

@login_required
def demarrer_combat_taekwondo(request, combat_id):
    """
    Permet de démarrer un combat de Taekwondo planifié.
    """
    # Vérifier manuellement les permissions
    if not manual_check_competition_permission(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.start_combat():
        messages.success(request, _("Le combat a été démarré."))
    else:
        messages.error(request, _("Impossible de démarrer ce combat."))
    
    return redirect('competitions:combat_taekwondo:interface_combat', combat_id=combat.id)

@login_required
def terminer_combat_taekwondo(request, combat_id):
    """
    Permet de terminer un combat de Taekwondo en cours.
    """
    # Vérifier manuellement les permissions
    if not manual_check_competition_permission(request.user, 'competitions.change_combat'):
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour cette action."))
        return redirect('competitions:dashboard:index')
    combat = get_object_or_404(Combat, id=combat_id)
    
    if combat.end_combat():
        # Message de victoire avec le type approprié
        if combat.score_rouge > combat.score_blanc:
            if abs(float(combat.score_rouge) - float(combat.score_blanc)) >= 20:
                messages.success(request, _("Combat terminé. Victoire par écart de points du combattant rouge."))
            else:
                messages.success(request, _("Combat terminé. Victoire du combattant rouge."))
        elif combat.score_blanc > combat.score_rouge:
            if abs(float(combat.score_blanc) - float(combat.score_rouge)) >= 20:
                messages.success(request, _("Combat terminé. Victoire par écart de points du combattant blanc."))
            else:
                messages.success(request, _("Combat terminé. Victoire du combattant blanc."))
        else:
            messages.success(request, _("Combat terminé. Match nul."))
    else:
        messages.error(request, _("Impossible de terminer ce combat."))
    
    return redirect('competitions:combat_taekwondo:detail_combat', combat_id=combat.id)

@login_required
def api_statut_combat_taekwondo(request, combat_id):
    """
    API JSON retournant le statut actuel d'un combat de Taekwondo.
    Inclut les informations spécifiques au Taekwondo (pénalités, rounds).
    """
    combat = get_object_or_404(Combat, id=combat_id)
    actions = ActionCombat.objects.filter(combat=combat).order_by('-temps')[:10]
    
    # Calculer le temps écoulé si le combat est en cours
    elapsed_time = None
    if combat.status == 'en_cours' and combat.debut_combat:
        elapsed_seconds = (timezone.now() - combat.debut_combat).total_seconds()
        elapsed_time = min(elapsed_seconds, combat.duree_combat)
    
    # Compter les pénalités
    kyong_go_rouge = ActionCombat.objects.filter(
        combat=combat, couleur='rouge', type_action='avertissement', description='kyong_go'
    ).count()
    kyong_go_blanc = ActionCombat.objects.filter(
        combat=combat, couleur='blanc', type_action='avertissement', description='kyong_go'
    ).count()
    gam_jeom_rouge = ActionCombat.objects.filter(
        combat=combat, couleur='rouge', type_action='penalite', description='gam_jeom'
    ).count()
    gam_jeom_blanc = ActionCombat.objects.filter(
        combat=combat, couleur='blanc', type_action='penalite', description='gam_jeom'
    ).count()
    
    data = {
        'id': combat.id,
        'uuid': str(combat.uuid),
        'status': combat.status,
        'score_rouge': float(combat.score_rouge),
        'score_blanc': float(combat.score_blanc),
        'debut_combat': combat.debut_combat.isoformat() if combat.debut_combat else None,
        'fin_combat': combat.fin_combat.isoformat() if combat.fin_combat else None,
        'elapsed_time': int(elapsed_time) if elapsed_time is not None else None,
        'total_time': combat.duree_combat,
        'vainqueur': combat.vainqueur,
        'est_nul': combat.est_nul,
        'kyong_go_rouge': kyong_go_rouge,
        'kyong_go_blanc': kyong_go_blanc,
        'gam_jeom_rouge': gam_jeom_rouge,
        'gam_jeom_blanc': gam_jeom_blanc,
        'disqualify_rouge': kyong_go_rouge >= 10 or gam_jeom_rouge >= 5,
        'disqualify_blanc': kyong_go_blanc >= 10 or gam_jeom_blanc >= 5,
        'point_gap_victory': abs(float(combat.score_rouge) - float(combat.score_blanc)) >= 20,
        'actions': []
    }
    
    # Informations des participants
    if combat.type_combat == 'individuel':
        data['rouge'] = {
            'id': combat.pratiquant_rouge.id,
            'nom': combat.pratiquant_rouge.full_name
        } if combat.pratiquant_rouge else None
        
        data['blanc'] = {
            'id': combat.pratiquant_blanc.id,
            'nom': combat.pratiquant_blanc.full_name
        } if combat.pratiquant_blanc else None
    else:
        data['rouge'] = {
            'id': combat.equipe_rouge.id,
            'nom': combat.equipe_rouge.nom
        } if combat.equipe_rouge else None
        
        data['blanc'] = {
            'id': combat.equipe_blanc.id,
            'nom': combat.equipe_blanc.nom
        } if combat.equipe_blanc else None
    
    # Liste des actions récentes
    for action in actions:
        action_data = {
            'id': action.id,
            'action_type': action.type_action,
            'team': 'red' if action.couleur == 'rouge' else 'blue' if action.couleur == 'blanc' else 'neutral',
            'points': float(action.valeur),
            'description': action.description,
            'timestamp': action.temps.isoformat(),
            'judge': action.arbitre.user.get_full_name() if action.arbitre else None,
        }
        data['actions'].append(action_data)
    
    return JsonResponse(data)

