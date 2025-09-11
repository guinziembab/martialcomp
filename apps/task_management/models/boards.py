from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class BoardType(models.TextChoices):
    """Types of boards available in the system"""
    GENERAL = 'general', _('Général')
    COMPETITION = 'competition', _('Compétition')
    TRAINING = 'training', _('Entraînement')
    FEDERATION = 'federation', _('Fédération')
    CLUB = 'club', _('Club')
    EVENT = 'event', _('Événement')


class Board(models.Model):
    """
    Main Kanban Board model
    Represents a project or workflow board that contains columns and tasks
    """
    name = models.CharField(_("Nom"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    
    # Multi-tenant relations
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='boards',
        verbose_name=_("Organisation")
    )
    
    # Board type and context
    board_type = models.CharField(
        _("Type de tableau"),
        max_length=20,
        choices=BoardType.choices,
        default=BoardType.GENERAL
    )
    
    # Optional relations based on context
    related_competition = models.ForeignKey(
        'competitions.Competition',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='boards',
        verbose_name=_("Compétition associée")
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_boards',
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Configuration
    is_template = models.BooleanField(_("Est un template"), default=False)
    is_archived = models.BooleanField(_("Archivé"), default=False)
    color_theme = models.CharField(_("Thème de couleur"), max_length=20, default='blue')
    
    # Access permissions
    is_public = models.BooleanField(_("Public dans l'organisation"), default=False)
    allowed_roles = models.JSONField(
        _("Rôles autorisés"),
        default=list,
        help_text=_("Liste des rôles d'organisation autorisés à accéder au board")
    )
    
    # Board settings
    enable_time_tracking = models.BooleanField(_("Suivi du temps activé"), default=True)
    enable_comments = models.BooleanField(_("Commentaires activés"), default=True)
    enable_attachments = models.BooleanField(_("Pièces jointes activées"), default=True)
    
    class Meta:
        verbose_name = _("Tableau Kanban")
        verbose_name_plural = _("Tableaux Kanban")
        ordering = ['-created_at']
        unique_together = ['organization', 'name']
        indexes = [
            models.Index(fields=['organization', 'board_type']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_archived', 'is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.organization.name})"
    
    def can_access(self, user):
        """Check if a user can access this board"""
        if not user.is_authenticated:
            return False
            
        # Board owner always has access
        if self.created_by == user:
            return True
            
        # Check organization membership and roles
        try:
            from apps.organizations.models import OrganizationMember
            membership = OrganizationMember.objects.get(
                user=user, 
                organization=self.organization,
                is_active=True
            )
            
            # Public boards are accessible to all organization members
            if self.is_public:
                return True
                
            # Check specific role permissions
            if not self.allowed_roles:
                # Default: only owners and admins
                return membership.role in ['owner', 'admin']
                
            return membership.role in self.allowed_roles
            
        except ImportError:
            # Fallback if organizations app is not available
            return user.is_staff or user.is_superuser
        except:
            return False
    
    def can_edit(self, user):
        """Check if a user can edit this board"""
        if not self.can_access(user):
            return False
            
        # Board owner can always edit
        if self.created_by == user:
            return True
            
        try:
            from apps.organizations.models import OrganizationMember
            membership = OrganizationMember.objects.get(
                user=user, 
                organization=self.organization,
                is_active=True
            )
            
            # Owners and admins can edit
            return membership.role in ['owner', 'admin']
            
        except:
            return user.is_staff or user.is_superuser
    
    @property
    def task_count(self):
        """Get total number of tasks in this board"""
        return self.tasks.count()
    
    @property
    def completed_task_count(self):
        """Get number of completed tasks"""
        return self.tasks.filter(status='done').count()
    
    @property
    def progress_percentage(self):
        """Calculate completion percentage"""
        total = self.task_count
        if total == 0:
            return 0
        completed = self.completed_task_count
        return round((completed / total) * 100, 1)


class Column(models.Model):
    """
    Kanban Board Columns
    Represents workflow stages in a board
    """
    name = models.CharField(_("Nom"), max_length=100)
    board = models.ForeignKey(
        Board,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name=_("Tableau")
    )
    position = models.PositiveIntegerField(_("Position"))
    color = models.CharField(_("Couleur"), max_length=7, default='#6B7280')
    
    # WIP (Work In Progress) limits
    wip_limit = models.PositiveIntegerField(
        _("Limite WIP"),
        null=True, blank=True,
        help_text=_("Nombre maximum de tâches dans cette colonne")
    )
    
    # Column behavior settings
    is_done_column = models.BooleanField(
        _("Colonne de fin"),
        default=False,
        help_text=_("Les tâches dans cette colonne sont considérées comme terminées")
    )
    
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    
    class Meta:
        verbose_name = _("Colonne")
        verbose_name_plural = _("Colonnes")
        ordering = ['position']
        unique_together = ['board', 'position']
        indexes = [
            models.Index(fields=['board', 'position']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.board.name})"
    
    @property
    def task_count(self):
        """Get number of tasks in this column"""
        return self.tasks.count()
    
    @property
    def is_over_wip_limit(self):
        """Check if column is over WIP limit"""
        if not self.wip_limit:
            return False
        return self.task_count > self.wip_limit
    
    def get_wip_status(self):
        """Get WIP status for UI display"""
        if not self.wip_limit:
            return 'no_limit'
        
        count = self.task_count
        if count > self.wip_limit:
            return 'over_limit'
        elif count == self.wip_limit:
            return 'at_limit'
        else:
            return 'under_limit'