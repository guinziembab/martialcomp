"""
Modèles pour le système de gestion des combats selon les règles du Qwan Ki Do.
Version 2.0 - Support compétitions par équipes avec ententes et fusions.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid


# =============================================================================
# SPRINT 1: Configuration des équipes (REQ-01, REQ-02)
# =============================================================================

class TeamConfiguration(models.Model):
    """
    Configuration de la composition des équipes pour une compétition.
    Permet de définir le format (N titulaires + M remplaçants) et les règles
    de validation des équipes.
    """
    # Présets standards
    FORMAT_2_1 = '2+1'
    FORMAT_3_1 = '3+1'
    FORMAT_3_2 = '3+2'
    FORMAT_5_2 = '5+2'
    FORMAT_CUSTOM = 'custom'

    FORMAT_CHOICES = [
        (FORMAT_2_1, _('2 titulaires + 1 remplaçant')),
        (FORMAT_3_1, _('3 titulaires + 1 remplaçant')),
        (FORMAT_3_2, _('3 titulaires + 2 remplaçants')),
        (FORMAT_5_2, _('5 titulaires + 2 remplaçants')),
        (FORMAT_CUSTOM, _('Personnalisé')),
    ]

    competition = models.OneToOneField(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='team_configuration',
        verbose_name=_("Compétition")
    )

    format_preset = models.CharField(
        _("Format prédéfini"),
        max_length=20,
        choices=FORMAT_CHOICES,
        default=FORMAT_3_1
    )

    # Configuration titulaires
    min_titulaires = models.PositiveSmallIntegerField(
        _("Minimum de titulaires"),
        default=3,
        validators=[MinValueValidator(1)]
    )
    max_titulaires = models.PositiveSmallIntegerField(
        _("Maximum de titulaires"),
        default=3,
        validators=[MinValueValidator(1)]
    )

    # Configuration remplaçants
    min_remplacants = models.PositiveSmallIntegerField(
        _("Minimum de remplaçants"),
        default=0
    )
    max_remplacants = models.PositiveSmallIntegerField(
        _("Maximum de remplaçants"),
        default=1
    )
    remplacants_obligatoires = models.BooleanField(
        _("Remplaçants obligatoires"),
        default=False,
        help_text=_("Si activé, les équipes doivent avoir le minimum de remplaçants requis")
    )

    # Seuil minimum d'équipes pour maintenir le mode équipe
    min_equipes_required = models.PositiveSmallIntegerField(
        _("Nombre minimum d'équipes"),
        default=3,
        help_text=_("Si moins d'équipes sont inscrites, proposer basculement vers individuel")
    )

    # Configuration des ententes (REQ-06)
    max_ententes_par_equipe = models.PositiveSmallIntegerField(
        _("Maximum d'ententes par équipe"),
        default=2,
        help_text=_("Nombre maximum de membres en entente (prêtés d'autres clubs)")
    )
    entente_validation_required = models.BooleanField(
        _("Validation des ententes requise"),
        default=False,
        help_text=_("Si activé, les ententes doivent être approuvées par l'organisateur")
    )

    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Configuration d'équipe")
        verbose_name_plural = _("Configurations d'équipes")

    def __str__(self):
        return f"Config équipe: {self.competition.title} ({self.get_format_preset_display()})"

    def save(self, *args, **kwargs):
        """Applique les présets si un format prédéfini est sélectionné."""
        if self.format_preset != self.FORMAT_CUSTOM:
            presets = {
                self.FORMAT_2_1: (2, 2, 0, 1),
                self.FORMAT_3_1: (3, 3, 0, 1),
                self.FORMAT_3_2: (3, 3, 0, 2),
                self.FORMAT_5_2: (5, 5, 0, 2),
            }
            if self.format_preset in presets:
                self.min_titulaires, self.max_titulaires, self.min_remplacants, self.max_remplacants = presets[self.format_preset]
        super().save(*args, **kwargs)

    def is_team_valid(self, equipe):
        """
        Vérifie si une équipe respecte cette configuration.

        Returns:
            tuple: (bool is_valid, str message)
        """
        nb_titulaires = equipe.memberships.filter(est_remplacant=False).count()
        nb_remplacants = equipe.memberships.filter(est_remplacant=True).count()
        nb_ententes = equipe.memberships.filter(is_entente=True).count()

        errors = []

        if nb_titulaires < self.min_titulaires:
            errors.append(f"Titulaires insuffisants: {nb_titulaires}/{self.min_titulaires}")
        if nb_titulaires > self.max_titulaires:
            errors.append(f"Trop de titulaires: {nb_titulaires}/{self.max_titulaires}")
        if self.remplacants_obligatoires and nb_remplacants < self.min_remplacants:
            errors.append(f"Remplaçants insuffisants: {nb_remplacants}/{self.min_remplacants}")
        if nb_remplacants > self.max_remplacants:
            errors.append(f"Trop de remplaçants: {nb_remplacants}/{self.max_remplacants}")
        if nb_ententes > self.max_ententes_par_equipe:
            errors.append(f"Trop d'ententes: {nb_ententes}/{self.max_ententes_par_equipe}")

        if errors:
            return False, "; ".join(errors)
        return True, _("Équipe conforme")

    @property
    def max_total_membres(self):
        """Retourne le nombre maximum total de membres autorisés."""
        return self.max_titulaires + self.max_remplacants


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
    Equipe participant a une competition de combat.
    Supporte les equipes mono-club et multi-clubs (fusion/entente).

    Sprint 1: Ajout support fusion et soft-delete (is_active, merged_into)
    """
    TYPE_CHOICES = [
        ('mono_club', _('Mono-club')),
        ('multi_club', _('Multi-clubs (fusion)')),
    ]

    STATUS_CHOICES = [
        ('active', _('Active')),
        ('pending_fusion', _('Fusion en attente')),
        ('fusion_complete', _('Fusion completee')),
        ('archived', _('Archivée')),  # Sprint 1: Nouveau statut pour les équipes fusionnées
    ]

    nom = models.CharField(_("Nom"), max_length=100)
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='equipes_combat',
        verbose_name=_("Competition")
    )
    # Club principal (createur de l'equipe)
    club = models.ForeignKey(
        'competitions.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_combat',
        verbose_name=_("Club principal")
    )
    # Clubs partenaires pour les equipes multi-clubs
    clubs_partenaires = models.ManyToManyField(
        'competitions.Club',
        related_name='equipes_partenaires',
        verbose_name=_("Clubs partenaires"),
        blank=True
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
        through_fields=('equipe', 'pratiquant'),  # Spécifie les FK à utiliser
        related_name='equipes_combat',
        verbose_name=_("Membres")
    )

    # Type d'equipe (mono ou multi-club)
    type_equipe = models.CharField(
        _("Type d'equipe"),
        max_length=20,
        choices=TYPE_CHOICES,
        default='mono_club'
    )

    # Statut pour la fusion
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Equipe parente (si cette equipe resulte d'une fusion)
    equipe_parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_fusionnees',
        verbose_name=_("Equipe parente (fusion)")
    )

    # Sprint 1: Champs pour la gestion des fusions (REQ-07)
    is_fusion = models.BooleanField(
        _("Est une fusion"),
        default=False,
        help_text=_("Indique si cette équipe résulte d'une fusion")
    )
    merged_into = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_absorbees',
        verbose_name=_("Fusionnée dans"),
        help_text=_("Si archivée suite à fusion, l'équipe résultante")
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("False si l'équipe a été fusionnée ou archivée (soft delete)")
    )

    # Nombre minimum/maximum de membres requis
    min_membres = models.PositiveSmallIntegerField(_("Minimum de membres"), default=3)
    max_membres = models.PositiveSmallIntegerField(_("Maximum de membres"), default=5)

    # Demande de fusion en attente
    demande_fusion_message = models.TextField(_("Message de demande de fusion"), blank=True)

    # Catégorie de combat (pour grouper les équipes)
    category = models.ForeignKey(
        'competitions.CompetitionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_combat',
        verbose_name=_("Catégorie")
    )

    created_at = models.DateTimeField(_("Cree le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis a jour le"), auto_now=True)

    def __str__(self):
        prefix = "[Archivée] " if not self.is_active else ""
        if self.is_fusion:
            prefix = "[Fusion] " + prefix
        if self.type_equipe == 'multi_club':
            clubs = [self.club.name] if self.club else []
            clubs.extend([c.name for c in self.clubs_partenaires.all()[:2]])
            return f"{prefix}{self.nom} ({' + '.join(clubs)})"
        return f"{prefix}{self.nom} ({self.club.name if self.club else 'Sans club'})"

    @property
    def is_complete(self):
        """Verifie si l'equipe a le nombre minimum de membres."""
        return self.memberships.filter(est_remplacant=False).count() >= self.min_membres

    @property
    def membres_manquants(self):
        """Retourne le nombre de membres titulaires manquants."""
        current = self.memberships.filter(est_remplacant=False).count()
        return max(0, self.min_membres - current)

    @property
    def peut_fusionner(self):
        """Verifie si l'equipe peut demander une fusion (incomplete et active)."""
        return not self.is_complete and self.type_equipe == 'mono_club' and self.is_active

    @property
    def nb_ententes(self):
        """Retourne le nombre de membres en entente dans l'équipe."""
        return self.memberships.filter(is_entente=True).count()

    def get_all_clubs(self):
        """Retourne tous les clubs associes a l'equipe."""
        clubs = []
        if self.club:
            clubs.append(self.club)
        clubs.extend(list(self.clubs_partenaires.all()))
        return clubs

    def has_started_combats(self):
        """Vérifie si l'équipe a déjà des combats commencés ou terminés."""
        from django.db.models import Q
        combats_actifs = self.combats_rouge.filter(
            Q(status='en_cours') | Q(status='termine')
        ).exists() or self.combats_blanc.filter(
            Q(status='en_cours') | Q(status='termine')
        ).exists()
        return combats_actifs

    def archive(self, merged_into=None):
        """Archive l'équipe (soft delete après fusion)."""
        self.is_active = False
        self.status = 'archived'
        if merged_into:
            self.merged_into = merged_into
        self.save(update_fields=['is_active', 'status', 'merged_into', 'updated_at'])

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Equipe")
        verbose_name_plural = _("Equipes")


