from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
import uuid


class CombatPool(models.Model):
    """
    Représente un groupe ou une poule de combats dans une compétition.
    Chaque poule regroupe plusieurs combats/participants selon les règles du tirage.
    """
    TYPE_CHOICES = [
        ('pool', _('Poule')),
        ('elimination', _('Élimination directe')),
        ('semi_final', _('Demi-finale')),
        ('final', _('Finale')),
        ('third_place', _('Combat pour la 3e place')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom de la poule'))
    
    # Relation avec la compétition
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, 
                                   related_name='combat_pools', verbose_name=_('Compétition'))
    
    # Type et position dans le tournoi
    pool_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='pool', verbose_name=_('Type de poule'))
    round_number = models.PositiveIntegerField(default=1, verbose_name=_('Numéro de tour dans la compétition'))
    sequence_number = models.PositiveIntegerField(default=1, verbose_name=_('Numéro de séquence dans le tour'))
    
    # Pour les compétitions par équipe
    is_team_based = models.BooleanField(default=False, verbose_name=_('Basé sur des équipes'))
    
    # Paramètres avancés
    advancement_count = models.PositiveIntegerField(default=1, 
                                                  verbose_name=_('Nombre de participants qualifiés pour le tour suivant'))
    
    # Métadonnées 
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    start_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Heure de début'))
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Heure de fin'))
    
    class Meta:
        verbose_name = _('Poule de combat')
        verbose_name_plural = _('Poules de combat')
        ordering = ['competition', 'round_number', 'sequence_number']
        indexes = [
            models.Index(fields=['competition', 'round_number']),
            models.Index(fields=['pool_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_pool_type_display()}) - {self.competition}"
    
    def get_participants(self):
        """Retourne tous les participants uniques dans cette poule"""
        participants_red = self.combats.values_list(
            'red_participant_content_type', 'red_participant_id').distinct()
        participants_white = self.combats.values_list(
            'white_participant_content_type', 'white_participant_id').distinct()
        
        # Combiner les deux listes et supprimer les doublons
        all_participants = list(participants_red) + list(participants_white)
        # Filtrer les valeurs None
        all_participants = [p for p in all_participants if p[0] is not None and p[1] is not None]
        # Supprimer les doublons
        return list(set(all_participants))
    
    def get_teams(self):
        """Retourne toutes les équipes uniques dans cette poule"""
        teams_red = self.combats.values_list('red_team', flat=True).distinct()
        teams_white = self.combats.values_list('white_team', flat=True).distinct()
        
        # Combiner les deux listes et supprimer les doublons
        all_teams = list(teams_red) + list(teams_white)
        # Filtrer les valeurs None
        all_teams = [t for t in all_teams if t is not None]
        # Supprimer les doublons
        return list(set(all_teams))
    
    def get_standings(self):
        """
        Calcule le classement des participants/équipes dans cette poule
        basé sur les victoires/défaites et les scores.
        """
        # Logique à implémenter en fonction des règles spécifiques
        # de la compétition (points, différentiel, etc.)
        pass
    

class CombatTeam(models.Model):
    """
    Représente une équipe dans une compétition de combat par équipe.
    """
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name=_('Nom de l\'équipe'))
    
    # Relation avec la compétition et organisation
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, 
                                   related_name='combat_teams', verbose_name=_('Compétition'))
    
    # Le club, l'école ou la fédération associé(e)
    organization_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, 
                                                 related_name='combat_teams',
                                                 verbose_name=_('Type d\'organisation'))
    organization_id = models.CharField(max_length=50, verbose_name=_('ID de l\'organisation'))
    organization = GenericForeignKey('organization_content_type', 'organization_id')
    
    # Options d'affichage
    logo = models.ImageField(upload_to='combat_teams/logos/', null=True, blank=True, verbose_name=_('Logo'))
    color = models.CharField(max_length=20, blank=True, verbose_name=_('Couleur')) 
    country_code = models.CharField(max_length=3, blank=True, verbose_name=_('Code pays'))
    
    # Membre de l'équipe désigné comme capitaine
    captain_content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, 
                                           related_name='team_captain',
                                           null=True, blank=True,
                                           verbose_name=_('Type du capitaine'))
    captain_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID du capitaine'))
    captain = GenericForeignKey('captain_content_type', 'captain_id')
    
    # Taille et membres
    max_members = models.PositiveIntegerField(default=5, verbose_name=_('Nombre maximum de membres'))
    
    # Métadonnées 
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Équipe de combat')
        verbose_name_plural = _('Équipes de combat')
        ordering = ['competition', 'name']
        indexes = [
            models.Index(fields=['competition']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.competition})"
    
    @property
    def members_count(self):
        """Retourne le nombre total de membres dans l'équipe"""
        return self.members.count()
    
    def get_members(self):
        """Retourne tous les membres de l'équipe"""
        return self.members.all()
    
    def add_member(self, content_type, object_id):
        """Ajoute un membre à l'équipe"""
        if self.members_count < self.max_members:
            # Créer un nouveau CombatTeamMember
            CombatTeamMember.objects.create(
                team=self,
                member_content_type=content_type,
                member_id=object_id
            )
            return True
        return False  # Équipe déjà complète
    
    def remove_member(self, content_type, object_id):
        """Retire un membre de l'équipe"""
        try:
            member = CombatTeamMember.objects.get(
                team=self,
                member_content_type=content_type,
                member_id=object_id
            )
            member.delete()
            return True
        except CombatTeamMember.DoesNotExist:
            return False


