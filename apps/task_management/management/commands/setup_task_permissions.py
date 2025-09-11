from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

from apps.task_management.models import Board, Task, Column, TaskComment, TaskAssignment


class Command(BaseCommand):
    help = 'Set up custom permissions for task management'
    
    def handle(self, *args, **options):
        # Custom permissions to create
        custom_permissions = [
            # Board permissions
            ('view_board_stats', Board, 'Can view board statistics'),
            ('export_board', Board, 'Can export board data'),
            ('archive_board', Board, 'Can archive/unarchive boards'),
            ('manage_board_members', Board, 'Can manage board member access'),
            
            # Task permissions
            ('move_task', Task, 'Can move tasks between columns'),
            ('assign_task', Task, 'Can assign tasks to users'),
            ('manage_task_time', Task, 'Can manage task time tracking'),
            
            # Column permissions
            ('reorder_columns', Column, 'Can reorder board columns'),
            ('set_wip_limits', Column, 'Can set WIP limits on columns'),
            
            # Comment permissions
            ('moderate_comments', TaskComment, 'Can moderate task comments'),
        ]
        
        created_count = 0
        
        for codename, model, name in custom_permissions:
            content_type = ContentType.objects.get_for_model(model)
            
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created permission: {codename}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Permission already exists: {codename}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted: {created_count} permissions created')
        )