class MembreEquipe(models.Model):
    """
    Relation entre un pratiquant et une équipe, avec information sur son statut
    (titulaire ou remplaçant).

    Sprint 1: Ajout support ententes (REQ-06) et traçabilité fusion.
    """
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name=_("Équipe")
    )
    pratiquant = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='equipe_memberships',
        verbose_name=_("Pratiquant")
    )
    est_remplacant = models.BooleanField(_("Est remplaçant"), default=False)
    ordre = models.PositiveSmallIntegerField(_("Ordre de passage"), default=0)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    # Sprint 1: Champs pour la gestion des ententes (REQ-06)
    is_entente = models.BooleanField(
        _("Est en entente"),
        default=False,
        help_text=_("Membre prêté par un autre club")
    )
    club_origine = models.ForeignKey(
        'competitions.Club',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='membres_en_entente',
        verbose_name=_("Club d'origine"),
        help_text=_("Pour les membres en entente: leur club d'origine")
    )
    equipe_origine = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='membres_pretes',
        verbose_name=_("Équipe d'origine"),
        help_text=_("Pour les ententes: équipe d'où vient le membre")
    )

    # Sprint 1: Traçabilité pour les fusions (REQ-07)
    equipe_avant_fusion = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='anciens_membres',
        verbose_name=_("Équipe avant fusion"),
        help_text=_("Équipe d'origine si ce membre a été transféré lors d'une fusion")
    )

    # Sprint 1: Suivi des combats pour le podium (REQ-05)
    a_combattu = models.BooleanField(
        _("A combattu"),
        default=False,
        help_text=_("Indique si le membre a participé à au moins un combat")
    )

    def __str__(self):
        status = _("Remplaçant") if self.est_remplacant else _("Titulaire")
        entente_info = ""
        if self.is_entente and self.club_origine:
            entente_info = f" [Entente: {self.club_origine.name}]"
        return f"{self.pratiquant.full_name} - {self.equipe.nom} ({status}){entente_info}"

    def save(self, *args, **kwargs):
        """Auto-remplit club_origine si entente et non défini."""
        if self.is_entente and not self.club_origine:
            self.club_origine = self.pratiquant.club
        super().save(*args, **kwargs)

    @property
    def role_display(self):
        """Retourne le rôle avec indication d'entente si applicable."""
        role = _("Titulaire") if not self.est_remplacant else _("Remplaçant")
        if self.is_entente:
            return f"{role} (Entente)"
        return role

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Membre d'équipe")
        verbose_name_plural = _("Membres d'équipe")
        ordering = ['equipe', 'est_remplacant', 'ordre']
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
    category = models.ForeignKey(
        'competitions.CompetitionCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='poules',
        verbose_name=_("Catégorie")
    )
    description = models.TextField(_("Description"), blank=True)
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    def __str__(self):
        return f"{self.nom} {self.numero} - {self.competition.title}"
    
    class Meta:
        app_label = 'competitions'
        verbose_name = _("Poule")
        verbose_name_plural = _("Poules")
        ordering = ['competition', 'category', 'phase', 'numero']