class CombatTeamMember(models.Model):
    """
    Représente un membre d'une équipe de combat.
    Utilise GenericForeignKey pour supporter différents types de participants.
    """
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relation avec l'équipe
    team = models.ForeignKey(CombatTeam, on_delete=models.CASCADE, related_name='members', verbose_name=_('Équipe'))
    
    # Participant (utilisation de GenericForeignKey pour supporter différents types de participants)
    member_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, verbose_name=_('Type de membre'))
    member_id = models.CharField(max_length=50, verbose_name=_('ID du membre'))
    member = GenericForeignKey('member_content_type', 'member_id')
    
    # Statut et position dans l'équipe
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    is_reserve = models.BooleanField(default=False, verbose_name=_('Remplaçant'))
    position = models.PositiveIntegerField(default=0, verbose_name=_('Position dans l\'équipe'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Membre d\'équipe de combat')
        verbose_name_plural = _('Membres d\'équipe de combat')
        ordering = ['team', 'position']
        unique_together = [['team', 'member_content_type', 'member_id']]
        indexes = [
            models.Index(fields=['team', 'is_active']),
            models.Index(fields=['is_reserve']),
        ]
    
    def __str__(self):
        member_str = str(self.member) if self.member else f"ID: {self.member_id}"
        return f"{member_str} - {self.team.name}"


class Combat(models.Model):
    """
    Représente un combat individuel dans une compétition.
    Chaque combat implique deux participants (rouge et blanc selon les conventions traditionnelles).
    """
    STATUS_CHOICES = [
        ('scheduled', _('Programmé')),
        ('in_progress', _('En cours')),
        ('completed', _('Terminé')),
        ('cancelled', _('Annulé')),
    ]

    RESULT_CHOICES = [
        ('red_win', _('Victoire Rouge')),
        ('white_win', _('Victoire Blanc')),
        ('draw', _('Match nul')),
        ('no_decision', _('Sans décision')),
        ('disqualification_red', _('Disqualification Rouge')),
        ('disqualification_white', _('Disqualification Blanc')),
        ('walkover_red', _('Forfait Rouge')),
        ('walkover_white', _('Forfait Blanc')),
    ]

    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name=_('Référence'))
    
    # Liens avec la compétition et les participants
    competition = models.ForeignKey('competitions.Competition', on_delete=models.CASCADE, related_name='finance_combats', verbose_name=_('Compétition'))
    
    # Participants (rouge et blanc, selon les conventions de la discipline)
    # Utilisation du GenericForeignKey pour supporter à la fois des participants internes et externes
    red_participant_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, 
        related_name='combat_red_participants',
        verbose_name=_('Type d\'entité participant rouge'),
        null=True, blank=True
    )
    red_participant_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID participant rouge'))
    red_participant = GenericForeignKey('red_participant_content_type', 'red_participant_id')
    
    white_participant_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, 
        related_name='combat_white_participants',
        verbose_name=_('Type d\'entité participant blanc'),
        null=True, blank=True
    )
    white_participant_id = models.CharField(max_length=50, null=True, blank=True, verbose_name=_('ID participant blanc'))
    white_participant = GenericForeignKey('white_participant_content_type', 'white_participant_id')
    
    # Pour les compétitions par équipe
    red_team = models.ForeignKey('CombatTeam', on_delete=models.SET_NULL, related_name='red_combats', 
                                null=True, blank=True, verbose_name=_('Équipe rouge'))
    white_team = models.ForeignKey('CombatTeam', on_delete=models.SET_NULL, related_name='white_combats', 
                                  null=True, blank=True, verbose_name=_('Équipe blanche'))
    
    # Groupes et pools
    pool = models.ForeignKey('CombatPool', on_delete=models.SET_NULL, related_name='combats', 
                            null=True, blank=True, verbose_name=_('Poule'))
    round_number = models.PositiveIntegerField(default=1, verbose_name=_('Numéro de tour'))
    
    # Configuration du temps
    duration = models.PositiveIntegerField(default=120, verbose_name=_('Durée (en secondes)'))
    extension_duration = models.PositiveIntegerField(default=30, blank=True, null=True, verbose_name=_('Durée prolongation (en secondes)'))
    
    # Scores finaux (calculés à partir des CombatScore)
    red_final_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Score final rouge'))
    white_final_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Score final blanc'))
    
    # Statut et résultat
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name=_('Statut'))
    result = models.CharField(max_length=30, choices=RESULT_CHOICES, blank=True, null=True, verbose_name=_('Résultat'))
    
    # Dates et heures
    scheduled_time = models.DateTimeField(verbose_name=_('Heure programmée'))
    start_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Heure de début'))
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Heure de fin'))
    
    # Arbitres
    main_referee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='referee_combats', verbose_name=_('Arbitre principal'))
    side_referees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='side_referee_combats', 
                                          blank=True, verbose_name=_('Arbitres latéraux'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Combat')
        verbose_name_plural = _('Combats')
        ordering = ['scheduled_time', 'pool', 'round_number']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['round_number']),
        ]
    
    def __str__(self):
        red_name = "Équipe Rouge" if self.red_team else "Participant Rouge"
        white_name = "Équipe Blanche" if self.white_team else "Participant Blanc"
        
        if self.red_participant:
            red_name = str(self.red_participant)
        if self.white_participant:
            white_name = str(self.white_participant)
            
        return f"Combat: {red_name} vs {white_name} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Générer une référence si elle n'existe pas
        if not self.reference:
            now = timezone.now()
            self.reference = f"C-{now.strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        # Mettre à jour les heures de début/fin en fonction du statut
        if self.status == 'in_progress' and not self.start_time:
            self.start_time = timezone.now()
        
        if self.status == 'completed' and not self.end_time:
            self.end_time = timezone.now()
            
            # Déterminer automatiquement le résultat en fonction des scores
            if not self.result:
                if self.red_final_score > self.white_final_score:
                    self.result = 'red_win'
                elif self.white_final_score > self.red_final_score:
                    self.result = 'white_win'
                else:
                    self.result = 'draw'
        
        super().save(*args, **kwargs)
    
    def start_combat(self):
        """Démarre un combat programmé"""
        if self.status == 'scheduled':
            self.status = 'in_progress'
            self.start_time = timezone.now()
            self.save()
            return True
        return False
    
    def end_combat(self, result=None):
        """Termine un combat en cours"""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.end_time = timezone.now()
            if result:
                self.result = result
            self.save()
            return True
        return False
    
    def cancel_combat(self):
        """Annule un combat programmé ou en cours"""
        if self.status in ['scheduled', 'in_progress']:
            self.status = 'cancelled'
            self.save()
            return True
        return False
    
    def reset_scores(self):
        """Réinitialise les scores du combat"""
        # Supprimer tous les scores existants
        self.scores.all().delete()
        self.penalties.all().delete()
        
        # Réinitialiser les scores finaux
        self.red_final_score = 0
        self.white_final_score = 0
        self.result = None
        self.save()
        return True
    
    def update_final_scores(self):
        """Met à jour les scores finaux à partir des scores et pénalités enregistrés"""
        # Calculer le score rouge
        red_score = sum([s.value for s in self.scores.filter(participant_side='red')])
        red_penalties = sum([p.value for p in self.penalties.filter(participant_side='red')])
        self.red_final_score = max(0, red_score - red_penalties)  # Les scores ne peuvent pas être négatifs
        
        # Calculer le score blanc
        white_score = sum([s.value for s in self.scores.filter(participant_side='white')])
        white_penalties = sum([p.value for p in self.penalties.filter(participant_side='white')])
        self.white_final_score = max(0, white_score - white_penalties)  # Les scores ne peuvent pas être négatifs
        
        self.save()
        return True


