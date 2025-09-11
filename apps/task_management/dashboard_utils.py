from django.db.models import Q, Count
from django.utils import timezone
from .models import Task, Board, TaskStatus
from .utils import get_user_organizations
from .permissions import has_task_management_access


def get_dashboard_task_data(user, limit_tasks=5, limit_boards=5):
    """
    Get task management data for dashboard widgets
    
    Returns:
        dict: Contains user tasks, boards, and statistics
    """
    if not has_task_management_access(user):
        return {
            'has_access': False,
            'user_tasks': [],
            'user_boards': [],
            'tasks_stats': {},
            'total_user_tasks': 0,
        }
    
    # Get user's assigned tasks
    user_tasks = Task.objects.filter(
        assignments__assignee=user,
        assignments__is_active=True
    ).select_related(
        'board', 'column', 'created_by'
    ).prefetch_related(
        'assignments__assignee'
    ).distinct().order_by(
        'due_date',  # Prioritize by due date
        '-priority',  # Then by priority
        '-created_at'
    )[:limit_tasks]
    
    # Get total count for "view all" link
    total_user_tasks = Task.objects.filter(
        assignments__assignee=user,
        assignments__is_active=True
    ).distinct().count()
    
    # Task statistics
    now = timezone.now()
    tasks_stats = {
        'todo_count': user_tasks.filter(status=TaskStatus.TODO).count(),
        'in_progress_count': user_tasks.filter(
            status__in=[TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
        ).count(),
        'overdue_count': user_tasks.filter(
            due_date__lt=now,
            status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
        ).count(),
    }
    
    # Get user's accessible boards
    user_orgs = get_user_organizations(user)
    user_boards = Board.objects.filter(
        organization__in=user_orgs,
        is_archived=False
    ).annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__status=TaskStatus.DONE))
    ).select_related('organization').order_by('-updated_at')[:limit_boards]
    
    # Calculate progress percentages
    for board in user_boards:
        if board.task_count > 0:
            board.progress_percentage = round(
                (board.completed_task_count / board.task_count) * 100, 1
            )
        else:
            board.progress_percentage = 0
    
    return {
        'has_access': True,
        'user_tasks': user_tasks,
        'user_boards': user_boards,
        'tasks_stats': tasks_stats,
        'total_user_tasks': total_user_tasks,
    }


def get_club_dashboard_task_data(user, organization):
    """
    Get task management data specific to club dashboard
    """
    if not has_task_management_access(user):
        return {'has_access': False}
    
    # Club-specific boards
    club_boards = Board.objects.filter(
        organization=organization,
        board_type__in=['club', 'general', 'training'],
        is_archived=False
    ).annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__status=TaskStatus.DONE))
    ).order_by('-updated_at')[:3]
    
    # Club members' tasks
    try:
        from apps.organizations.models import OrganizationMember
        club_member_users = OrganizationMember.objects.filter(
            organization=organization,
            is_active=True
        ).values_list('user', flat=True)
        
        club_tasks_stats = {
            'total_tasks': Task.objects.filter(
                board__organization=organization
            ).count(),
            'active_tasks': Task.objects.filter(
                board__organization=organization,
                status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
            ).count(),
            'overdue_tasks': Task.objects.filter(
                board__organization=organization,
                due_date__lt=timezone.now(),
                status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
            ).count(),
        }
    except ImportError:
        club_tasks_stats = {}
    
    return {
        'has_access': True,
        'club_boards': club_boards,
        'club_tasks_stats': club_tasks_stats,
    }