class Combat(models.Model):
    """
    Combat individuel ou par équipe dans une compétition.

    Sprint 1: Ajout codes couleur pour l'affichage état matchs (REQ-08)
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
        ('forfait', _('Forfait')),      # Sprint 1 REQ-08
        ('reporte', _('Reporté')),       # Sprint 1 REQ-08
    ]

    # Sprint 1 REQ-08: Codes couleur pour les états des matchs (style football)
    STATUS_COLORS = {
        'planifie': '#F5F5F5',      # Gris clair - À jouer
        'en_cours': '#FFF3CD',      # Jaune - En cours
        'termine': '#D4EDDA',       # Vert - Terminé
        'forfait': '#F8D7DA',       # Rouge - Forfait
        'reporte': '#D1ECF1',       # Bleu - Reporté
        'annule': '#F8D7DA',        # Rouge - Annulé
    }

    # Texte couleurs pour CSS classes
    STATUS_CSS_CLASSES = {
        'planifie': 'match-scheduled',
        'en_cours': 'match-in-progress',
        'termine': 'match-completed',
        'forfait': 'match-forfeit',
        'reporte': 'match-postponed',
        'annule': 'match-cancelled',
    }

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
    score_cumul_rouge = models.DecimalField(
        _("Score cumulé rouge"),
        max_digits=5,
        decimal_places=2,
        default=0
    )
    score_cumul_blanc = models.DecimalField(
        _("Score cumulé blanc"),
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

    def forfait_combat(self, couleur_gagnante, motif=""):
        """Marque le combat comme forfait avec un gagnant par défaut."""
        if self.status not in ('termine', 'annule'):
            self.status = 'forfait'
            self.vainqueur = couleur_gagnante
            self.motif_annulation = motif or _("Forfait adverse")
            self.fin_combat = timezone.now()
            self.save(update_fields=['status', 'vainqueur', 'motif_annulation', 'fin_combat'])
            return True
        return False

    def reporter_combat(self, motif=""):
        """Reporte le combat."""
        if self.status in ('planifie', 'en_cours'):
            self.status = 'reporte'
            self.motif_annulation = motif or _("Reporté")
            self.save(update_fields=['status', 'motif_annulation'])
            return True
        return False

    # Sprint 1 REQ-08: Propriétés pour les couleurs d'état
    @property
    def status_color(self):
        """Retourne le code couleur hexadécimal pour le statut actuel."""
        return self.STATUS_COLORS.get(self.status, '#F5F5F5')

    @property
    def status_css_class(self):
        """Retourne la classe CSS pour le statut actuel."""
        return self.STATUS_CSS_CLASSES.get(self.status, 'match-scheduled')

    @property
    def status_icon(self):
        """Retourne l'icône FontAwesome appropriée pour le statut."""
        icons = {
            'planifie': 'fas fa-clock',
            'en_cours': 'fas fa-play-circle',
            'termine': 'fas fa-check-circle',
            'forfait': 'fas fa-user-slash',
            'reporte': 'fas fa-calendar-times',
            'annule': 'fas fa-times-circle',
        }
        return icons.get(self.status, 'fas fa-question-circle')

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
            from decimal import Decimal
            valeur = Decimal(str(self.valeur))
            if self.couleur == 'rouge':
                combat.score_rouge += valeur
            elif self.couleur == 'blanc':
                combat.score_blanc += valeur

            combat.save(update_fields=['score_rouge', 'score_blanc'])
    
    def __str__(self):
        return f"{self.get_type_action_display()} {self.couleur} ({self.valeur}) - {self.combat}"

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Action de combat")
        verbose_name_plural = _("Actions de combat")
        ordering = ['combat', 'temps']