class CombatScore(models.Model):
    """
    Représente un point marqué durant un combat.
    Chaque instance correspond à une attribution de points, avec la valeur, le temps, et l'arbitre.
    """
    SCORE_TYPES = [
        ('quarter', _('¼ point (Phân Tu Ðiểm)')),
        ('half', _('½ point (Nửa Ðiểm)')),
        ('one', _('1 point (Một Ðiểm)')),
        ('one_half', _('1.5 points (Một Ðiểm Dưới)')),
        ('two', _('2 points (Hai Ðiểm)')),
        ('custom', _('Valeur personnalisée')),
    ]
    
    PARTICIPANT_SIDES = [
        ('red', _('Rouge')),
        ('white', _('Blanc')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations principales
    combat = models.ForeignKey(Combat, on_delete=models.CASCADE, related_name='scores', verbose_name=_('Combat'))
    participant_side = models.CharField(max_length=10, choices=PARTICIPANT_SIDES, verbose_name=_('Côté du participant'))
    
    # Informations sur le score
    score_type = models.CharField(max_length=10, choices=SCORE_TYPES, verbose_name=_('Type de score'))
    value = models.DecimalField(max_digits=4, decimal_places=2, verbose_name=_('Valeur'))
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))
    
    # Informations temporelles
    time = models.DateTimeField(default=timezone.now, verbose_name=_('Heure d\'attribution'))
    round_number = models.PositiveIntegerField(default=1, verbose_name=_('Numéro de round'))
    time_in_round = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Temps dans le round (secondes)'))
    
    # Attribution du score
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='awarded_scores', verbose_name=_('Attribué par'))
    validated = models.BooleanField(default=True, verbose_name=_('Validé'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    class Meta:
        verbose_name = _('Score de combat')
        verbose_name_plural = _('Scores de combat')
        ordering = ['combat', 'time']
        indexes = [
            models.Index(fields=['combat', 'participant_side']),
            models.Index(fields=['time']),
            models.Index(fields=['round_number']),
        ]
    
    def __str__(self):
        return f"{self.get_participant_side_display()}: {self.value} points ({self.get_score_type_display()})"
    
    def save(self, *args, **kwargs):
        # Si c'est un type de score standard, définir la valeur automatiquement
        if self.score_type == 'quarter' and self.value != Decimal('0.25'):
            self.value = Decimal('0.25')
        elif self.score_type == 'half' and self.value != Decimal('0.5'):
            self.value = Decimal('0.5')
        elif self.score_type == 'one' and self.value != Decimal('1.0'):
            self.value = Decimal('1.0')
        elif self.score_type == 'one_half' and self.value != Decimal('1.5'):
            self.value = Decimal('1.5')
        elif self.score_type == 'two' and self.value != Decimal('2.0'):
            self.value = Decimal('2.0')
        
        super().save(*args, **kwargs)
        
        # Mettre à jour les scores finaux du combat
        self.combat.update_final_scores()


class CombatRound(models.Model):
    """
    Représente un round individuel dans un combat.
    Permet de suivre les scores, pauses et durées pour chaque round.
    """
    STATUS_CHOICES = [
        ('scheduled', _('Programmé')),
        ('in_progress', _('En cours')),
        ('paused', _('En pause')),
        ('completed', _('Terminé')),
        ('cancelled', _('Annulé')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relation avec le combat
    combat = models.ForeignKey(Combat, on_delete=models.CASCADE, related_name='rounds', verbose_name=_('Combat'))
    round_number = models.PositiveIntegerField(verbose_name=_('Numéro du round'))
    is_extension = models.BooleanField(default=False, verbose_name=_('Prolongation'))
    
    # Durée et temps
    duration = models.PositiveIntegerField(default=120, verbose_name=_('Durée prévue (en secondes)'))
    actual_duration = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Durée réelle (en secondes)'))
    
    # Statut et temps 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name=_('Statut'))
    start_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Heure de début'))
    end_time = models.DateTimeField(null=True, blank=True, verbose_name=_('Heure de fin'))
    
    # Pauses
    total_pause_duration = models.PositiveIntegerField(default=0, verbose_name=_('Durée totale des pauses (en secondes)'))
    pause_count = models.PositiveIntegerField(default=0, verbose_name=_('Nombre de pauses'))
    last_pause_start = models.DateTimeField(null=True, blank=True, verbose_name=_('Début de la dernière pause'))
    
    # Scores à la fin du round
    red_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Score Rouge à la fin du round'))
    white_score = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_('Score Blanc à la fin du round'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))
    
    class Meta:
        verbose_name = _('Round de combat')
        verbose_name_plural = _('Rounds de combat')
        ordering = ['combat', 'round_number']
        unique_together = [['combat', 'round_number']]
        indexes = [
            models.Index(fields=['combat', 'round_number']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        round_type = _("Prolongation") if self.is_extension else _("Round")
        return f"{round_type} {self.round_number} - {self.combat}"
    
    def save(self, *args, **kwargs):
        # Si c'est un nouveau round et que round_number n'est pas défini,
        # utiliser le prochain numéro disponible pour ce combat
        if not self.pk and not self.round_number:
            last_round = CombatRound.objects.filter(combat=self.combat).order_by('-round_number').first()
            self.round_number = (last_round.round_number + 1) if last_round else 1
        
        super().save(*args, **kwargs)
    
    def start_round(self):
        """Démarre un round programmé"""
        if self.status == 'scheduled':
            self.status = 'in_progress'
            self.start_time = timezone.now()
            self.save()
            return True
        return False
    
    def pause_round(self):
        """Met le round en pause"""
        if self.status == 'in_progress' and not self.last_pause_start:
            self.status = 'paused'
            self.last_pause_start = timezone.now()
            self.pause_count += 1
            self.save()
            return True
        return False
    
    def resume_round(self):
        """Reprend un round en pause"""
        if self.status == 'paused' and self.last_pause_start:
            pause_duration = (timezone.now() - self.last_pause_start).total_seconds()
            self.total_pause_duration += int(pause_duration)
            self.status = 'in_progress'
            self.last_pause_start = None
            self.save()
            return True
        return False
    
    def end_round(self):
        """Termine un round en cours ou en pause"""
        if self.status in ['in_progress', 'paused']:
            # Si le round est en pause, calculer la dernière pause
            if self.status == 'paused' and self.last_pause_start:
                pause_duration = (timezone.now() - self.last_pause_start).total_seconds()
                self.total_pause_duration += int(pause_duration)
                self.last_pause_start = None
            
            self.status = 'completed'
            self.end_time = timezone.now()
            
            # Calculer la durée réelle
            if self.start_time:
                total_duration = (self.end_time - self.start_time).total_seconds()
                self.actual_duration = int(total_duration) - self.total_pause_duration
            
            # Calculer les scores à la fin du round
            self.update_round_scores()
            
            self.save()
            return True
        return False
    
    def update_round_scores(self):
        """Met à jour les scores pour ce round spécifique"""
        # Récupérer tous les scores de ce round
        red_scores = sum([s.value for s in self.combat.scores.filter(
            participant_side='red', round_number=self.round_number)])
        
        red_penalties = sum([p.value for p in self.combat.penalties.filter(
            participant_side='red', round_number=self.round_number)])
        
        white_scores = sum([s.value for s in self.combat.scores.filter(
            participant_side='white', round_number=self.round_number)])
        
        white_penalties = sum([p.value for p in self.combat.penalties.filter(
            participant_side='white', round_number=self.round_number)])
        
        # Mettre à jour les scores du round
        self.red_score = max(0, red_scores - red_penalties)
        self.white_score = max(0, white_scores - white_penalties)
        self.save(update_fields=['red_score', 'white_score'])


class CombatPenalty(models.Model):
    """
    Représente une pénalité appliquée durant un combat.
    Chaque pénalité a un type, une valeur et affecte un participant.
    """
    PENALTY_TYPES = [
        ('canh_cao', _('Cảnh Cáo (Avertissement verbal)')),
        ('kem_diem', _('Kém Ðiểm (Retrait de ½ point)')),
        ('phat', _('Phạt (Retrait de 1 point)')),
        ('phat_hai', _('Phạt Hai (Retrait de 1 point + Disqualification)')),
        ('loai', _('Loại (Disqualification immédiate)')),
        ('exit', _('Sortie de l\'aire de combat')),
        ('custom', _('Pénalité personnalisée')),
    ]
    
    PARTICIPANT_SIDES = [
        ('red', _('Rouge')),
        ('white', _('Blanc')),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations principales
    combat = models.ForeignKey(Combat, on_delete=models.CASCADE, related_name='penalties', verbose_name=_('Combat'))
    participant_side = models.CharField(max_length=10, choices=PARTICIPANT_SIDES, verbose_name=_('Côté du participant'))
    
    # Informations sur la pénalité
    penalty_type = models.CharField(max_length=15, choices=PENALTY_TYPES, verbose_name=_('Type de pénalité'))
    value = models.DecimalField(max_digits=4, decimal_places=2, verbose_name=_('Valeur'))
    description = models.CharField(max_length=255, blank=True, verbose_name=_('Description'))
    
    # Informations temporelles
    time = models.DateTimeField(default=timezone.now, verbose_name=_('Heure d\'attribution'))
    round_number = models.PositiveIntegerField(default=1, verbose_name=_('Numéro de round'))
    time_in_round = models.PositiveIntegerField(null=True, blank=True, verbose_name=_('Temps dans le round (secondes)'))
    
    # Compteurs pour les pénalités
    # Pour suivre les règles spécifiques comme "3 sorties = -0.5 point" ou "5 sorties = disqualification"
    count_number = models.PositiveIntegerField(default=1, verbose_name=_('Numéro de décompte (ex: 3e sortie)'))
    cumulative = models.BooleanField(default=True, verbose_name=_('Cumulatif avec les pénalités précédentes'))
    
    # Attribution de la pénalité
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='awarded_penalties', verbose_name=_('Attribué par'))
    validated = models.BooleanField(default=True, verbose_name=_('Validé'))
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date de mise à jour'))
    
    class Meta:
        verbose_name = _('Pénalité de combat')
        verbose_name_plural = _('Pénalités de combat')
        ordering = ['combat', 'time']
        indexes = [
            models.Index(fields=['combat', 'participant_side']),
            models.Index(fields=['time']),
            models.Index(fields=['round_number']),
        ]
    
    def __str__(self):
        return f"{self.get_participant_side_display()}: {self.value} points de pénalité ({self.get_penalty_type_display()})"
    
    def save(self, *args, **kwargs):
        # Définir la valeur en fonction du type de pénalité si la valeur est différente de celle attendue
        if self.penalty_type == 'canh_cao' and self.value != 0:
            self.value = 0  # Avertissement verbal - pas de pénalité de points
        elif self.penalty_type == 'kem_diem' and self.value != Decimal('0.5'):
            self.value = Decimal('0.5')  # Retrait de 0.5 point
        elif self.penalty_type == 'phat' and self.value != Decimal('1.0'):
            self.value = Decimal('1.0')  # Retrait de 1 point
        elif self.penalty_type == 'phat_hai' and self.value != Decimal('1.0'):
            self.value = Decimal('1.0')  # Retrait de 1 point (plus disqualification gérée dans after_save)
        elif self.penalty_type == 'loai' and self.value != 0:
            self.value = 0  # Disqualification immédiate - pas de pénalité de points supplémentaires
        elif self.penalty_type == 'exit':
            # Les sorties ont une logique spéciale: 3e sortie = -0.5 point, 5e sortie = disqualification
            if self.count_number == 3:
                self.value = Decimal('0.5')
            elif self.count_number >= 5:
                self.value = 0  # La disqualification sera gérée après le save
            else:
                self.value = 0  # 1ère et 2e sorties n'ont pas de pénalité
        
        # Enregistrer l'objet
        super().save(*args, **kwargs)
        
        # Actions post-sauvegarde
        
        # Gérer les disqualifications automatiques
        if (self.penalty_type == 'phat_hai' or 
            (self.penalty_type == 'exit' and self.count_number >= 5)):
            # Définir le résultat du combat comme disqualification du côté approprié
            if self.participant_side == 'red':
                self.combat.result = 'disqualification_red'
            else:
                self.combat.result = 'disqualification_white'
            self.combat.status = 'completed'
            self.combat.end_time = timezone.now()
            self.combat.save(update_fields=['result', 'status', 'end_time'])
        
        # Mettre à jour les scores finaux du combat
        self.combat.update_final_scores()