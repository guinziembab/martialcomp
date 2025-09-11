"""
Modèles pour le système de gestion des combats selon les règles du Qwan Ki Do.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

class CombatConfiguration(models.Model):
    """
    Configuration globale pour les règles de combat d'une discipline.
    """
    SCORING_SYSTEM_CHOICES = [
        ('qwan_ki_do', _('Qwan Ki Do')),
        ('karate', _('Karaté')),
        ('taekwondo', _('Taekwondo')),
        ('judo', _('Judo')),
        ('custom', _('Personnalisé')),
    ]
    
    discipline = models.ForeignKey(
        'competitions.Discipline',
        on_delete=models.CASCADE,
        related_name='combat_configurations',
        verbose_name=_("Discipline")
    )
    nom = models.CharField(_("Nom"), max_length=100)
    system = models.CharField(
        _("Système de notation"),
        max_length=20,
        choices=SCORING_SYSTEM_CHOICES,
        default='qwan_ki_do'
    )
    description = models.TextField(_("Description"), blank=True)
    
    # Durées de combat
    durees_combat = models.JSONField(
        _("Durées de combat disponibles (secondes)"),
        default=list
    )
    
    # Durées de prolongation
    durees_prolongation = models.JSONField(
        _("Durées de prolongation disponibles (secondes)"),
        default=list
    )
    
    def save(self, *args, **kwargs):
        # Initialiser les valeurs par défaut si nécessaire
        if not self.durees_combat:
            self.durees_combat = [60, 90, 120]
        if not self.durees_prolongation:
            self.durees_prolongation = [30, 60]
        if not self.valeurs_points:
            self.valeurs_points = [0.25, 0.5, 1, 1.5, 2]
        if not self.valeurs_penalites:
            self.valeurs_penalites = [-0.25, -0.5, -1, -2]
        super().save(*args, **kwargs)
    
    # Configuration des sorties
    nb_sorties_avertissement = models.PositiveSmallIntegerField(
        _("Nombre de sorties avant avertissement"),
        default=3
    )
    nb_sorties_disqualification = models.PositiveSmallIntegerField(
        _("Nombre de sorties avant disqualification"),
        default=5
    )
    
    # Règles de points et pénalités
    valeurs_points = models.JSONField(
        _("Valeurs de points disponibles"),
        default=list
    )
    valeurs_penalites = models.JSONField(
        _("Valeurs de pénalités disponibles"),
        default=list
    )
    
    # Règles de sanction
    nb_avertissements_sanction = models.PositiveSmallIntegerField(
        _("Nombre d'avertissements avant sanction"),
        default=3
    )
    valeur_sanction = models.DecimalField(
        _("Valeur de la sanction après avertissements"),
        max_digits=4, 
        decimal_places=2,
        default=-1.0
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    def __str__(self):
        return f"{self.nom} - {self.discipline.name}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Configuration de combat")
        verbose_name_plural = _("Configurations de combat")


class Equipe(models.Model):
    """
    Ã‰quipe participant Ã  une compétition de combat.
    """
    nom = models.CharField(_("Nom"), max_length=100)
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='equipes_combat',
        verbose_name=_("Compétition")
    )
    club = models.ForeignKey(
        'competitions.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_combat',
        verbose_name=_("Club")
    )
    coach = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_coachees',
        verbose_name=_("Coach")
    )
    membres = models.ManyToManyField(
        'competitions.Practitioner',
        through='MembreEquipe',
        related_name='equipes_combat',
        verbose_name=_("Membres")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.nom} ({self.club.name if self.club else 'Sans club'})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Ã‰quipe")
        verbose_name_plural = _("Ã‰quipes")


class MembreEquipe(models.Model):
    """
    Relation entre un pratiquant et une équipe, avec information sur son statut
    (titulaire ou remplaçant).
    """
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_("Ã‰quipe")
    )
    pratiquant = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='equipe_memberships',
        verbose_name=_("Pratiquant")
    )
    est_remplacant = models.BooleanField(_("Est remplaçant"), default=False)
    ordre = models.PositiveSmallIntegerField(_("Ordre"), default=0)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    def __str__(self):
        status = _("Remplaçant") if self.est_remplacant else _("Titulaire")
        return f"{self.pratiquant.full_name} - {self.equipe.nom} ({status})"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Membre d'équipe")
        verbose_name_plural = _("Membres d'équipe")
        ordering = ['equipe', 'ordre']
        unique_together = [('equipe', 'pratiquant')]


class Poule(models.Model):
    """
    Groupe d'équipes ou de compétiteurs pour une phase de compétition.
    """
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='poules',
        verbose_name=_("Compétition")
    )
    nom = models.CharField(_("Nom"), max_length=100, default=_("Poule"))
    numero = models.PositiveSmallIntegerField(_("Numéro"), default=1)
    
    PHASE_CHOICES = [
        ('eliminatoire', _('Ã‰liminatoire')),
        ('quart', _('Quart de finale')),
        ('demi', _('Demi-finale')),
        ('finale', _('Finale')),
        ('repechage', _('RepÃªchage')),
    ]
    phase = models.CharField(
        _("Phase"), 
        max_length=20, 
        choices=PHASE_CHOICES, 
        default='eliminatoire'
    )
    
    equipes = models.ManyToManyField(
        Equipe,
        related_name='poules',
        verbose_name=_("Ã‰quipes"),
        blank=True
    )
    pratiquants = models.ManyToManyField(
        'competitions.Practitioner',
        related_name='poules_individuelles',
        verbose_name=_("Pratiquants individuels"),
        blank=True
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.nom} {self.numero} - {self.competition.title}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Poule")
        verbose_name_plural = _("Poules")
        ordering = ['competition', 'phase', 'numero']
        unique_together = [('competition', 'phase', 'numero')]


class Combat(models.Model):
    """
    Combat individuel ou par équipe dans une compétition.
    """
    TYPE_CHOICES = [
        ('individuel', _('Individuel')),
        ('equipe', _('Par équipe')),
    ]
    
    STATUS_CHOICES = [
        ('planifie', _('Planifié')),
        ('en_cours', _('En cours')),
        ('termine', _('Terminé')),
        ('annule', _('Annulé')),
    ]
    
    COULEUR_CHOICES = [
        ('rouge', _('Rouge')),
        ('blanc', _('Blanc')),
    ]
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='combats',
        verbose_name=_("Compétition")
    )
    poule = models.ForeignKey(
        Poule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats',
        verbose_name=_("Poule")
    )
    type_combat = models.CharField(
        _("Type de combat"),
        max_length=20,
        choices=TYPE_CHOICES,
        default='individuel'
    )
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='planifie'
    )
    
    # Participants au combat
    equipe_rouge = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats_rouge',
        verbose_name=_("Ã‰quipe rouge")
    )
    equipe_blanc = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats_blanc',
        verbose_name=_("Ã‰quipe blanc")
    )
    
    pratiquant_rouge = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats_rouge',
        verbose_name=_("Pratiquant rouge")
    )
    pratiquant_blanc = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats_blanc',
        verbose_name=_("Pratiquant blanc")
    )
    
    # Paramètres du combat
    duree_combat = models.PositiveSmallIntegerField(
        _("Durée du combat (secondes)"),
        default=120
    )
    duree_prolongation = models.PositiveSmallIntegerField(
        _("Durée de prolongation (secondes)"),
        null=True,
        blank=True
    )
    
    # Configuration des règles
    configuration = models.ForeignKey(
        CombatConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        related_name='combats',
        verbose_name=_("Configuration")
    )
    
    # Résultat du combat
    score_rouge = models.DecimalField(
        _("Score rouge"),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    score_blanc = models.DecimalField(
        _("Score blanc"),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    vainqueur = models.CharField(
        _("Couleur du vainqueur"),
        max_length=10,
        choices=COULEUR_CHOICES,
        null=True,
        blank=True
    )
    
    est_nul = models.BooleanField(_("Match nul"), default=False)
    motif_annulation = models.TextField(_("Motif d'annulation"), blank=True)
    
    # Suivi temporel
    date_planifiee = models.DateTimeField(_("Date planifiée"), null=True, blank=True)
    debut_combat = models.DateTimeField(_("Début du combat"), null=True, blank=True)
    fin_combat = models.DateTimeField(_("Fin du combat"), null=True, blank=True)
    
    # Arbitrage
    arbitre_central = models.ForeignKey(
        'competitions.Judge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats_arbitre_central',
        verbose_name=_("Arbitre central")
    )
    arbitres_lateraux = models.ManyToManyField(
        'competitions.Judge',
        related_name='combats_arbitre_lateral',
        verbose_name=_("Arbitres latéraux"),
        blank=True
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis Ã  jour le"), auto_now=True)
    
    def __str__(self):
        if self.type_combat == 'individuel':
            rouge = self.pratiquant_rouge.full_name if self.pratiquant_rouge else "Non défini"
            blanc = self.pratiquant_blanc.full_name if self.pratiquant_blanc else "Non défini"
        else:
            rouge = self.equipe_rouge.nom if self.equipe_rouge else "Non définie"
            blanc = self.equipe_blanc.nom if self.equipe_blanc else "Non définie"
        return f"Combat {rouge} vs {blanc} - {self.get_status_display()}"
    
    def start_combat(self):
        """Démarre le combat."""
        if self.status == 'planifie':
            self.status = 'en_cours'
            self.debut_combat = timezone.now()
            self.save(update_fields=['status', 'debut_combat'])
            return True
        return False
    
    def end_combat(self):
        """Termine le combat et détermine le vainqueur."""
        if self.status == 'en_cours':
            self.status = 'termine'
            self.fin_combat = timezone.now()
            
            # Déterminer le vainqueur
            if self.score_rouge > self.score_blanc:
                self.vainqueur = 'rouge'
                self.est_nul = False
            elif self.score_blanc > self.score_rouge:
                self.vainqueur = 'blanc'
                self.est_nul = False
            else:
                self.vainqueur = None
                self.est_nul = True
                
            self.save(update_fields=['status', 'fin_combat', 'vainqueur', 'est_nul'])
            return True
        return False
    
    def cancel_combat(self, motif=""):
        """Annule le combat."""
        if self.status != 'termine':
            self.status = 'annule'
            self.motif_annulation = motif
            self.save(update_fields=['status', 'motif_annulation'])
            return True
        return False
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Combat")
        verbose_name_plural = _("Combats")
        ordering = ['competition', 'date_planifiee', 'poule']


class ActionCombat(models.Model):
    """
    Action survenue pendant un combat (point, pénalité, etc.).
    """
    TYPE_CHOICES = [
        ('point', _('Point')),
        ('penalite', _('Pénalité')),
        ('avertissement', _('Avertissement')),
        ('sortie', _('Sortie de tapis')),
        ('pause', _('Pause')),
        ('disqualification', _('Disqualification')),
    ]
    
    COULEUR_CHOICES = [
        ('rouge', _('Rouge')),
        ('blanc', _('Blanc')),
        ('neutre', _('Neutre')),
    ]
    
    combat = models.ForeignKey(
        Combat,
        on_delete=models.CASCADE,
        related_name='actions',
        verbose_name=_("Combat")
    )
    type_action = models.CharField(
        _("Type d'action"),
        max_length=20,
        choices=TYPE_CHOICES
    )
    couleur = models.CharField(
        _("Couleur concernée"),
        max_length=10,
        choices=COULEUR_CHOICES,
        default='neutre'
    )
    valeur = models.DecimalField(
        _("Valeur"),
        max_digits=4,
        decimal_places=2,
        default=0
    )
    description = models.CharField(_("Description"), max_length=255, blank=True)
    temps = models.DateTimeField(_("Temps de l'action"), auto_now_add=True)
    arbitre = models.ForeignKey(
        'competitions.Judge',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actions_combat',
        verbose_name=_("Arbitre")
    )
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour mettre Ã  jour le score du combat en fonction
        de l'action enregistrée.
        """
        super().save(*args, **kwargs)
        
        # Mettre Ã  jour le score du combat
        combat = self.combat
        if self.type_action in ['point', 'penalite']:
            if self.couleur == 'rouge':
                combat.score_rouge += self.valeur
            elif self.couleur == 'blanc':
                combat.score_blanc += self.valeur
                
            combat.save(update_fields=['score_rouge', 'score_blanc'])
    
    def __str__(self):
        return f"{self.get_type_action_display()} {self.couleur} ({self.valeur}) - {self.combat}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Action de combat")
        verbose_name_plural = _("Actions de combat")
        ordering = ['combat', 'temps']