# =============================================================================
# SPRINT 2: Ententes et Fusions (REQ-06, REQ-07)
# =============================================================================

class Entente(models.Model):
    """
    Sprint 2 REQ-06: Gestion des ententes (prêt de joueurs entre clubs).

    Une entente permet à un pratiquant d'un club de renforcer temporairement
    une équipe d'un autre club pour une compétition donnée.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Refusée')),
        ('cancelled', _('Annulée')),
        ('expired', _('Expirée')),
    ]

    # La compétition concernée
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='ententes',
        verbose_name=_("Compétition")
    )

    # Le pratiquant prêté
    pratiquant = models.ForeignKey(
        'competitions.Practitioner',
        on_delete=models.CASCADE,
        related_name='ententes',
        verbose_name=_("Pratiquant prêté")
    )

    # Club d'origine (celui qui prête le joueur)
    club_origine = models.ForeignKey(
        'competitions.Club',
        on_delete=models.CASCADE,
        related_name='ententes_sortantes',
        verbose_name=_("Club d'origine")
    )

    # Club d'accueil (celui qui reçoit le joueur)
    club_accueil = models.ForeignKey(
        'competitions.Club',
        on_delete=models.CASCADE,
        related_name='ententes_entrantes',
        verbose_name=_("Club d'accueil")
    )

    # Équipe d'accueil (où le joueur sera intégré)
    equipe_accueil = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='ententes_recues',
        verbose_name=_("Équipe d'accueil"),
        null=True,
        blank=True
    )

    # Rôle prévu dans l'équipe d'accueil
    ROLE_CHOICES = [
        ('titulaire', _('Titulaire')),
        ('remplacant', _('Remplaçant')),
    ]
    role = models.CharField(
        _("Rôle prévu"),
        max_length=20,
        choices=ROLE_CHOICES,
        default='titulaire'
    )

    # Statut de la demande
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Justification / notes
    raison = models.TextField(
        _("Raison de l'entente"),
        blank=True,
        help_text=_("Motif de la demande d'entente")
    )

    # Validation
    validateur = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ententes_validees',
        verbose_name=_("Validateur")
    )
    date_validation = models.DateTimeField(
        _("Date de validation"),
        null=True,
        blank=True
    )
    commentaire_validation = models.TextField(
        _("Commentaire de validation"),
        blank=True
    )

    # Demandeur
    demandeur = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ententes_demandees',
        verbose_name=_("Demandé par")
    )

    date_demande = models.DateTimeField(_("Date de demande"), auto_now_add=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Entente")
        verbose_name_plural = _("Ententes")
        ordering = ['-date_demande']

    def __str__(self):
        return f"Entente: {self.pratiquant.full_name} ({self.club_origine.name} → {self.club_accueil.name})"

    def approve(self, user, commentaire=""):
        """Approuve l'entente et intègre le pratiquant dans l'équipe."""
        if self.status == 'pending':
            self.status = 'approved'
            self.validateur = user
            self.date_validation = timezone.now()
            self.commentaire_validation = commentaire
            self.save()

            # Créer l'appartenance à l'équipe avec le flag is_entente
            if self.equipe_accueil:
                MembreEquipe.objects.create(
                    equipe=self.equipe_accueil,
                    pratiquant=self.pratiquant,
                    est_remplacant=(self.role == 'remplacant'),
                    is_entente=True,
                    club_origine=self.club_origine
                )
            return True
        return False

    def reject(self, user, commentaire=""):
        """Refuse l'entente."""
        if self.status == 'pending':
            self.status = 'rejected'
            self.validateur = user
            self.date_validation = timezone.now()
            self.commentaire_validation = commentaire
            self.save()
            return True
        return False

    def cancel(self):
        """Annule une entente approuvée (retire le membre de l'équipe)."""
        if self.status == 'approved':
            # Retirer de l'équipe
            MembreEquipe.objects.filter(
                equipe=self.equipe_accueil,
                pratiquant=self.pratiquant,
                is_entente=True
            ).delete()
            self.status = 'cancelled'
            self.save()
            return True
        return False