def get_federation_dashboard_task_data(user, federation_organizations):
    """
    Get task management data specific to federation dashboard
    """
    if not has_task_management_access(user):
        return {'has_access': False}
    
    # Federation-wide boards
    federation_boards = Board.objects.filter(
        organization__in=federation_organizations,
        board_type__in=['federation', 'competition', 'general'],
        is_archived=False
    ).annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__status=TaskStatus.DONE))
    ).select_related('organization').order_by('-updated_at')[:5]
    
    # Federation-wide task statistics
    federation_stats = {
        'total_boards': Board.objects.filter(
            organization__in=federation_organizations,
            is_archived=False
        ).count(),
        'total_tasks': Task.objects.filter(
            board__organization__in=federation_organizations
        ).count(),
        'active_competitions': Board.objects.filter(
            organization__in=federation_organizations,
            board_type='competition',
            is_archived=False
        ).count(),
    }
    
    return {
        'has_access': True,
        'federation_boards': federation_boards,
        'federation_stats': federation_stats,
    }


def get_coach_dashboard_task_data(user):
    """
    Get task management data specific to coach dashboard
    """
    if not has_task_management_access(user):
        return {'has_access': False}
    
    # Coach's training-related boards
    user_orgs = get_user_organizations(user)
    coaching_boards = Board.objects.filter(
        Q(organization__in=user_orgs) & 
        Q(board_type__in=['training', 'general']) |
        Q(created_by=user)
    ).annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__status=TaskStatus.DONE))
    ).distinct().order_by('-updated_at')[:4]
    
    # Coach's personal tasks (training plans, student management, etc.)
    coaching_tasks = Task.objects.filter(
        Q(assignments__assignee=user) |
        Q(created_by=user, board__board_type='training')
    ).select_related(
        'board', 'column'
    ).distinct().order_by('due_date', '-priority')[:5]
    
    # Coaching statistics
    coaching_stats = {
        'training_boards': coaching_boards.filter(board_type='training').count(),
        'pending_training_tasks': coaching_tasks.filter(
            status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS],
            board__board_type='training'
        ).count(),
    }
    
    return {
        'has_access': True,
        'coaching_boards': coaching_boards,
        'coaching_tasks': coaching_tasks,
        'coaching_stats': coaching_stats,
    }


def get_quick_action_context(user, dashboard_type):
    """
    Get quick action links for task management based on user role
    """
    if not has_task_management_access(user):
        return []
    
    base_actions = [
        {
            'title': 'Mes Tâches',
            'url': 'task_management:my_tasks',
            'icon': 'fas fa-tasks',
            'color': 'primary'
        },
        {
            'title': 'Mes Tableaux',
            'url': 'task_management:board_list', 
            'icon': 'fas fa-columns',
            'color': 'success'
        }
    ]
    
    # Role-specific actions
    role_actions = {
        'club': [
            {
                'title': 'Nouveau Tableau Club',
                'url': 'task_management:board_create',
                'icon': 'fas fa-plus',
                'color': 'info',
                'params': '?type=club'
            }
        ],
        'federation': [
            {
                'title': 'Tableau Compétition',
                'url': 'task_management:board_create',
                'icon': 'fas fa-trophy',
                'color': 'warning',
                'params': '?type=competition'
            }
        ],
        'coach': [
            {
                'title': 'Plan d\'Entraînement',
                'url': 'task_management:board_create',
                'icon': 'fas fa-dumbbell',
                'color': 'success',
                'params': '?type=training'
            }
        ]
    }
    
    actions = base_actions + role_actions.get(dashboard_type, [])
    return actions


def get_recent_activity_data(user, limit=5):
    """
    Get recent task activity for dashboard
    """
    if not has_task_management_access(user):
        return []
    
    # Get user's recent task updates
    recent_tasks = Task.objects.filter(
        Q(assignments__assignee=user) | Q(created_by=user)
    ).select_related(
        'board', 'column', 'created_by'
    ).distinct().order_by('-updated_at')[:limit]
    
    activity_items = []
    for task in recent_tasks:
        activity_items.append({
            'type': 'task_update',
            'title': task.title,
            'description': f"dans {task.board.name}",
            'url': f"/task-management/tasks/{task.id}/",
            'timestamp': task.updated_at,
            'icon': 'fas fa-task',
            'color': 'primary'
        })
    
    return activity_items