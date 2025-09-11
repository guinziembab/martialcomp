from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


def check_board_access(user, board, permission='view'):
    """
    Check if user has specific permission on board
    
    Args:
        user: User instance
        board: Board instance  
        permission: 'view', 'edit', 'admin'
    """
    if not user.is_authenticated:
        return False
    
    # Superuser has all permissions
    if user.is_superuser:
        return True
    
    # Board creator has all permissions
    if board.created_by == user:
        return True
    
    # Check organization membership
    try:
        from apps.organizations.models import OrganizationMember
        membership = OrganizationMember.objects.get(
            user=user,
            organization=board.organization,
            is_active=True
        )
        
        # Admin permission check
        if permission == 'admin':
            return membership.role in ['owner', 'admin']
        
        # Edit permission check  
        if permission == 'edit':
            if board.is_public:
                return membership.role in ['owner', 'admin', 'manager']
            else:
                if not board.allowed_roles:
                    return membership.role in ['owner', 'admin']
                return membership.role in board.allowed_roles
        
        # View permission check (default)
        if board.is_public:
            return True
        else:
            if not board.allowed_roles:
                return membership.role in ['owner', 'admin']
            return membership.role in board.allowed_roles
            
    except ImportError:
        # Fallback if organizations app not available
        return user.is_staff
    except:
        return False


def get_user_organizations(user):
    """Get organizations that user belongs to"""
    if not user.is_authenticated:
        return []
    
    try:
        from apps.organizations.models import OrganizationMember
        return OrganizationMember.objects.filter(
            user=user,
            is_active=True
        ).values_list('organization', flat=True)
    except ImportError:
        return []


def get_user_boards(user, include_archived=False):
    """Get boards accessible to user"""
    from .models import Board
    
    if not user.is_authenticated:
        return Board.objects.none()
    
    user_orgs = get_user_organizations(user)
    queryset = Board.objects.filter(organization__in=user_orgs)
    
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    
    return queryset.select_related('organization', 'created_by')