class TeamMerge(models.Model):
    """
    Sprint 2 REQ-07: Historique des fusions d'équipes.

    Une fusion permet de combiner deux équipes incomplètes en une seule
    équipe fonctionnelle pour la compétition.
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvée')),
        ('rejected', _('Refusée')),
        ('completed', _('Complétée')),
        ('cancelled', _('Annulée')),
    ]

    # La compétition concernée
    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='fusions',
        verbose_name=_("Compétition")
    )

    # L'équipe initiatrice de la demande
    equipe_demandeur = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='fusions_initiees',
        verbose_name=_("Équipe demandeuse")
    )

    # L'équipe qui reçoit la demande
    equipe_cible = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='fusions_recues',
        verbose_name=_("Équipe cible")
    )

    # L'équipe résultante de la fusion (créée après approbation)
    equipe_resultante = models.ForeignKey(
        Equipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fusion_source',
        verbose_name=_("Équipe résultante")
    )

    # Nom proposé pour l'équipe fusionnée
    nom_equipe_proposee = models.CharField(
        _("Nom proposé"),
        max_length=100,
        blank=True,
        help_text=_("Nom suggéré pour l'équipe fusionnée")
    )

    # Statut de la demande
    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Raison de la demande
    raison = models.TextField(
        _("Raison de la fusion"),
        blank=True,
        help_text=_("Explication de la demande de fusion")
    )

    # Commentaire de validation
    commentaire_validation = models.TextField(
        _("Commentaire"),
        blank=True
    )

    # Validation
    validateur = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fusions_validees',
        verbose_name=_("Validateur")
    )
    date_validation = models.DateTimeField(
        _("Date de validation"),
        null=True,
        blank=True
    )
    date_fusion = models.DateTimeField(
        _("Date de fusion effective"),
        null=True,
        blank=True
    )

    # Demandeur
    demandeur = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fusions_demandees',
        verbose_name=_("Demandé par")
    )

    # Date de demande (créée automatiquement)
    date_demande = models.DateTimeField(
        _("Date de demande"),
        auto_now_add=True
    )

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Fusion d'équipe")
        verbose_name_plural = _("Fusions d'équipes")
        ordering = ['-date_demande']

    def __str__(self):
        return f"Fusion: {self.equipe_demandeur.nom} + {self.equipe_cible.nom}"

    def approve_and_merge(self, user, nom_equipe=None):
        """
        Approuve la fusion et crée l'équipe résultante.

        Args:
            user: L'utilisateur qui approuve
            nom_equipe: Nom de l'équipe fusionnée (ou auto-généré)

        Returns:
            Equipe: L'équipe résultante ou None si échec
        """
        if self.status != 'pending':
            return None

        # Nom par défaut
        if not nom_equipe:
            nom_equipe = self.nom_propose or f"{self.equipe_demandeur.nom} + {self.equipe_cible.nom}"

        # Créer l'équipe fusionnée
        equipe_fusionnee = Equipe.objects.create(
            nom=nom_equipe,
            competition=self.competition,
            club=self.equipe_demandeur.club,  # Club principal = demandeur
            type_equipe='multi_club',
            is_fusion=True,
            category=self.equipe_demandeur.category
        )

        # Ajouter le club cible comme partenaire
        if self.equipe_cible.club:
            equipe_fusionnee.clubs_partenaires.add(self.equipe_cible.club)

        # Transférer les membres des deux équipes
        for membre in self.equipe_demandeur.memberships.all():
            MembreEquipe.objects.create(
                equipe=equipe_fusionnee,
                pratiquant=membre.pratiquant,
                est_remplacant=membre.est_remplacant,
                ordre=membre.ordre,
                equipe_avant_fusion=self.equipe_demandeur,
                is_entente=membre.is_entente,
                club_origine=membre.club_origine
            )

        for membre in self.equipe_cible.memberships.all():
            # Vérifier que le membre n'est pas déjà dans l'équipe
            if not MembreEquipe.objects.filter(
                equipe=equipe_fusionnee,
                pratiquant=membre.pratiquant
            ).exists():
                MembreEquipe.objects.create(
                    equipe=equipe_fusionnee,
                    pratiquant=membre.pratiquant,
                    est_remplacant=membre.est_remplacant,
                    ordre=membre.ordre + 100,  # Décalage pour éviter les conflits
                    equipe_avant_fusion=self.equipe_cible,
                    is_entente=membre.is_entente,
                    club_origine=membre.club_origine
                )

        # Archiver les anciennes équipes
        self.equipe_demandeur.archive(merged_into=equipe_fusionnee)
        self.equipe_cible.archive(merged_into=equipe_fusionnee)

        # Mettre à jour la fusion
        self.equipe_resultante = equipe_fusionnee
        self.status = 'completed'
        self.validee_par = user
        self.date_validation = timezone.now()
        self.save()

        return equipe_fusionnee

    def reject(self, user, message=""):
        """Refuse la fusion."""
        if self.status == 'pending':
            self.status = 'rejected'
            self.validee_par = user
            self.date_validation = timezone.now()
            self.message_reponse = message
            self.save()
            return True
        return False


# =============================================================================
# SPRINT 3: Phase Finale et Podium (REQ-05)
# =============================================================================

class PhaseFinale(models.Model):
    """
    Sprint 3 REQ-05: Modèle pour gérer la phase finale d'une compétition par équipes.

    Permet de :
    - Configurer les phases éliminatoires (quarts, demis, finale)
    - Générer automatiquement le bracket à partir des classements de poules
    - Gérer le podium complet (y compris petite finale)
    """
    PHASE_CHOICES = [
        ('huitiemes', _('Huitièmes de finale')),
        ('quarts', _('Quarts de finale')),
        ('demis', _('Demi-finales')),
        ('petite_finale', _('Petite finale (3ème place)')),
        ('finale', _('Finale')),
    ]

    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('active', _('Active')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée')),
    ]

    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='phases_finales',
        verbose_name=_("Compétition")
    )

    phase = models.CharField(
        _("Phase"),
        max_length=20,
        choices=PHASE_CHOICES,
        default='demis'
    )

    status = models.CharField(
        _("Statut"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Configuration
    qualifies_par_poule = models.PositiveSmallIntegerField(
        _("Qualifiés par poule"),
        default=2,
        help_text=_("Nombre de premiers de chaque poule qualifiés")
    )

    avec_petite_finale = models.BooleanField(
        _("Avec petite finale"),
        default=True,
        help_text=_("Activer le match pour la 3ème place")
    )

    # Tracking
    created_at = models.DateTimeField(_("Créée le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mise à jour le"), auto_now=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Phase finale")
        verbose_name_plural = _("Phases finales")
        ordering = ['competition', '-created_at']
        unique_together = [['competition', 'phase']]

    def __str__(self):
        return f"{self.get_phase_display()} - {self.competition.title}"

    def get_combats(self):
        """Retourne les combats de cette phase."""
        return self.combats.filter(is_active=True).order_by('ordre')

    def is_complete(self):
        """Vérifie si tous les combats de cette phase sont terminés."""
        return not self.combats.filter(status__in=['planifie', 'en_cours']).exists()

    def get_vainqueur(self):
        """
        Retourne le vainqueur de la phase (pour la finale uniquement).
        """
        if self.phase != 'finale':
            return None

        finale = self.combats.filter(status='termine').first()
        if finale:
            return finale.vainqueur
        return None

    def get_perdant_finale(self):
        """Retourne le perdant de la finale (2ème place)."""
        if self.phase != 'finale':
            return None

        finale = self.combats.filter(status='termine').first()
        if finale:
            return finale.perdant
        return None


class CombatPhaseFinale(models.Model):
    """
    Combat de phase finale.
    Extension du modèle Combat pour les phases éliminatoires.
    """
    phase_finale = models.ForeignKey(
        PhaseFinale,
        on_delete=models.CASCADE,
        related_name='combats',
        verbose_name=_("Phase finale")
    )

    combat = models.OneToOneField(
        Combat,
        on_delete=models.CASCADE,
        related_name='info_phase_finale',
        verbose_name=_("Combat")
    )

    # Position dans le bracket
    ordre = models.PositiveSmallIntegerField(
        _("Ordre"),
        default=0,
        help_text=_("Position dans le bracket (1 = premier match)")
    )

    # Qualifications depuis les poules
    equipe1_source = models.CharField(
        _("Source équipe 1"),
        max_length=50,
        blank=True,
        help_text=_("Ex: '1er Poule A' ou 'Vainqueur QF1'")
    )
    equipe2_source = models.CharField(
        _("Source équipe 2"),
        max_length=50,
        blank=True,
        help_text=_("Ex: '2ème Poule B' ou 'Perdant DF1'")
    )

    # Lien vers le combat suivant
    combat_suivant = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='combats_precedents',
        verbose_name=_("Combat suivant")
    )

    is_active = models.BooleanField(_("Actif"), default=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Combat de phase finale")
        verbose_name_plural = _("Combats de phases finales")
        ordering = ['phase_finale', 'ordre']

    def __str__(self):
        return f"{self.phase_finale.get_phase_display()} #{self.ordre} - {self.combat}"

    def get_equipe1_display(self):
        """Affiche l'équipe 1 ou sa source si pas encore déterminée."""
        if self.combat.equipe1:
            return self.combat.equipe1.nom
        return self.equipe1_source or "À déterminer"

    def get_equipe2_display(self):
        """Affiche l'équipe 2 ou sa source si pas encore déterminée."""
        if self.combat.equipe2:
            return self.combat.equipe2.nom
        return self.equipe2_source or "À déterminer"


