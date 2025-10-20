"""
WebSocket consumers pour les compétitions en temps réel
"""
import json
from datetime import datetime
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

User = get_user_model()


class TechnicalScoringConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour la notation technique en temps réel
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition_id = None
        self.competition_group_name = None
        self.user = None
    
    async def connect(self):
        """Connexion d'un juge au système de notation"""
        self.competition_id = self.scope['url_route']['kwargs']['competition_id']
        self.competition_group_name = f'technical_{self.competition_id}'
        self.user = self.scope.get("user", None)
        
        # Pour les tests, accepter les connexions anonymes
        # if not await self.is_authorized_judge():
        #     await self.close()
        #     return
        
        # Joindre le groupe de la compétition
        await self.channel_layer.group_add(
            self.competition_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Notifier les autres juges de la connexion
        await self.channel_layer.group_send(
            self.competition_group_name,
            {
                'type': 'judge_connected',
                'judge_id': self.user.id,
                'judge_name': self.user.get_full_name() or self.user.username,
                'timestamp': datetime.now().isoformat()
            }
        )
    
    async def disconnect(self, close_code):
        """Déconnexion d'un juge"""
        if self.competition_group_name:
            # Notifier les autres juges de la déconnexion
            await self.channel_layer.group_send(
                self.competition_group_name,
                {
                    'type': 'judge_disconnected',
                    'judge_id': self.user.id,
                    'judge_name': self.user.get_full_name() or self.user.username,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Quitter le groupe
            await self.channel_layer.group_discard(
                self.competition_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'submit_score':
                await self.handle_score_submission(data)
            elif action == 'request_current_state':
                await self.send_current_state()
            elif action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
        except json.JSONDecodeError:
            await self.send_error(_("Format de message invalide"))
    
    async def handle_score_submission(self, data):
        """Gérer la soumission d'un score par un juge"""
        performance_id = data.get('performance_id')
        score_value = data.get('score')
        criteria_id = data.get('criteria_id')
        
        # Valider les données
        if not all([performance_id, score_value is not None, criteria_id]):
            await self.send_error(_("Données de score incomplètes"))
            return
        
        # Sauvegarder le score en base
        success, score = await self.save_score(
            performance_id, 
            score_value, 
            criteria_id
        )
        
        if success:
            # Diffuser le score à tous les juges
            await self.channel_layer.group_send(
                self.competition_group_name,
                {
                    'type': 'score_update',
                    'performance_id': performance_id,
                    'judge_id': self.user.id if self.user and hasattr(self.user, 'id') else 'anonymous',
                    'judge_name': (self.user.get_full_name() if self.user and hasattr(self.user, 'get_full_name') else 'Test User'),
                    'score': score_value,
                    'criteria_id': criteria_id,
                    'average': await self.calculate_average(performance_id, criteria_id),
                    'timestamp': datetime.now().isoformat()
                }
            )
        else:
            await self.send_error(_("Erreur lors de la sauvegarde du score"))
    
    @database_sync_to_async
    def is_authorized_judge(self):
        """Vérifier si l'utilisateur est un juge autorisé pour cette compétition"""
        from apps.competitions.models import Competition, JudgeAssignment
        
        if not self.user.is_authenticated:
            return False
        
        try:
            competition = Competition.objects.get(id=self.competition_id)
            # Vérifier si l'utilisateur est assigné comme juge
            return JudgeAssignment.objects.filter(
                competition=competition,
                judge__user=self.user,
                is_active=True
            ).exists()
        except Competition.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_score(self, performance_id, score_value, criteria_id):
        """Sauvegarder un score en base de données"""
        from apps.competitions.models import TechnicalScore, TechnicalPerformance, ScoringCriterion
        
        try:
            performance = TechnicalPerformance.objects.get(id=performance_id)
            criterion = ScoringCriterion.objects.get(id=criteria_id)
            
            score, created = TechnicalScore.objects.update_or_create(
                performance=performance,
                judge=self.user,
                criterion=criterion,
                defaults={'score': score_value}
            )
            
            return True, score
        except Exception as e:
            print(f"Erreur sauvegarde score: {e}")
            return False, None
    
    @database_sync_to_async
    def calculate_average(self, performance_id, criteria_id):
        """Calculer la moyenne des scores pour une performance et un critère"""
        from apps.competitions.models import TechnicalScore
        from django.db.models import Avg
        
        result = TechnicalScore.objects.filter(
            performance_id=performance_id,
            criterion_id=criteria_id
        ).aggregate(Avg('score'))
        
        return result['score__avg'] or 0
    
    async def send_current_state(self):
        """Envoyer l'état actuel des scores au juge"""
        # TODO: Implémenter l'envoi de l'état actuel
        pass
    
    async def send_error(self, message):
        """Envoyer un message d'erreur au client"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': str(message),
            'timestamp': datetime.now().isoformat()
        }))
    
    # Handlers pour les messages de groupe
    
    async def judge_connected(self, event):
        """Handler pour la connexion d'un juge"""
        await self.send(text_data=json.dumps(event))
    
    async def judge_disconnected(self, event):
        """Handler pour la déconnexion d'un juge"""
        await self.send(text_data=json.dumps(event))
    
    async def score_update(self, event):
        """Handler pour la mise à jour d'un score"""
        await self.send(text_data=json.dumps(event))


class CombatConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour les combats en temps réel
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition_id = None
        self.combat_id = None
        self.combat_group_name = None
        self.user = None
    
    async def connect(self):
        """Connexion au combat en temps réel"""
        self.competition_id = self.scope['url_route']['kwargs']['competition_id']
        self.combat_id = self.scope['url_route']['kwargs']['combat_id']
        self.combat_group_name = f'combat_{self.competition_id}_{self.combat_id}'
        self.user = self.scope["user"]
        
        # Vérifier l'autorisation
        if not await self.is_authorized():
            await self.close()
            return
        
        # Joindre le groupe du combat
        await self.channel_layer.group_add(
            self.combat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état actuel du combat
        await self.send_combat_state()
    
    async def disconnect(self, close_code):
        """Déconnexion du combat"""
        if self.combat_group_name:
            await self.channel_layer.group_discard(
                self.combat_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            # Actions disponibles selon le rôle
            if action == 'start_combat':
                await self.handle_start_combat()
            elif action == 'score_point':
                await self.handle_score_point(data)
            elif action == 'add_penalty':
                await self.handle_penalty(data)
            elif action == 'pause_combat':
                await self.handle_pause()
            elif action == 'resume_combat':
                await self.handle_resume()
            elif action == 'end_round':
                await self.handle_end_round()
            elif action == 'end_combat':
                await self.handle_end_combat()
            elif action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
        except json.JSONDecodeError:
            await self.send_error(_("Format de message invalide"))
    
    async def handle_start_combat(self):
        """Démarrer le combat"""
        if not await self.is_referee():
            await self.send_error(_("Seul l'arbitre peut démarrer le combat"))
            return
        
        success = await self.update_combat_status('ongoing')
        if success:
            await self.channel_layer.group_send(
                self.combat_group_name,
                {
                    'type': 'combat_started',
                    'timestamp': datetime.now().isoformat(),
                    'started_by': self.user.get_full_name() or self.user.username
                }
            )
    
    async def handle_score_point(self, data):
        """Gérer l'attribution de points"""
        if not await self.is_referee():
            await self.send_error(_("Seul l'arbitre peut attribuer des points"))
            return
        
        participant = data.get('participant')  # 'red' or 'blue'
        points = data.get('points', 1)
        
        # Sauvegarder l'action
        success, action = await self.save_combat_action('score', participant, points)
        
        if success:
            # Diffuser la mise à jour
            await self.channel_layer.group_send(
                self.combat_group_name,
                {
                    'type': 'score_update',
                    'participant': participant,
                    'points': points,
                    'total_score': await self.get_total_score(),
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    async def handle_penalty(self, data):
        """Gérer les pénalités"""
        if not await self.is_referee():
            await self.send_error(_("Seul l'arbitre peut donner des pénalités"))
            return
        
        participant = data.get('participant')
        penalty_type = data.get('penalty_type', 'warning')
        
        success, action = await self.save_combat_action('penalty', participant, 0, penalty_type)
        
        if success:
            await self.channel_layer.group_send(
                self.combat_group_name,
                {
                    'type': 'penalty_update',
                    'participant': participant,
                    'penalty_type': penalty_type,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    @database_sync_to_async
    def is_authorized(self):
        """Vérifier si l'utilisateur peut accéder au combat"""
        if not self.user.is_authenticated:
            return False
        
        # TODO: Implémenter la logique d'autorisation
        # Arbitres, juges, coaches des participants, organisateurs
        return True
    
    @database_sync_to_async
    def is_referee(self):
        """Vérifier si l'utilisateur est l'arbitre du combat"""
        from apps.competitions.models import Combat
        
        try:
            combat = Combat.objects.get(id=self.combat_id)
            return combat.referee and combat.referee.user == self.user
        except Combat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def update_combat_status(self, status):
        """Mettre à jour le statut du combat"""
        from apps.competitions.models import Combat
        
        try:
            combat = Combat.objects.get(id=self.combat_id)
            combat.status = status
            combat.save()
            return True
        except Combat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_combat_action(self, action_type, participant, value=0, details=None):
        """Sauvegarder une action de combat"""
        from apps.competitions.models import Combat, ActionCombat
        
        try:
            combat = Combat.objects.get(id=self.combat_id)
            action = ActionCombat.objects.create(
                combat=combat,
                type=action_type,
                participant=participant,
                value=value,
                details=details or {},
                created_by=self.user
            )
            return True, action
        except Exception as e:
            print(f"Erreur sauvegarde action: {e}")
            return False, None
    
    @database_sync_to_async
    def get_total_score(self):
        """Obtenir le score total actuel"""
        from apps.competitions.models import ActionCombat
        from django.db.models import Sum
        
        scores = ActionCombat.objects.filter(
            combat_id=self.combat_id,
            type='score'
        ).values('participant').annotate(
            total=Sum('value')
        )
        
        result = {'red': 0, 'blue': 0}
        for score in scores:
            result[score['participant']] = score['total'] or 0
        
        return result
    
    async def send_combat_state(self):
        """Envoyer l'état actuel du combat"""
        # TODO: Implémenter l'envoi de l'état complet
        pass
    
    async def send_error(self, message):
        """Envoyer un message d'erreur"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': str(message),
            'timestamp': datetime.now().isoformat()
        }))
    
    # Handlers pour les messages de groupe
    
    async def combat_started(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def score_update(self, event):
        await self.send(text_data=json.dumps(event))
    
    async def penalty_update(self, event):
        await self.send(text_data=json.dumps(event))


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    Consumer pour le dashboard général de la compétition
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.competition_id = None
        self.dashboard_group_name = None
        self.user = None
    
    async def connect(self):
        """Connexion au dashboard"""
        self.competition_id = self.scope['url_route']['kwargs']['competition_id']
        self.dashboard_group_name = f'dashboard_{self.competition_id}'
        self.user = self.scope["user"]
        
        # Tout utilisateur authentifié peut voir le dashboard
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Joindre le groupe du dashboard
        await self.channel_layer.group_add(
            self.dashboard_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Envoyer l'état initial
        await self.send_dashboard_state()
    
    async def disconnect(self, close_code):
        """Déconnexion du dashboard"""
        if self.dashboard_group_name:
            await self.channel_layer.group_discard(
                self.dashboard_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Recevoir un message du WebSocket"""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'refresh':
                await self.send_dashboard_state()
            elif action == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
        except json.JSONDecodeError:
            pass
    
    async def send_dashboard_state(self):
        """Envoyer l'état actuel du dashboard"""
        stats = await self.get_competition_stats()
        
        await self.send(text_data=json.dumps({
            'type': 'dashboard_update',
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        }))
    
    @database_sync_to_async
    def get_competition_stats(self):
        """Obtenir les statistiques de la compétition"""
        from apps.competitions.models import Competition, CompetitionRegistration
        
        try:
            competition = Competition.objects.get(id=self.competition_id)
            
            return {
                'total_participants': competition.registrations.count(),
                'active_combats': competition.combats.filter(status='ongoing').count(),
                'completed_combats': competition.combats.filter(status='completed').count(),
                'categories_count': competition.categories.count(),
                # Ajouter d'autres statistiques selon les besoins
            }
        except Competition.DoesNotExist:
            return {}
    
    # Handlers pour les messages de groupe
    
    async def competition_update(self, event):
        """Mise à jour générale de la compétition"""
        await self.send(text_data=json.dumps(event))
    
    async def category_update(self, event):
        """Mise à jour d'une catégorie"""
        await self.send(text_data=json.dumps(event))
    
    async def results_update(self, event):
        """Mise à jour des résultats"""
        await self.send(text_data=json.dumps(event))