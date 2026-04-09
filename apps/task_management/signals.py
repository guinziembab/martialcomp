import logging
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.db import models

from .models import Board, Task, Column, TaskComment, TaskAssignment

logger = logging.getLogger(__name__)


# =============================================================================
# CACHE INVALIDATION SIGNALS
# =============================================================================

@receiver(post_save, sender=Board)
def board_post_save(sender, instance, created, **kwargs):
    """Handle board creation and updates"""
    # Invalidate cache
    cache_key = f'board_{instance.id}_detail'
    cache.delete(cache_key)

    # Create default columns for new boards if none exist
    if created and not instance.columns.exists():
        default_columns = [
            {'name': 'À faire', 'position': 1, 'color': '#EF4444'},
            {'name': 'En cours', 'position': 2, 'color': '#F59E0B'},
            {'name': 'En révision', 'position': 3, 'color': '#3B82F6'},
            {'name': 'Terminé', 'position': 4, 'color': '#10B981', 'is_done_column': True}
        ]

        for col_data in default_columns:
            Column.objects.create(board=instance, **col_data)


@receiver(post_delete, sender=Board)
def board_post_delete(sender, instance, **kwargs):
    """Clean up after board deletion"""
    cache_key = f'board_{instance.id}_detail'
    cache.delete(cache_key)


@receiver(post_save, sender=Task)
def task_post_save(sender, instance, created, **kwargs):
    """Handle task creation and updates"""
    # Invalidate board cache
    cache_key = f'board_{instance.board.id}_detail'
    cache.delete(cache_key)

    # Set position for new tasks
    if created and instance.position == 0:
        max_position = Task.objects.filter(
            column=instance.column
        ).exclude(id=instance.id).aggregate(
            max_pos=models.Max('position')
        )['max_pos'] or 0

        instance.position = max_position + 1
        instance.save(update_fields=['position'])


@receiver(pre_delete, sender=Task)
def task_pre_delete(sender, instance, **kwargs):
    """Handle task deletion - reorder positions"""
    Task.objects.filter(
        column=instance.column,
        position__gt=instance.position
    ).update(position=models.F('position') - 1)


@receiver(post_delete, sender=Task)
def task_post_delete(sender, instance, **kwargs):
    """Clean up after task deletion"""
    cache_key = f'board_{instance.board.id}_detail'
    cache.delete(cache_key)


@receiver(post_save, sender=TaskComment)
def task_comment_post_save(sender, instance, created, **kwargs):
    """Handle comment creation"""
    if created:
        cache_key = f'task_{instance.task.id}_comments'
        cache.delete(cache_key)


# =============================================================================
# TASK NOTIFICATION SIGNALS
# =============================================================================

def _create_task_notification(user, title, message, action_url=None, priority='standard', notification_type='info'):
    """Helper to create a notification for a user about a task event."""
    try:
        from apps.competitions.models.notifications import Notification
        Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            action_url=action_url,
            action_text='Voir la tâche' if action_url else None,
        )
    except Exception as e:
        logger.warning(f"Failed to create task notification for {user}: {e}")


def _get_task_url(task):
    """Build absolute URL for a task detail page."""
    try:
        from django.urls import reverse
        return reverse('task_management:task_detail', kwargs={'task_id': task.id})
    except Exception:
        return None


@receiver(post_save, sender=TaskAssignment)
def task_assignment_notify(sender, instance, created, **kwargs):
    """Notify user when assigned to a task."""
    if not created:
        return

    task = instance.task
    assignee = instance.assignee
    assigned_by = instance.assigned_by

    # Don't notify if user assigned themselves
    if assignee == assigned_by:
        return

    assigner_name = assigned_by.get_full_name() or assigned_by.username if assigned_by else 'Quelqu\'un'
    board_name = task.board.name
    role_display = instance.get_role_display()

    title = f"Nouvelle tâche assignée : {task.title}"
    message = (
        f"{assigner_name} vous a assigné la tâche « {task.title} » "
        f"({role_display}) dans le tableau « {board_name} »."
    )

    if task.due_date:
        from django.utils.formats import date_format
        message += f"\nÉchéance : {date_format(task.due_date, 'd/m/Y à H:i')}"

    _create_task_notification(
        user=assignee,
        title=title,
        message=message,
        action_url=_get_task_url(task),
        priority='important',
        notification_type='info',
    )
    logger.info(f"Task assignment notification sent to {assignee.username} for task #{task.id}")


@receiver(post_save, sender=TaskComment)
def task_comment_notify(sender, instance, created, **kwargs):
    """Notify task assignees and creator when a comment is added."""
    if not created:
        return

    task = instance.task
    author = instance.author
    author_name = author.get_full_name() or author.username

    # Collect users to notify (assignees + creator), excluding comment author
    users_to_notify = set()

    # Task creator
    if task.created_by and task.created_by != author:
        users_to_notify.add(task.created_by)

    # Active assignees who want comment notifications
    for assignment in task.assignments.filter(is_active=True, notify_on_comments=True):
        if assignment.assignee != author:
            users_to_notify.add(assignment.assignee)

    if not users_to_notify:
        return

    title = f"Nouveau commentaire sur « {task.title} »"
    preview = instance.content[:100] + ('...' if len(instance.content) > 100 else '')
    message = f"{author_name} a commenté : {preview}"

    task_url = _get_task_url(task)
    for user in users_to_notify:
        _create_task_notification(
            user=user,
            title=title,
            message=message,
            action_url=task_url,
            priority='standard',
            notification_type='info',
        )

    logger.info(f"Comment notification sent to {len(users_to_notify)} users for task #{task.id}")


@receiver(post_save, sender=Task)
def task_status_change_notify(sender, instance, created, **kwargs):
    """Notify assignees when task status changes."""
    if created:
        return

    # Check if status actually changed by comparing with update_fields
    update_fields = kwargs.get('update_fields')
    if update_fields and 'status' not in update_fields and 'position' in update_fields:
        return

    # We need to detect status change. Use a simple approach:
    # only notify when status is DONE (completion) since we can't easily
    # track the old value without additional overhead
    if instance.status != 'done':
        return

    task = instance
    completer_name = ''

    # Notify task creator if they're not the one who completed it
    users_to_notify = set()
    if task.created_by:
        users_to_notify.add(task.created_by)

    for assignment in task.assignments.filter(is_active=True, notify_on_updates=True):
        users_to_notify.add(assignment.assignee)

    if not users_to_notify:
        return

    title = f"Tâche terminée : {task.title}"
    message = f"La tâche « {task.title} » dans le tableau « {task.board.name} » a été marquée comme terminée."

    task_url = _get_task_url(task)
    for user in users_to_notify:
        _create_task_notification(
            user=user,
            title=title,
            message=message,
            action_url=task_url,
            priority='standard',
            notification_type='success',
        )

    logger.info(f"Task completion notification sent for task #{task.id}")
