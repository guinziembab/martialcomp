from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class TaskAssignment(models.Model):
    """
    Task Assignment model
    Manages user assignments to tasks with roles and permissions
    """
    task = models.ForeignKey(
        'task_management.Task',
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name=_("Tâche")
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='task_assignments',
        verbose_name=_("Assigné")
    )
    
    # Assignment metadata
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assignments_made',
        verbose_name=_("Assigné par")
    )
    assigned_at = models.DateTimeField(_("Assigné le"), auto_now_add=True)
    
    # Assignment role/type
    class AssignmentRole(models.TextChoices):
        ASSIGNEE = 'assignee', _('Assigné')
        REVIEWER = 'reviewer', _('Réviseur')
        WATCHER = 'watcher', _('Observateur')
        COLLABORATOR = 'collaborator', _('Collaborateur')
    
    role = models.CharField(
        _("Rôle"),
        max_length=15,
        choices=AssignmentRole.choices,
        default=AssignmentRole.ASSIGNEE
    )
    
    # Assignment status
    is_active = models.BooleanField(_("Actif"), default=True)
    
    # Notification preferences
    notify_on_updates = models.BooleanField(_("Notifier des mises à jour"), default=True)
    notify_on_comments = models.BooleanField(_("Notifier des commentaires"), default=True)
    notify_on_due_date = models.BooleanField(_("Notifier de l'échéance"), default=True)
    
    class Meta:
        verbose_name = _("Assignation de tâche")
        verbose_name_plural = _("Assignations de tâches")
        unique_together = ['task', 'assignee', 'role']
        indexes = [
            models.Index(fields=['task', 'is_active']),
            models.Index(fields=['assignee', 'is_active']),
            models.Index(fields=['assigned_at']),
        ]
    
    def __str__(self):
        return f"{self.assignee.get_full_name()} - {self.task.title} ({self.get_role_display()})"
    
    @property
    def can_edit_task(self):
        """Check if this assignment allows task editing"""
        return self.role in [self.AssignmentRole.ASSIGNEE, self.AssignmentRole.COLLABORATOR]
    
    @property
    def can_review_task(self):
        """Check if this assignment allows task review"""
        return self.role in [self.AssignmentRole.REVIEWER, self.AssignmentRole.ASSIGNEE]