class PodiumEquipe(models.Model):
    """
    Sprint 3 REQ-05: Podium complet pour les compétitions par équipes.

    Enregistre le classement final avec toutes les informations
    nécessaires pour l'affichage (équipe, club, membres, statistiques).
    """
    PLACE_CHOICES = [
        (1, _('1ère place - Or')),
        (2, _('2ème place - Argent')),
        (3, _('3ème place - Bronze')),
        (4, _('4ème place')),
        (5, _('5ème place')),
    ]

    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='podiums_equipes',
        verbose_name=_("Compétition")
    )

    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='podiums',
        verbose_name=_("Équipe")
    )

    place = models.PositiveSmallIntegerField(
        _("Place"),
        choices=PLACE_CHOICES
    )

    # Statistiques de l'équipe
    victoires = models.PositiveSmallIntegerField(_("Victoires"), default=0)
    defaites = models.PositiveSmallIntegerField(_("Défaites"), default=0)
    nuls = models.PositiveSmallIntegerField(_("Matchs nuls"), default=0)
    points_marques = models.PositiveIntegerField(_("Points marqués"), default=0)
    points_encaisses = models.PositiveIntegerField(_("Points encaissés"), default=0)

    # Détails des membres ayant participé
    membres_details = models.JSONField(
        _("Détails des membres"),
        default=dict,
        blank=True,
        help_text=_("JSON avec détails de chaque membre (nom, rôle, stats)")
    )

    # Si l'équipe était une fusion
    is_fusion = models.BooleanField(_("Équipe fusionnée"), default=False)
    clubs_partenaires = models.CharField(
        _("Clubs partenaires"),
        max_length=255,
        blank=True,
        help_text=_("Liste des clubs si équipe multi-clubs")
    )

    # Tracking
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Podium équipe")
        verbose_name_plural = _("Podiums équipes")
        ordering = ['competition', 'place']
        unique_together = [['competition', 'place']]

    def __str__(self):
        return f"{self.get_place_display()} - {self.equipe.nom}"

    @property
    def difference_points(self):
        """Calcule la différence de points."""
        return self.points_marques - self.points_encaisses

    @property
    def total_combats(self):
        """Nombre total de combats joués."""
        return self.victoires + self.defaites + self.nuls

    def get_medaille_icon(self):
        """Retourne l'emoji de médaille correspondant."""
        icons = {
            1: '🥇',
            2: '🥈',
            3: '🥉',
        }
        return icons.get(self.place, '')

    def get_medaille_color(self):
        """Retourne la couleur CSS de la médaille."""
        colors = {
            1: '#FFD700',  # Or
            2: '#C0C0C0',  # Argent
            3: '#CD7F32',  # Bronze
        }
        return colors.get(self.place, '#666')

    def populate_membres_details(self):
        """
        Remplit les détails des membres depuis l'équipe.
        À appeler lors de la création du podium.
        """
        membres_data = []
        for membre in self.equipe.membres.all():
            data = {
                'id': membre.pratiquant.id,
                'nom': membre.pratiquant.full_name,
                'role': membre.role,
                'is_entente': membre.is_entente,
                'club_origine': membre.club_origine.nom if membre.club_origine else None,
                'a_combattu': membre.a_combattu,
            }
            membres_data.append(data)

        self.membres_details = {'membres': membres_data}
        self.is_fusion = self.equipe.is_fusion

        # Clubs partenaires si fusion
        if self.equipe.is_fusion:
            clubs = set()
            clubs.add(self.equipe.club.nom)
            for m in self.equipe.membres.filter(is_entente=True):
                if m.club_origine:
                    clubs.add(m.club_origine.nom)
            self.clubs_partenaires = ', '.join(sorted(clubs))

        self.save()


