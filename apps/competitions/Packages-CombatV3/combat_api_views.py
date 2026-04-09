"""
Views API pour la mise à jour en temps réel des combats
MartialComp - Interface de Combat V3
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

from apps.competitions.models import Combat

logger = logging.getLogger(__name__)


# ============================================================================
# API VIEW : Mise à jour des scores de combat
# ============================================================================
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
        "avert_rouge": int,
        "avert_blanc": int,
        "penal_rouge": int,
        "penal_blanc": int,
        "exit_rouge": int,
        "exit_blanc": int,
        "time_remaining": int
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
        if not (request.user.is_staff or 
                request.user in combat.juges.all() or
                request.user == combat.arbitre or
                request.user == combat.competition.organisateur):
            return JsonResponse({
                'status': 'error',
                'message': 'Permission refusée. Vous n\'êtes pas autorisé à modifier ce combat.'
            }, status=403)
        
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
            
            # Avertissements
            if 'avert_rouge' in data:
                combat.avertissements_rouge = int(data['avert_rouge'])
            if 'avert_blanc' in data:
                combat.avertissements_blanc = int(data['avert_blanc'])
            
            # Pénalités
            if 'penal_rouge' in data:
                combat.penalites_rouge = int(data['penal_rouge'])
            if 'penal_blanc' in data:
                combat.penalites_blanc = int(data['penal_blanc'])
            
            # Sorties de tatami
            if 'exit_rouge' in data:
                combat.sorties_rouge = int(data['exit_rouge'])
            if 'exit_blanc' in data:
                combat.sorties_blanc = int(data['exit_blanc'])
            
            # Temps restant
            if 'time_remaining' in data:
                combat.temps_restant = int(data['time_remaining'])
            
            # Sauvegarder
            combat.save()
            
            logger.info(f"Combat {combat_id} mis à jour par {request.user.username}")
            
            # Préparer la réponse
            response_data = {
                'status': 'success',
                'message': 'Scores mis à jour avec succès',
                'combat_id': combat_id,
                'timestamp': combat.updated_at.isoformat(),
                'data': {
                    'score_rouge': combat.score_rouge,
                    'score_blanc': combat.score_blanc,
                    'avert_rouge': combat.avertissements_rouge,
                    'avert_blanc': combat.avertissements_blanc,
                    'penal_rouge': combat.penalites_rouge,
                    'penal_blanc': combat.penalites_blanc,
                    'exit_rouge': combat.sorties_rouge,
                    'exit_blanc': combat.sorties_blanc,
                    'time_remaining': combat.temps_restant,
                    'vainqueur': combat.get_vainqueur()
                }
            }
            
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
        
        # Préparer les données
        response_data = {
            'status': 'success',
            'combat': {
                'id': combat.id,
                'rouge': {
                    'nom': combat.combattant_rouge.nom_complet,
                    'club': combat.combattant_rouge.club.nom,
                    'pays': combat.combattant_rouge.pays.code if combat.combattant_rouge.pays else None,
                    'logo_club': combat.combattant_rouge.club.logo.url if combat.combattant_rouge.club.logo else None
                },
                'blanc': {
                    'nom': combat.combattant_blanc.nom_complet,
                    'club': combat.combattant_blanc.club.nom,
                    'pays': combat.combattant_blanc.pays.code if combat.combattant_blanc.pays else None,
                    'logo_club': combat.combattant_blanc.club.logo.url if combat.combattant_blanc.club.logo else None
                },
                'scores': {
                    'rouge': combat.score_rouge,
                    'blanc': combat.score_blanc,
                    'avert_rouge': combat.avertissements_rouge,
                    'avert_blanc': combat.avertissements_blanc,
                    'penal_rouge': combat.penalites_rouge,
                    'penal_blanc': combat.penalites_blanc,
                    'exit_rouge': combat.sorties_rouge,
                    'exit_blanc': combat.sorties_blanc
                },
                'timer': {
                    'duree_totale': combat.duree_combat,
                    'temps_restant': combat.temps_restant,
                    'en_cours': combat.est_en_cours
                },
                'status': combat.statut,
                'vainqueur': combat.get_vainqueur(),
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


# ============================================================================
# API VIEW : Historique des actions d'un combat
# ============================================================================
@require_http_methods(["GET"])
@login_required
def get_combat_history(request, combat_id):
    """
    Endpoint API pour récupérer l'historique des actions d'un combat.
    
    URL: GET /api/combat/<combat_id>/history/
    
    Query params:
    - limit: int (défaut: 20) - Nombre d'actions à retourner
    
    Réponse JSON:
    {
        "status": "success",
        "actions": [
            {
                "timestamp": str,
                "time_remaining": int,
                "fighter": "rouge|blanc",
                "action": str,
                "points": float,
                "description": str
            }
        ]
    }
    """
    try:
        combat = get_object_or_404(Combat, id=combat_id)
        limit = int(request.GET.get('limit', 20))
        
        # Récupérer les actions depuis la base de données
        # (Vous devrez adapter selon votre modèle ActionCombat)
        from apps.competitions.models import ActionCombat
        
        actions = ActionCombat.objects.filter(combat=combat).order_by('-created_at')[:limit]
        
        actions_data = [
            {
                'timestamp': action.created_at.isoformat(),
                'time_remaining': action.temps_restant,
                'fighter': action.combattant,  # 'rouge' ou 'blanc'
                'action': action.type_action,
                'points': action.points,
                'description': action.description
            }
            for action in actions
        ]
        
        return JsonResponse({
            'status': 'success',
            'combat_id': combat_id,
            'total_actions': len(actions_data),
            'actions': actions_data
        })
        
    except Combat.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'Combat {combat_id} introuvable'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique du combat {combat_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Erreur serveur'
        }, status=500)


# ============================================================================
# API VIEW : Terminer un combat
# ============================================================================
@require_http_methods(["POST"])
@login_required
def end_combat(request, combat_id):
    """
    Endpoint API pour terminer un combat et calculer le vainqueur.
    
    URL: POST /api/combat/<combat_id>/end/
    
    Réponse JSON:
    {
        "status": "success",
        "combat_id": int,
        "vainqueur": str,
        "score_final": {
            "rouge": float,
            "blanc": float
        }
    }
    """
    try:
        combat = get_object_or_404(Combat, id=combat_id)
        
        # Vérifier les permissions
        if not (request.user.is_staff or 
                request.user == combat.arbitre or
                request.user == combat.competition.organisateur):
            return JsonResponse({
                'status': 'error',
                'message': 'Permission refusée'
            }, status=403)
        
        # Marquer le combat comme terminé
        combat.statut = 'termine'
        combat.est_en_cours = False
        combat.temps_restant = 0
        
        # Calculer le vainqueur
        vainqueur = combat.determiner_vainqueur()
        combat.vainqueur = vainqueur
        
        combat.save()
        
        logger.info(f"Combat {combat_id} terminé. Vainqueur: {vainqueur}")
        
        return JsonResponse({
            'status': 'success',
            'combat_id': combat_id,
            'vainqueur': vainqueur,
            'score_final': {
                'rouge': combat.score_rouge,
                'blanc': combat.score_blanc
            },
            'timestamp': combat.updated_at.isoformat()
        })
        
    except Combat.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': f'Combat {combat_id} introuvable'
        }, status=404)
    
    except Exception as e:
        logger.error(f"Erreur lors de la finalisation du combat {combat_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Erreur serveur'
        }, status=500)


# ============================================================================
# API VIEW : Websocket pour les mises à jour en temps réel
# ============================================================================
# Note: Pour une véritable solution temps réel, utilisez Django Channels
# Cet exemple utilise du polling HTTP simple via AJAX

class CombatRealtimeView(View):
    """
    Vue pour gérer les connexions temps réel (polling).
    Pour une vraie solution WebSocket, migrer vers Django Channels.
    """
    
    @method_decorator(login_required)
    def get(self, request, combat_id):
        """
        Retourne l'état actuel du combat pour le polling.
        """
        return get_combat_status(request, combat_id)
    
    @method_decorator(login_required)
    def post(self, request, combat_id):
        """
        Met à jour le combat via POST.
        """
        return update_combat_scores(request, combat_id)


# ============================================================================
# MIDDLEWARE : Logger toutes les requêtes API
# ============================================================================
class APILoggingMiddleware:
    """
    Middleware pour logger toutes les requêtes API de combat.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log avant la requête
        if request.path.startswith('/api/combat/'):
            logger.info(f"API Request: {request.method} {request.path} by {request.user}")
        
        response = self.get_response(request)
        
        # Log après la requête
        if request.path.startswith('/api/combat/'):
            logger.info(f"API Response: {response.status_code}")
        
        return response


