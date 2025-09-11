from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Prefetch
from django.utils import timezone

from ..models import Board, Column, Task, TaskAssignment, TaskStatus
from ..forms import QuickTaskForm
from ..utils import check_board_access, move_task
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


@login_required
def kanban_view(request, board_id):
    """Main Kanban board interface"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check access permission
    if not board.can_access(request.user):
        messages.error(request, _("Vous n'avez pas accès à ce tableau."))
        return redirect('task_management:board_list')
    
    # Get columns with optimized task loading
    columns = board.columns.prefetch_related(
        Prefetch(
            'tasks',
            queryset=Task.objects.select_related('created_by').prefetch_related(
                Prefetch(
                    'assignments',
                    queryset=TaskAssignment.objects.select_related('assignee').filter(is_active=True)
                ),
                'subtasks'
            ).order_by('position', 'created_at')
        )
    ).order_by('position')
    
    # Filter tasks if needed
    filter_status = request.GET.get('status')
    filter_priority = request.GET.get('priority')
    filter_assignee = request.GET.get('assignee')
    filter_overdue = request.GET.get('overdue')
    
    filtered_columns = []
    for column in columns:
        filtered_tasks = column.tasks.all()
        
        if filter_status:
            filtered_tasks = filtered_tasks.filter(status=filter_status)
        if filter_priority:
            filtered_tasks = filtered_tasks.filter(priority=filter_priority)
        if filter_assignee:
            filtered_tasks = filtered_tasks.filter(assignments__assignee_id=filter_assignee)
        if filter_overdue:
            filtered_tasks = filtered_tasks.filter(
                due_date__lt=timezone.now(),
                status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
            )
        
        # Create a new column object with filtered tasks
        column_data = {
            'id': column.id,
            'name': column.name,
            'color': column.color,
            'position': column.position,
            'wip_limit': column.wip_limit,
            'is_done_column': column.is_done_column,
            'tasks': list(filtered_tasks),
            'task_count': len(filtered_tasks),
            'wip_status': column.get_wip_status() if not any([filter_status, filter_priority, filter_assignee, filter_overdue]) else 'no_limit',
        }
        filtered_columns.append(column_data)
    
    # Get board members for assignment filter
    try:
        from apps.organizations.models import OrganizationMember
        board_members = OrganizationMember.objects.filter(
            organization=board.organization,
            is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
    except ImportError:
        board_members = []
    
    # Quick task form
    quick_task_form = QuickTaskForm(board=board)
    
    context = {
        'board': board,
        'columns': filtered_columns,
        'can_edit': check_board_access(request.user, board, 'edit'),
        'can_admin': check_board_access(request.user, board, 'admin'),
        'quick_task_form': quick_task_form,
        'board_members': board_members,
        'filters': {
            'status': filter_status,
            'priority': filter_priority,
            'assignee': filter_assignee,
            'overdue': filter_overdue,
        },
        'task_statuses': TaskStatus.choices,
        'task_priorities': [
            ('low', _('Basse')),
            ('medium', _('Moyenne')),
            ('high', _('Haute')),
            ('urgent', _('Urgente')),
        ],
    }
    
    return render(request, 'task_management/kanban/kanban_board.html', context)


@login_required
@require_POST
def kanban_move_task(request, board_id):
    """Handle task movement in Kanban board"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check permission
    if not check_board_access(request.user, board, 'edit'):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
    except:
        return JsonResponse({
            'success': False,
            'error': _('Données JSON invalides')
        }, status=400)
    
    task_id = data.get('task_id')
    new_column_id = data.get('column_id')
    new_position = data.get('position', 0)
    
    if not task_id or not new_column_id:
        return JsonResponse({
            'success': False,
            'error': _('task_id et column_id requis')
        }, status=400)
    
    try:
        task = Task.objects.get(id=task_id, board=board)
        new_column = Column.objects.get(id=new_column_id, board=board)
    except (Task.DoesNotExist, Column.DoesNotExist):
        return JsonResponse({
            'success': False,
            'error': _('Tâche ou colonne non trouvée')
        }, status=404)
    
    # Check WIP limit
    if new_column.wip_limit and task.column != new_column:
        current_tasks_count = new_column.tasks.count()
        if current_tasks_count >= new_column.wip_limit:
            return JsonResponse({
                'success': False,
                'error': _('Limite WIP atteinte pour cette colonne ({}/{})').format(
                    current_tasks_count, new_column.wip_limit
                ),
                'wip_exceeded': True
            }, status=400)
    
    # Move the task
    try:
        move_task(task, new_column, new_position)
        
        # Update task status based on column
        old_status = task.status
        if new_column.is_done_column and task.status != TaskStatus.DONE:
            task.status = TaskStatus.DONE
            if not task.completed_at:
                task.completed_at = timezone.now()
            task.save()
        elif not new_column.is_done_column and task.status == TaskStatus.DONE:
            task.status = TaskStatus.IN_PROGRESS
            task.completed_at = None
            task.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'column_id': new_column.id,
                'position': task.position,
                'status': task.status,
                'status_changed': old_status != task.status,
            },
            'column_stats': {
                'task_count': new_column.tasks.count(),
                'wip_status': new_column.get_wip_status(),
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def kanban_task_card(request, task_id):
    """Get task card HTML for dynamic updates"""
    task = get_object_or_404(Task.objects.select_related(
        'created_by', 'board', 'column'
    ).prefetch_related(
        'assignments__assignee',
        'subtasks',
        'comments'
    ), id=task_id)
    
    # Check access
    if not task.board.can_access(request.user):
        return JsonResponse({
            'success': False,
            'error': _('Accès refusé')
        }, status=403)
    
    # Render task card
    card_html = render(request, 'task_management/kanban/kanban_card.html', {
        'task': task,
        'can_edit': task.can_edit(request.user)
    }).content.decode('utf-8')
    
    return JsonResponse({
        'success': True,
        'html': card_html,
        'task_data': {
            'id': task.id,
            'title': task.title,
            'status': task.status,
            'priority': task.priority,
            'column_id': task.column.id,
            'position': task.position,
            'is_overdue': task.is_overdue,
            'assignee_count': task.assignee_count,
            'comments_count': task.comments.count(),
            'subtasks_count': task.subtasks.count(),
            'completed_subtasks': task.subtasks.filter(status=TaskStatus.DONE).count(),
        }
    })


@login_required
@require_POST
def kanban_update_column_wip(request, board_id, column_id):
    """Update column WIP limit"""
    board = get_object_or_404(Board, id=board_id)
    column = get_object_or_404(Column, id=column_id, board=board)
    
    # Check admin permission
    if not check_board_access(request.user, board, 'admin'):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    try:
        wip_limit = request.POST.get('wip_limit')
        if wip_limit:
            wip_limit = int(wip_limit)
            if wip_limit <= 0:
                wip_limit = None
        else:
            wip_limit = None
        
        column.wip_limit = wip_limit
        column.save()
        
        return JsonResponse({
            'success': True,
            'wip_limit': wip_limit,
            'wip_status': column.get_wip_status(),
            'current_count': column.tasks.count()
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': _('Limite WIP invalide')
        }, status=400)


@login_required
def kanban_board_stats(request, board_id):
    """Get board statistics for dashboard"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check access
    if not board.can_access(request.user):
        return JsonResponse({
            'success': False,
            'error': _('Accès refusé')
        }, status=403)
    
    from ..utils import get_board_statistics
    stats = get_board_statistics(board)
    
    # Add real-time column stats
    column_stats = []
    for column in board.columns.all().order_by('position'):
        tasks = column.tasks.all()
        column_stats.append({
            'id': column.id,
            'name': column.name,
            'task_count': tasks.count(),
            'overdue_count': tasks.filter(
                due_date__lt=timezone.now(),
                status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
            ).count(),
            'wip_limit': column.wip_limit,
            'wip_status': column.get_wip_status(),
            'is_over_limit': column.is_over_wip_limit,
        })
    
    return JsonResponse({
        'success': True,
        'board_stats': stats,
        'column_stats': column_stats,
        'last_updated': timezone.now().isoformat()
    })


@login_required
def kanban_fullscreen(request, board_id):
    """Fullscreen Kanban view for presentations"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check access permission
    if not board.can_access(request.user):
        messages.error(request, _("Vous n'avez pas accès à ce tableau."))
        return redirect('task_management:board_list')
    
    # Get columns with tasks (simplified for fullscreen)
    columns = board.columns.prefetch_related(
        Prefetch(
            'tasks',
            queryset=Task.objects.select_related('created_by').prefetch_related(
                'assignments__assignee'
            ).filter(
                # Only show non-archived tasks
            ).order_by('position', 'created_at')
        )
    ).order_by('position')
    
    context = {
        'board': board,
        'columns': columns,
        'fullscreen': True,
    }
    
    return render(request, 'task_management/kanban/kanban_fullscreen.html', context)


@login_required
@require_POST
def kanban_auto_refresh(request, board_id):
    """Auto-refresh endpoint for real-time updates"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check access
    if not board.can_access(request.user):
        return JsonResponse({
            'success': False,
            'error': _('Accès refusé')
        }, status=403)
    
    last_update = request.POST.get('last_update')
    if last_update:
        try:
            from datetime import datetime
            last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        except:
            last_update = None
    
    # Get updated tasks since last update
    updated_tasks = []
    if last_update:
        recent_tasks = board.tasks.filter(
            updated_at__gt=last_update
        ).select_related('column').prefetch_related(
            'assignments__assignee'
        )
        
        for task in recent_tasks:
            updated_tasks.append({
                'id': task.id,
                'column_id': task.column.id,
                'title': task.title,
                'status': task.status,
                'priority': task.priority,
                'position': task.position,
                'updated_at': task.updated_at.isoformat(),
                'assignees': [{
                    'id': a.assignee.id,
                    'name': a.assignee.get_full_name() or a.assignee.username,
                } for a in task.assignments.all()],
                'is_overdue': task.is_overdue,
            })
    
    return JsonResponse({
        'success': True,
        'updated_tasks': updated_tasks,
        'timestamp': timezone.now().isoformat(),
        'has_updates': len(updated_tasks) > 0
    })