# =============================================================================
# MODE KIOSQUE: Aires de Combat (Multi-Tatami)
# =============================================================================

class AireCombat(models.Model):
    """
    Aire de combat (tatami) pour le mode kiosque.

    Permet de gérer plusieurs aires de combat pendant une compétition,
    chacune protégée par un code PIN et assignée à des catégories spécifiques.

    Fonctionnalités:
    - Accès sans authentification utilisateur via URL publique + PIN
    - Chaque aire a ses propres catégories assignées
    - Le manager peut générer/régénérer le PIN
    - Interface simplifiée pour les arbitres sur chaque tatami
    """

    competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        related_name='aires_combat',
        verbose_name=_("Compétition")
    )

    nom = models.CharField(
        _("Nom de l'aire"),
        max_length=50,
        help_text=_("Ex: Tatami 1, Aire A, Zone Combat 1")
    )

    numero = models.PositiveSmallIntegerField(
        _("Numéro"),
        default=1,
        help_text=_("Numéro d'ordre de l'aire")
    )

    # Code PIN pour l'accès (4-6 chiffres)
    pin_code = models.CharField(
        _("Code PIN"),
        max_length=6,
        help_text=_("Code PIN à 4-6 chiffres pour accéder à cette aire")
    )

    # Token unique pour l'URL d'accès
    access_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        help_text=_("Token unique pour l'URL d'accès")
    )

    # Catégories assignées à cette aire
    categories = models.ManyToManyField(
        'competitions.CompetitionCategory',
        related_name='aires_combat',
        verbose_name=_("Catégories assignées"),
        blank=True
    )

    # Statut de l'aire
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Si désactivée, l'aire n'est plus accessible")
    )

    # Couleur pour l'identification visuelle
    COLOR_CHOICES = [
        ('blue', _('Bleu')),
        ('red', _('Rouge')),
        ('green', _('Vert')),
        ('yellow', _('Jaune')),
        ('purple', _('Violet')),
        ('orange', _('Orange')),
        ('teal', _('Turquoise')),
        ('pink', _('Rose')),
    ]
    couleur = models.CharField(
        _("Couleur extérieure"),
        max_length=20,
        choices=COLOR_CHOICES,
        default='blue',
        help_text=_("Couleur extérieure du tatami")
    )
    couleur_interieur = models.CharField(
        _("Couleur intérieure"),
        max_length=20,
        choices=COLOR_CHOICES,
        default='red',
        help_text=_("Couleur intérieure du tatami")
    )

    # Description/notes optionnelles
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Notes ou instructions spécifiques pour cette aire")
    )

    # Tracking
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    last_accessed = models.DateTimeField(
        _("Dernier accès"),
        null=True,
        blank=True,
        help_text=_("Dernière fois que quelqu'un s'est connecté à cette aire")
    )

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Aire de combat")
        verbose_name_plural = _("Aires de combat")
        ordering = ['competition', 'numero']
        unique_together = [['competition', 'numero']]

    def __str__(self):
        return f"{self.nom} - {self.competition.title}"

    def save(self, *args, **kwargs):
        """Génère un PIN si non défini."""
        if not self.pin_code:
            self.generate_pin()
        super().save(*args, **kwargs)

    def generate_pin(self, length=4):
        """Génère un nouveau code PIN aléatoire."""
        import random
        self.pin_code = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        return self.pin_code

    def regenerate_access(self):
        """Régénère le token et le PIN pour cette aire."""
        self.access_token = uuid.uuid4()
        self.generate_pin()
        self.save(update_fields=['access_token', 'pin_code', 'updated_at'])

    def verify_pin(self, entered_pin):
        """Vérifie si le PIN entré est correct."""
        return self.pin_code == entered_pin

    def record_access(self):
        """Enregistre un accès à cette aire."""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])

    def get_absolute_url(self):
        """Retourne l'URL publique de l'aire."""
        from django.urls import reverse
        return reverse('competitions:combat:aire_kiosque_login', kwargs={'token': str(self.access_token)})

    def get_assigned_combats(self, status=None):
        """
        Retourne les combats des catégories assignées à cette aire.

        Args:
            status: Filtrer par statut (optionnel)

        Returns:
            QuerySet de Combat
        """
        from apps.competitions.models import Combat

        # Récupérer les combats liés aux catégories assignées
        category_ids = self.categories.values_list('id', flat=True)

        combats = Combat.objects.filter(
            competition=self.competition
        ).filter(
            # Combats dont la poule est liée à une catégorie assignée
            # OU combats avec des équipes dans ces catégories
            models.Q(poule__category_id__in=category_ids) |
            models.Q(equipe_rouge__category_id__in=category_ids) |
            models.Q(equipe_blanc__category_id__in=category_ids)
        ).distinct()

        if status:
            combats = combats.filter(status=status)

        return combats.order_by('date_planifiee', 'id')

    def get_pending_combats(self):
        """Retourne les combats planifiés."""
        return self.get_assigned_combats(status='planifie')

    def get_active_combats(self):
        """Retourne les combats en cours."""
        return self.get_assigned_combats(status='en_cours')

    def get_completed_combats(self):
        """Retourne les combats terminés."""
        return self.get_assigned_combats(status='termine')

    @property
    def stats(self):
        """Statistiques de l'aire."""
        return {
            'categories_count': self.categories.count(),
            'pending_combats': self.get_pending_combats().count(),
            'active_combats': self.get_active_combats().count(),
            'completed_combats': self.get_completed_combats().count(),
        }

    @property
    def color_hex(self):
        """Retourne le code couleur hexadécimal."""
        colors = {
            'blue': '#3B82F6',
            'red': '#EF4444',
            'green': '#10B981',
            'yellow': '#F59E0B',
            'purple': '#8B5CF6',
            'orange': '#F97316',
            'teal': '#14B8A6',
            'pink': '#EC4899',
        }
        return colors.get(self.couleur, '#3B82F6')

    @property
    def color_inner_hex(self):
        """Retourne le code couleur intérieure hexadécimal."""
        colors = {
            'blue': '#3B82F6', 'red': '#EF4444', 'green': '#10B981',
            'yellow': '#F59E0B', 'purple': '#8B5CF6', 'orange': '#F97316',
            'teal': '#14B8A6', 'pink': '#EC4899',
        }
        return colors.get(self.couleur_interieur, '#EF4444')