def get_board_statistics(board):
    """Get comprehensive board statistics"""
    cache_key = f'board_stats_{board.id}'
    stats = cache.get(cache_key)
    
    if stats is None:
        from .models import TaskStatus
        
        tasks = board.tasks.all()
        total_tasks = tasks.count()
        
        if total_tasks == 0:
            stats = {
                'total_tasks': 0,
                'completed_tasks': 0,
                'in_progress_tasks': 0,
                'overdue_tasks': 0,
                'completion_rate': 0,
                'average_completion_time': None,
                'tasks_by_priority': {},
                'tasks_by_status': {},
            }
        else:
            completed_tasks = tasks.filter(status=TaskStatus.DONE)
            overdue_tasks = tasks.filter(
                due_date__lt=timezone.now(),
                status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
            )
            
            # Calculate average completion time
            completed_with_time = completed_tasks.filter(
                completed_at__isnull=False,
                created_at__isnull=False
            )
            
            if completed_with_time.exists():
                total_time = sum([
                    (task.completed_at - task.created_at).total_seconds()
                    for task in completed_with_time
                ])
                avg_seconds = total_time / completed_with_time.count()
                avg_completion_time = timedelta(seconds=avg_seconds)
            else:
                avg_completion_time = None
            
            # Tasks by priority
            from .models import TaskPriority
            tasks_by_priority = {}
            for priority in TaskPriority:
                count = tasks.filter(priority=priority.value).count()
                if count > 0:
                    tasks_by_priority[priority.label] = count
            
            # Tasks by status
            tasks_by_status = {}
            for status in TaskStatus:
                count = tasks.filter(status=status.value).count()
                if count > 0:
                    tasks_by_status[status.label] = count
            
            stats = {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks.count(),
                'in_progress_tasks': tasks.filter(
                    status__in=[TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
                ).count(),
                'overdue_tasks': overdue_tasks.count(),
                'completion_rate': round((completed_tasks.count() / total_tasks) * 100, 1),
                'average_completion_time': avg_completion_time,
                'tasks_by_priority': tasks_by_priority,
                'tasks_by_status': tasks_by_status,
            }
        
        # Cache for 15 minutes
        cache.set(cache_key, stats, 900)
    
    return stats


def move_task(task, new_column, new_position=None):
    """
    Move task to new column and position
    
    Args:
        task: Task instance to move
        new_column: Column instance to move to
        new_position: New position in column (optional)
    """
    from django.db import transaction
    from .models import Task
    
    old_column = task.column
    old_position = task.position
    
    with transaction.atomic():
        # If moving to different column
        if old_column != new_column:
            # Update positions in old column
            Task.objects.filter(
                column=old_column,
                position__gt=old_position
            ).update(position=models.F('position') - 1)
            
            # Get new position if not specified
            if new_position is None:
                max_pos = Task.objects.filter(column=new_column).aggregate(
                    max_pos=models.Max('position')
                )['max_pos'] or 0
                new_position = max_pos + 1
            
            # Make space in new column
            Task.objects.filter(
                column=new_column,
                position__gte=new_position
            ).update(position=models.F('position') + 1)
            
            # Update task
            task.column = new_column
            task.position = new_position
            task.save()
        
        # If moving within same column
        elif new_position is not None and new_position != old_position:
            if new_position > old_position:
                # Moving down
                Task.objects.filter(
                    column=old_column,
                    position__gt=old_position,
                    position__lte=new_position
                ).update(position=models.F('position') - 1)
            else:
                # Moving up
                Task.objects.filter(
                    column=old_column,
                    position__gte=new_position,
                    position__lt=old_position
                ).update(position=models.F('position') + 1)
            
            task.position = new_position
            task.save()
    
    # Clear cache
    cache.delete(f'board_stats_{task.board.id}')


def create_board_from_template(template, organization, user, **kwargs):
    """Create a new board from a template"""
    from .models import Board, Column, Task
    
    # Create board
    board_data = {
        'name': kwargs.get('name', f'{template.name} - {organization.name}'),
        'description': kwargs.get('description', template.description),
        'organization': organization,
        'created_by': user,
        'board_type': template.board_type,
        'is_public': kwargs.get('is_public', True),
    }
    
    board = Board.objects.create(**board_data)
    
    # Create columns
    columns_map = {}  # Map template position to actual column
    for col_config in template.get_default_columns():
        column = Column.objects.create(
            board=board,
            name=col_config['name'],
            position=col_config['position'],
            color=col_config['color'],
            wip_limit=col_config.get('wip_limit'),
            is_done_column=col_config.get('is_done_column', False)
        )
        columns_map[col_config['position']] = column
    
    # Create default tasks
    for task_config in template.get_default_tasks():
        column_pos = task_config.get('column_position', 1)
        column = columns_map.get(column_pos)
        
        if column:
            Task.objects.create(
                board=board,
                column=column,
                title=task_config['title'],
                description=task_config.get('description', ''),
                priority=task_config.get('priority', 'medium'),
                created_by=user,
                labels=task_config.get('labels', [])
            )
    
    # Increment template usage
    template.increment_usage()
    
    return board


def get_task_activity(task, days=30):
    """Get recent activity for a task"""
    from .models import TaskComment
    from django.contrib.admin.models import LogEntry
    from django.contrib.contenttypes.models import ContentType
    
    since = timezone.now() - timedelta(days=days)
    activity = []
    
    # Get comments
    comments = TaskComment.objects.filter(
        task=task,
        created_at__gte=since
    ).select_related('author').order_by('created_at')
    
    for comment in comments:
        activity.append({
            'type': 'comment',
            'timestamp': comment.created_at,
            'user': comment.author,
            'data': {'content': comment.content}
        })
    
    # Get change logs if available
    try:
        content_type = ContentType.objects.get_for_model(task)
        logs = LogEntry.objects.filter(
            content_type=content_type,
            object_id=str(task.id),
            action_time__gte=since
        ).select_related('user').order_by('action_time')
        
        for log in logs:
            activity.append({
                'type': 'change',
                'timestamp': log.action_time,
                'user': log.user,
                'data': {'message': log.change_message}
            })
    except:
        pass
    
    # Sort by timestamp
    activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activity


def export_board_data(board, format='json'):
    """Export board data in various formats"""
    from .models import TaskStatus
    import json
    from datetime import datetime
    
    # Serialize datetime objects
    def datetime_handler(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    # Collect board data
    data = {
        'board': {
            'name': board.name,
            'description': board.description,
            'board_type': board.board_type,
            'created_at': board.created_at,
            'is_public': board.is_public,
        },
        'columns': [],
        'tasks': [],
        'export_date': timezone.now()
    }
    
    # Add columns
    for column in board.columns.all().order_by('position'):
        data['columns'].append({
            'name': column.name,
            'position': column.position,
            'color': column.color,
            'wip_limit': column.wip_limit,
            'is_done_column': column.is_done_column,
        })
    
    # Add tasks
    for task in board.tasks.all().select_related('created_by').prefetch_related('assignments'):
        task_data = {
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'priority': task.priority,
            'column_position': task.column.position,
            'position': task.position,
            'created_at': task.created_at,
            'updated_at': task.updated_at,
            'due_date': task.due_date,
            'estimated_hours': float(task.estimated_hours) if task.estimated_hours else None,
            'time_spent': float(task.time_spent),
            'labels': task.labels,
            'assignees': [a.assignee.username for a in task.assignments.all()],
            'creator': task.created_by.username if task.created_by else None,
        }
        
        if task.completed_at:
            task_data['completed_at'] = task.completed_at
            
        data['tasks'].append(task_data)
    
    if format.lower() == 'json':
        return json.dumps(data, default=datetime_handler, indent=2)
    elif format.lower() == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        
        # Export tasks as CSV
        fieldnames = [
            'title', 'description', 'status', 'priority', 'column',
            'created_at', 'due_date', 'estimated_hours', 'time_spent',
            'assignees', 'creator'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for task in data['tasks']:
            csv_row = {
                'title': task['title'],
                'description': task['description'],
                'status': task['status'],
                'priority': task['priority'],
                'column': f"Position {task['column_position']}",
                'created_at': task['created_at'],
                'due_date': task['due_date'] or '',
                'estimated_hours': task['estimated_hours'] or '',
                'time_spent': task['time_spent'],
                'assignees': ', '.join(task['assignees']),
                'creator': task['creator'] or '',
            }
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    return data


# Import models for use in functions
from django.db import models