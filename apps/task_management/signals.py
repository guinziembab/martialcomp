from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Board, Task, Column, TaskComment


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
    # Invalidate cache
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
        # Get the highest position in the column
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
    # Reorder other tasks in the same column
    Task.objects.filter(
        column=instance.column,
        position__gt=instance.position
    ).update(position=models.F('position') - 1)


@receiver(post_delete, sender=Task)
def task_post_delete(sender, instance, **kwargs):
    """Clean up after task deletion"""
    # Invalidate board cache
    cache_key = f'board_{instance.board.id}_detail'
    cache.delete(cache_key)


@receiver(post_save, sender=TaskComment)
def task_comment_post_save(sender, instance, created, **kwargs):
    """Handle comment creation"""
    if created:
        # Invalidate task cache
        cache_key = f'task_{instance.task.id}_comments'
        cache.delete(cache_key)


# Import models for the signals
from django.db import models