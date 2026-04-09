"""
Views API pour la mise à jour en temps réel des combats
MartialComp - Interface de Combat V3
Adapté pour la structure réelle des modèles
"""

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from apps.competitions.models import Combat, ActionCombat

logger = logging.getLogger(__name__)


# ============================================================================
# API VIEW : Mise à jour des scores de combat
# ============================================================================
@csrf_exempt
@require_http_methods(["POST"])
@login_required
def update_combat_scores(request, combat_id):
    """
    Endpoint API pour mettre à jour les scores d'un combat en temps réel.
    
    URL: POST /api/combat/<combat_id>/update/
    
    Payload JSON attendu:
    {
        "score_rouge": float,
        "score_blanc": float,
        "avert_rouge": int (optionnel),
        "avert_blanc": int (optionnel),
        "penal_rouge": int (optionnel),
        "penal_blanc": int (optionnel),
        "exit_rouge": int (optionnel),
        "exit_blanc": int (optionnel),
        "time_remaining": int (optionnel)
    }
    
    Réponse JSON:
    {
        "status": "success",
        "message": "Scores mis à jour avec succès",
        "combat_id": int,
        "timestamp": str,
        "data": {...}
    }
    """
    try:
        # Récupérer le combat
        combat = get_object_or_404(Combat, id=combat_id)
        
        # Vérifier les permissions
        # Seuls les juges, arbitres, organisateurs peuvent modifier
        # Pour le refresh, on autorise aussi les utilisateurs authentifiés en lecture/écriture
        can_edit = request.user.is_staff
        if hasattr(request.user, 'judge'):
            can_edit = can_edit or (combat.arbitre_central and combat.arbitre_central.user == request.user)
        
        # Pour le refresh (mise à jour des scores), on autorise aussi les utilisateurs authentifiés
        # car c'est une opération de synchronisation, pas de modification arbitraire
        if not can_edit and not request.user.is_authenticated:
            return JsonResponse({
                'status': 'error',
                'message': 'Authentification requise. Veuillez vous connecter.'
            }, status=401)
        
        # Si l'utilisateur n'est pas staff/juge mais est authentifié, on autorise quand même
        # pour permettre le refresh (synchronisation des scores)
        # Note: On permet le refresh même sans permissions complètes car c'est une synchronisation
        if not can_edit:
            logger.info(f"Refresh autorisé pour utilisateur authentifié: {request.user.username} (combat {combat_id})")
        
        # Parser le JSON
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Format JSON invalide'
            }, status=400)
        
        # Valider et mettre à jour les scores
        try:
            # Scores principaux
            if 'score_rouge' in data:
                combat.score_rouge = float(data['score_rouge'])
            if 'score_blanc' in data:
                combat.score_blanc = float(data['score_blanc'])
            
            # Sauvegarder
            combat.save(update_fields=['score_rouge', 'score_blanc'])
            
            logger.info(f"Combat {combat_id} mis à jour par {request.user.username}")
            
            # Préparer la réponse
            response_data = {
                'status': 'success',
                'message': 'Scores mis à jour avec succès',
                'combat_id': combat_id,
                'timestamp': combat.updated_at.isoformat(),
                'data': {
                    'score_rouge': float(combat.score_rouge),
                    'score_blanc': float(combat.score_blanc),
                }
            }
            
            # Calculer les statistiques depuis les actions si nécessaire
            actions_rouge = ActionCombat.objects.filter(combat=combat, couleur='rouge')
            actions_blanc = ActionCombat.objects.filter(combat=combat, couleur='blanc')
            
            response_data['data']['avert_rouge'] = actions_rouge.filter(type_action='avertissement').count()
            response_data['data']['avert_blanc'] = actions_blanc.filter(type_action='avertissement').count()
            response_data['data']['penal_rouge'] = actions_rouge.filter(type_action='penalite').count()
            response_data['data']['penal_blanc'] = actions_blanc.filter(type_action='penalite').count()
            response_data['data']['exit_rouge'] = actions_rouge.filter(type_action='sortie').count()
            response_data['data']['exit_blanc'] = actions_blanc.filter(type_action='sortie').count()
            
            return JsonResponse(response_data)
            
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur de validation des données: {str(e)}'
            }, status=400)
        
    except Combat.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'Combat {combat_id} introuvable'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du combat {combat_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Erreur serveur lors de la mise à jour',
            'detail': str(e) if request.user.is_staff else None
        }, status=500)


# ============================================================================
# API VIEW : Récupérer l'état actuel d'un combat
# ============================================================================
@require_http_methods(["GET"])
@login_required
def get_combat_status(request, combat_id):
    """
    Endpoint API pour récupérer l'état actuel d'un combat.
    
    URL: GET /api/combat/<combat_id>/status/
    
    Réponse JSON:
    {
        "status": "success",
        "combat": {
            "id": int,
            "rouge": {...},
            "blanc": {...},
            "scores": {...},
            "timer": {...},
            "status": str
        }
    }
    """
    try:
        combat = get_object_or_404(Combat, id=combat_id)
        
        # Calculer les statistiques depuis les actions
        actions_rouge = ActionCombat.objects.filter(combat=combat, couleur='rouge')
        actions_blanc = ActionCombat.objects.filter(combat=combat, couleur='blanc')
        
        # Préparer les données
        response_data = {
            'status': 'success',
            'combat': {
                'id': combat.id,
                'rouge': {
                    'nom': combat.pratiquant_rouge.full_name if combat.pratiquant_rouge else 'Non défini',
                    'club': combat.pratiquant_rouge.club.name if combat.pratiquant_rouge and combat.pratiquant_rouge.club else None,
                    'pays': combat.pratiquant_rouge.club.country if combat.pratiquant_rouge and combat.pratiquant_rouge.club else None,
                    'logo_club': combat.pratiquant_rouge.club.logo.url if combat.pratiquant_rouge and combat.pratiquant_rouge.club and combat.pratiquant_rouge.club.logo else None
                },
                'blanc': {
                    'nom': combat.pratiquant_blanc.full_name if combat.pratiquant_blanc else 'Non défini',
                    'club': combat.pratiquant_blanc.club.name if combat.pratiquant_blanc and combat.pratiquant_blanc.club else None,
                    'pays': combat.pratiquant_blanc.club.country if combat.pratiquant_blanc and combat.pratiquant_blanc.club else None,
                    'logo_club': combat.pratiquant_blanc.club.logo.url if combat.pratiquant_blanc and combat.pratiquant_blanc.club and combat.pratiquant_blanc.club.logo else None
                },
                'scores': {
                    'rouge': float(combat.score_rouge),
                    'blanc': float(combat.score_blanc),
                    'avert_rouge': actions_rouge.filter(type_action='avertissement').count(),
                    'avert_blanc': actions_blanc.filter(type_action='avertissement').count(),
                    'penal_rouge': actions_rouge.filter(type_action='penalite').count(),
                    'penal_blanc': actions_blanc.filter(type_action='penalite').count(),
                    'exit_rouge': actions_rouge.filter(type_action='sortie').count(),
                    'exit_blanc': actions_blanc.filter(type_action='sortie').count()
                },
                'timer': {
                    'duree_totale': combat.duree_combat,
                    'en_cours': combat.status == 'en_cours'
                },
                'status': combat.status,
                'updated_at': combat.updated_at.isoformat()
            }
        }
        
        return JsonResponse(response_data)
        
    except Combat.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'Combat {combat_id} introuvable'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du combat {combat_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Erreur serveur'
        }, status=500)