# ============================================================================
# UTILITAIRES
# ============================================================================
def validate_combat_permissions(user, combat):
    """
    Vérifie si l'utilisateur a les permissions pour modifier un combat.
    
    Args:
        user: User object
        combat: Combat object
    
    Returns:
        bool: True si autorisé, False sinon
    """
    return (
        user.is_staff or
        user in combat.juges.all() or
        user == combat.arbitre or
        user == combat.competition.organisateur
    )


def calculate_combat_statistics(combat):
    """
    Calcule les statistiques détaillées d'un combat.
    
    Args:
        combat: Combat object
    
    Returns:
        dict: Statistiques du combat
    """
    total_points = combat.score_rouge + combat.score_blanc
    
    return {
        'total_points': total_points,
        'avg_points_per_minute': total_points / (combat.duree_combat / 60) if combat.duree_combat > 0 else 0,
        'total_penalties': combat.penalites_rouge + combat.penalites_blanc,
        'total_warnings': combat.avertissements_rouge + combat.avertissements_blanc,
        'total_exits': combat.sorties_rouge + combat.sorties_blanc,
        'score_difference': abs(combat.score_rouge - combat.score_blanc),
        'combat_intensity': 'high' if total_points > 10 else 'medium' if total_points > 5 else 'low'
    }
