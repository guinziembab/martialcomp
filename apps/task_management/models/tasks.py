from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class TaskPriority(models.TextChoices):
    """Task priority levels"""
    LOW = 'low', _('Basse')
    MEDIUM = 'medium', _('Moyenne')
    HIGH = 'high', _('Haute')
    URGENT = 'urgent', _('Urgente')


class TaskStatus(models.TextChoices):
    """Task status options"""
    TODO = 'todo', _('À faire')
    IN_PROGRESS = 'in_progress', _('En cours')
    IN_REVIEW = 'in_review', _('En révision')
    DONE = 'done', _('Terminé')
    BLOCKED = 'blocked', _('Bloqué')


class Task(models.Model):
    """
    Kanban Task model
    Represents individual work items that can be moved between columns
    """
    title = models.CharField(_("Titre"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    # Board relations
    board = models.ForeignKey(
        'task_management.Board',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_("Tableau")
    )
    column = models.ForeignKey(
        'task_management.Column',
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name=_("Colonne")
    )
    
    # Task properties
    priority = models.CharField(
        _("Priorité"),
        max_length=10,
        choices=TaskPriority.choices,
        default=TaskPriority.MEDIUM
    )
    status = models.CharField(
        _("Statut"),
        max_length=15,
        choices=TaskStatus.choices,
        default=TaskStatus.TODO
    )
    
    # Dates and timing
    due_date = models.DateTimeField(_("Date d'échéance"), null=True, blank=True)
    start_date = models.DateTimeField(_("Date de début"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Terminé le"), null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks',
        verbose_name=_("Créé par")
    )
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    
    # Position in column for ordering
    position = models.PositiveIntegerField(_("Position"), default=0)
    
    # Time tracking
    estimated_hours = models.DecimalField(
        _("Heures estimées"),
        max_digits=5, decimal_places=2,
        null=True, blank=True
    )
    time_spent = models.DecimalField(
        _("Temps passé"),
        max_digits=5, decimal_places=2,
        default=0
    )
    
    # Hierarchy - subtasks
    parent_task = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='subtasks',
        verbose_name=_("Tâche parent")
    )
    
    # File attachments (stored as URLs/paths)
    attachments = models.JSONField(
        _("Pièces jointes"),
        default=list,
        help_text=_("URLs des fichiers attachés")
    )
    
    # Labels and tags
    labels = models.JSONField(
        _("Étiquettes"),
        default=list,
        help_text=_("Tags et labels pour la catégorisation")
    )
    
    # Additional context data
    custom_fields = models.JSONField(
        _("Champs personnalisés"),
        default=dict,
        help_text=_("Données contextuelles supplémentaires")
    )
    
    class Meta:
        verbose_name = _("Tâche")
        verbose_name_plural = _("Tâches")
        ordering = ['column__position', 'position', 'created_at']
        indexes = [
            models.Index(fields=['board', 'column']),
            models.Index(fields=['created_by']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['due_date']),
            models.Index(fields=['parent_task']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.board.name})"
    
    def save(self, *args, **kwargs):
        """Override save to handle status changes"""
        # Auto-set completed_at when task is marked as done
        if self.status == TaskStatus.DONE and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status != TaskStatus.DONE and self.completed_at:
            self.completed_at = None
            
        # Update status based on column type
        if hasattr(self.column, 'is_done_column') and self.column.is_done_column:
            self.status = TaskStatus.DONE
            
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if task is overdue"""
        if not self.due_date or self.status == TaskStatus.DONE:
            return False
        return timezone.now() > self.due_date
    
    @property
    def days_until_due(self):
        """Calculate days until due date"""
        if not self.due_date:
            return None
        
        delta = self.due_date.date() - timezone.now().date()
        return delta.days
    
    def get_progress_percentage(self):
        """Calculate progress percentage based on subtasks"""
        subtasks = self.subtasks.all()
        if not subtasks:
            return 100 if self.status == TaskStatus.DONE else 0
            
        completed = subtasks.filter(status=TaskStatus.DONE).count()
        return round((completed / subtasks.count()) * 100, 1)
    
    @property
    def has_subtasks(self):
        """Check if task has subtasks"""
        return self.subtasks.exists()
    
    @property
    def assignee_count(self):
        """Get number of assignees"""
        return self.assignments.count()
    
    def get_assignees(self):
        """Get list of assigned users"""
        return [assignment.assignee for assignment in self.assignments.all()]
    
    def is_assigned_to(self, user):
        """Check if user is assigned to this task"""
        return self.assignments.filter(assignee=user).exists()
    
    def can_edit(self, user):
        """Check if user can edit this task"""
        # Check board permissions first
        if not self.board.can_edit(user):
            return False
            
        # Task creator can edit
        if self.created_by == user:
            return True
            
        # Assigned users can edit
        if self.is_assigned_to(user):
            return True
            
        return False
    
    def get_priority_color(self):
        """Get color code for priority level"""
        colors = {
            TaskPriority.LOW: '#10B981',      # Green
            TaskPriority.MEDIUM: '#F59E0B',   # Yellow
            TaskPriority.HIGH: '#EF4444',     # Red
            TaskPriority.URGENT: '#DC2626',   # Dark Red
        }
        return colors.get(self.priority, '#6B7280')
    
    def get_status_color(self):
        """Get color code for status"""
        colors = {
            TaskStatus.TODO: '#6B7280',       # Gray
            TaskStatus.IN_PROGRESS: '#3B82F6', # Blue
            TaskStatus.IN_REVIEW: '#8B5CF6',   # Purple
            TaskStatus.DONE: '#10B981',        # Green
            TaskStatus.BLOCKED: '#EF4444',     # Red
        }
        return colors.get(self.status, '#6B7280')


class TaskComment(models.Model):
    """
    Comments on tasks for collaboration
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_("Tâche")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Auteur")
    )
    content = models.TextField(_("Contenu"))
    
    # Comment metadata
    created_at = models.DateTimeField(_("Créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Mis à jour le"), auto_now=True)
    is_edited = models.BooleanField(_("Modifié"), default=False)
    
    # Optional parent for threaded comments
    parent_comment = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies',
        verbose_name=_("Commentaire parent")
    )
    
    class Meta:
        verbose_name = _("Commentaire")
        verbose_name_plural = _("Commentaires")
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.task.title}"
    
    def save(self, *args, **kwargs):
        """Mark as edited if content changes"""
        if self.pk:
            original = TaskComment.objects.get(pk=self.pk)
            if original.content != self.content:
                self.is_edited = True
        super().save(*args, **kwargs)
    
    @property
    def is_reply(self):
        """Check if this is a reply to another comment"""
        return self.parent_comment is not None
    
    def can_edit(self, user):
        """Check if user can edit this comment"""
        return self.author == user or self.task.board.can_edit(user)