class AireCombatSession(models.Model):
    """
    Session active sur une aire de combat.

    Permet de tracer qui utilise l'aire et quand, ainsi que
    de gérer les sessions multiples si nécessaire.
    """

    aire = models.ForeignKey(
        AireCombat,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_("Aire de combat")
    )

    # Identifiant de session (stocké en cookie côté client)
    session_token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    # Informations sur le client
    ip_address = models.GenericIPAddressField(
        _("Adresse IP"),
        null=True,
        blank=True
    )
    user_agent = models.CharField(
        _("User Agent"),
        max_length=255,
        blank=True
    )

    # Timing
    started_at = models.DateTimeField(_("Démarré le"), auto_now_add=True)
    last_activity = models.DateTimeField(_("Dernière activité"), auto_now=True)
    ended_at = models.DateTimeField(_("Terminé le"), null=True, blank=True)

    # Statut
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        app_label = 'competitions'
        verbose_name = _("Session d'aire")
        verbose_name_plural = _("Sessions d'aires")
        ordering = ['-started_at']

    def __str__(self):
        return f"Session {self.aire.nom} - {self.started_at.strftime('%H:%M')}"

    def end_session(self):
        """Termine la session."""
        self.is_active = False
        self.ended_at = timezone.now()
        self.save(update_fields=['is_active', 'ended_at'])

    def update_activity(self):
        """Met à jour le timestamp de dernière activité."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])

    @property
    def duration(self):
        """Durée de la session en minutes."""
        end = self.ended_at or timezone.now()
        delta = end - self.started_at
        return int(delta.total_seconds() / 60)

