from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import Task, Board, Column, TaskComment, TaskAssignment, TaskStatus, TaskPriority
from ..forms import TaskForm, TaskCommentForm, QuickTaskForm, TaskAssignmentForm
from ..utils import check_board_access, move_task, get_task_activity
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

User = get_user_model()


@login_required
def task_detail(request, task_id):
    """Display detailed view of a task"""
    task = get_object_or_404(Task.objects.select_related(
        'board', 'column', 'created_by', 'parent_task'
    ).prefetch_related(
        'assignments__assignee',
        'subtasks',
        'comments__author'
    ), id=task_id)
    
    # Check board access
    if not task.board.can_access(request.user):
        raise Http404(_("Tâche non trouvée"))
    
    # Handle comment form submission
    if request.method == 'POST' and 'add_comment' in request.POST:
        comment_form = TaskCommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()
            
            messages.success(request, _("Commentaire ajouté avec succès."))
            return redirect('task_management:task_detail', task_id=task.id)
    else:
        comment_form = TaskCommentForm()
    
    # Get task activity
    activity = get_task_activity(task)

    # Get related tasks
    related_tasks = []
    if task.parent_task:
        related_tasks.extend(task.parent_task.subtasks.exclude(id=task.id))
    if task.subtasks.exists():
        related_tasks.extend(task.subtasks.all())

    # Get board members for inline assignment
    board_members = []
    try:
        from apps.organizations.models import OrganizationMember
        board_members = OrganizationMember.objects.filter(
            organization=task.board.organization,
            is_active=True
        ).select_related('user').order_by('user__first_name', 'user__last_name')
    except ImportError:
        pass

    # Get board columns for inline column change
    board_columns = task.board.columns.order_by('position')

    context = {
        'task': task,
        'comment_form': comment_form,
        'activity': activity,
        'related_tasks': related_tasks,
        'can_edit': task.can_edit(request.user),
        'can_edit_board': check_board_access(request.user, task.board, 'edit'),
        'progress_percentage': task.get_progress_percentage() if task.has_subtasks else None,
        'board_members': board_members,
        'board_columns': board_columns,
        'task_statuses': TaskStatus.choices,
        'task_priorities': TaskPriority.choices,
    }
    
    return render(request, 'task_management/tasks/task_detail.html', context)


@login_required
def task_create(request):
    """Create a new task"""
    board_id = request.GET.get('board_id')
    if not board_id:
        messages.error(request, _("Aucun tableau spécifié."))
        return redirect('task_management:board_list')
    
    board = get_object_or_404(Board, id=board_id)
    
    # Check edit permission
    if not check_board_access(request.user, board, 'edit'):
        messages.error(request, _("Vous n'avez pas la permission de créer des tâches dans ce tableau."))
        return redirect('task_management:board_detail', board_id=board.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, board=board)
        assignment_form = TaskAssignmentForm(request.POST, board=board)
        
        if form.is_valid():
            task = form.save(commit=False)
            task.board = board
            task.created_by = request.user
            
            # If no column specified, use first column
            if not task.column:
                task.column = board.columns.first()
            
            task.save()
            
            # Handle assignments
            if assignment_form.is_valid():
                assignees = assignment_form.cleaned_data.get('assignees', [])
                for assignee_user in assignees:
                    TaskAssignment.objects.create(
                        task=task,
                        assignee=assignee_user,
                        assigned_by=request.user,
                        role=TaskAssignment.AssignmentRole.ASSIGNEE
                    )
            
            messages.success(request, _("Tâche créée avec succès."))
            return redirect('task_management:task_detail', task_id=task.id)
    else:
        # Pre-fill column if specified
        initial_data = {}
        column_id = request.GET.get('column_id')
        if column_id:
            try:
                column = board.columns.get(id=column_id)
                initial_data['column'] = column
            except Column.DoesNotExist:
                pass
        
        form = TaskForm(initial=initial_data, board=board)
        assignment_form = TaskAssignmentForm(board=board)
    
    context = {
        'form': form,
        'assignment_form': assignment_form,
        'board': board,
    }
    
    return render(request, 'task_management/tasks/task_create.html', context)


@login_required
def task_edit(request, task_id):
    """Edit an existing task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check edit permission
    if not task.can_edit(request.user):
        messages.error(request, _("Vous n'avez pas la permission de modifier cette tâche."))
        return redirect('task_management:task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, board=task.board)
        assignment_form = TaskAssignmentForm(request.POST, board=task.board)
        
        if form.is_valid():
            task = form.save()
            
            # Handle assignments updates
            if assignment_form.is_valid():
                assignees = assignment_form.cleaned_data.get('assignees', [])
                
                # Remove old assignments
                task.assignments.all().delete()
                
                # Add new assignments
                for assignee_user in assignees:
                    TaskAssignment.objects.create(
                        task=task,
                        assignee=assignee_user,
                        assigned_by=request.user,
                        role=TaskAssignment.AssignmentRole.ASSIGNEE
                    )
            
            messages.success(request, _("Tâche mise à jour avec succès."))
            return redirect('task_management:task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task, board=task.board)
        
        # Pre-fill current assignees
        current_assignees = [assignment.assignee for assignment in task.assignments.all()]
        assignment_form = TaskAssignmentForm(
            initial={'assignees': current_assignees},
            board=task.board
        )
    
    context = {
        'form': form,
        'assignment_form': assignment_form,
        'task': task,
        'board': task.board,
    }
    
    return render(request, 'task_management/tasks/task_edit.html', context)


@login_required
@require_POST
def task_delete(request, task_id):
    """Delete a task"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if not (task.can_edit(request.user) or check_board_access(request.user, task.board, 'admin')):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    # Check if task has subtasks
    if task.subtasks.exists():
        return JsonResponse({
            'success': False,
            'error': _('Impossible de supprimer une tâche ayant des sous-tâches')
        }, status=400)
    
    board_id = task.board.id
    task_title = task.title
    task.delete()
    
    return JsonResponse({
        'success': True,
        'message': _("Tâche '{}' supprimée avec succès.").format(task_title),
        'redirect_url': f'/task-management/boards/{board_id}/kanban/'
    })


@login_required
@require_POST
def task_quick_create(request):
    """Quick task creation from Kanban board"""
    try:
        import json
        data = json.loads(request.body)
    except:
        data = request.POST
    
    form = QuickTaskForm(data)
    
    if form.is_valid():
        title = form.cleaned_data['title']
        column_id = form.cleaned_data['column_id']
        
        try:
            column = Column.objects.select_related('board').get(id=column_id)
            board = column.board
            
            # Check permission
            if not check_board_access(request.user, board, 'edit'):
                return JsonResponse({
                    'success': False,
                    'error': _('Permission insuffisante')
                }, status=403)
            
            # Create task
            task = Task.objects.create(
                title=title,
                board=board,
                column=column,
                created_by=request.user,
                status=TaskStatus.TODO
            )
            
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'status': task.status,
                    'priority': task.priority,
                    'column_id': column.id,
                    'created_at': task.created_at.isoformat(),
                    'assignees': [],
                    'due_date': None,
                    'is_overdue': False,
                    'labels': task.labels,
                    'comments_count': 0,
                    'subtasks_progress': 0,
                }
            })
            
        except Column.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': _('Colonne non trouvée')
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    }, status=400)


@login_required
@require_POST
def task_move(request, task_id):
    """Move task between columns"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if not check_board_access(request.user, task.board, 'edit'):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    try:
        import json
        data = json.loads(request.body)
    except:
        data = request.POST
    
    new_column_id = data.get('column_id')
    new_position = data.get('position', 0)
    
    if not new_column_id:
        return JsonResponse({
            'success': False,
            'error': _('column_id requis')
        }, status=400)
    
    try:
        new_column = Column.objects.get(id=new_column_id, board=task.board)
    except Column.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': _('Colonne invalide')
        }, status=400)
    
    # Move task using utility function
    move_task(task, new_column, new_position)
    
    # Update status based on column
    if new_column.is_done_column:
        task.status = TaskStatus.DONE
        task.save()
    
    return JsonResponse({
        'success': True,
        'task': {
            'id': task.id,
            'column_id': new_column.id,
            'position': task.position,
            'status': task.status,
        }
    })


@login_required
@require_POST
def task_update_status(request, task_id):
    """Update task status"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if not task.can_edit(request.user):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    new_status = data.get('status')
    if new_status not in [choice[0] for choice in TaskStatus.choices]:
        return JsonResponse({
            'success': False,
            'error': _('Statut invalide')
        }, status=400)

    old_column = task.column
    task.status = new_status
    if new_status == TaskStatus.DONE and not task.completed_at:
        task.completed_at = timezone.now()
    elif new_status != TaskStatus.DONE:
        task.completed_at = None

    # Move task to matching column on the board
    # Use explicit name mapping (case-insensitive) to avoid translation issues
    STATUS_COLUMN_MAP = {
        'todo': ['à faire', 'a faire', 'todo', 'to do'],
        'in_progress': ['en cours', 'in progress'],
        'in_review': ['en révision', 'en revision', 'in review'],
        'done': ['terminé', 'termine', 'done', 'completed'],
        'blocked': ['bloqué', 'bloque', 'blocked'],
    }
    moved_to_column = None
    matching_col = None

    # Strategy 1: match column name against known names for this status
    expected_names = STATUS_COLUMN_MAP.get(new_status, [])
    if expected_names:
        board_columns = list(task.board.columns.order_by('position'))
        for col in board_columns:
            if col.name.lower().strip() in expected_names:
                matching_col = col
                break

    # Strategy 2: for 'done', also check is_done_column flag
    if not matching_col and new_status == TaskStatus.DONE:
        matching_col = task.board.columns.filter(
            is_done_column=True
        ).first()

    # Strategy 3: fallback to position-based matching
    if not matching_col:
        status_position = {
            'todo': 0, 'in_progress': 1,
            'in_review': 2, 'done': 3,
        }
        target_pos = status_position.get(new_status)
        if target_pos is not None:
            board_columns = list(
                task.board.columns.order_by('position')
            )
            if target_pos < len(board_columns):
                matching_col = board_columns[target_pos]

    if matching_col and matching_col.id != old_column.id:
        task.column = matching_col
        task.position = 0
        moved_to_column = {
            'id': matching_col.id,
            'name': matching_col.name,
        }

    task.save()

    return JsonResponse({
        'success': True,
        'status': task.status,
        'status_display': task.get_status_display(),
        'moved_to_column': moved_to_column,
    })


@login_required
@require_POST
def task_update_priority(request, task_id):
    """Update task priority"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if not task.can_edit(request.user):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        data = request.POST
    new_priority = data.get('priority')
    if new_priority not in [choice[0] for choice in TaskPriority.choices]:
        return JsonResponse({
            'success': False,
            'error': _('Priorité invalide')
        }, status=400)

    task.priority = new_priority
    task.save()

    return JsonResponse({
        'success': True,
        'priority': task.priority,
        'priority_display': task.get_priority_display(),
    })


@login_required
@require_POST
def task_add_comment(request, task_id):
    """Add comment to task via AJAX"""
    task = get_object_or_404(Task, id=task_id)
    
    # Check access
    if not task.board.can_access(request.user):
        return JsonResponse({
            'success': False,
            'error': _('Accès refusé')
        }, status=403)
    
    content = request.POST.get('content', '').strip()
    parent_id = request.POST.get('parent_id')
    
    if not content:
        return JsonResponse({
            'success': False,
            'error': _('Contenu requis')
        }, status=400)
    
    # Create comment
    comment = TaskComment.objects.create(
        task=task,
        author=request.user,
        content=content,
        parent_comment_id=parent_id if parent_id else None
    )
    
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'content': comment.content,
            'author': comment.author.get_full_name() or comment.author.username,
            'created_at': comment.created_at.isoformat(),
            'is_reply': comment.is_reply,
        }
    })


@login_required
@require_POST
def task_assign(request, task_id):
    """Toggle assignment of a user to a task via AJAX"""
    task = get_object_or_404(Task, id=task_id)

    if not task.can_edit(request.user):
        return JsonResponse({'success': False, 'error': _('Permission insuffisante')}, status=403)

    import json
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST

    user_id = data.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': _('user_id requis')}, status=400)

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': _('Utilisateur non trouvé')}, status=404)

    # Toggle: if already assigned, remove; otherwise add
    existing = TaskAssignment.objects.filter(task=task, assignee=target_user).first()
    if existing:
        existing.delete()
        action = 'removed'
    else:
        TaskAssignment.objects.create(
            task=task,
            assignee=target_user,
            assigned_by=request.user,
            role=TaskAssignment.AssignmentRole.ASSIGNEE
        )
        action = 'added'

    assignees = [
        {
            'id': a.id,
            'name': a.get_full_name() or a.username,
            'initials': (a.first_name[:1] + a.last_name[:1]).upper() if a.first_name else a.username[:2].upper(),
        }
        for a in task.get_assignees()
    ]

    return JsonResponse({
        'success': True,
        'action': action,
        'assignees': assignees,
        'assignee_count': len(assignees),
    })


@login_required
def task_list(request):
    """List tasks with filtering and search"""
    # Get user's accessible boards
    from ..utils import get_user_boards
    user_boards = get_user_boards(request.user)
    
    tasks = Task.objects.filter(board__in=user_boards).select_related(
        'board', 'column', 'created_by'
    ).prefetch_related('assignments__assignee')
    
    # Filters
    board_id = request.GET.get('board')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    assigned_to_me = request.GET.get('assigned_to_me')
    overdue_only = request.GET.get('overdue_only')
    search = request.GET.get('q')
    
    if board_id:
        tasks = tasks.filter(board_id=board_id)
    
    if status:
        tasks = tasks.filter(status=status)
    
    if priority:
        tasks = tasks.filter(priority=priority)
    
    if assigned_to_me:
        tasks = tasks.filter(assignments__assignee=request.user)
    
    if overdue_only:
        tasks = tasks.filter(
            due_date__lt=timezone.now(),
            status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
        )
    
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Ordering
    order_by = request.GET.get('order', '-created_at')
    valid_orders = [
        'title', '-title', 'created_at', '-created_at',
        'due_date', '-due_date', 'priority', '-priority'
    ]
    if order_by in valid_orders:
        tasks = tasks.order_by(order_by)
    
    # Pagination
    paginator = Paginator(tasks, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'tasks': page_obj,
        'user_boards': user_boards,
        'task_statuses': TaskStatus.choices,
        'task_priorities': TaskPriority.choices,
        'filters': {
            'board': board_id,
            'status': status,
            'priority': priority,
            'assigned_to_me': assigned_to_me,
            'overdue_only': overdue_only,
            'search': search,
        }
    }
    
    return render(request, 'task_management/tasks/task_list.html', context)


@login_required
def my_tasks(request):
    """Show tasks assigned to current user"""
    tasks = Task.objects.filter(
        assignments__assignee=request.user,
        assignments__is_active=True
    ).select_related('board', 'column').prefetch_related(
        'assignments__assignee'
    ).distinct()
    
    # Group by status
    tasks_by_status = {}
    for status_value, status_label in TaskStatus.choices:
        tasks_by_status[status_value] = {
            'label': status_label,
            'tasks': tasks.filter(status=status_value).order_by('-created_at'),
            'count': tasks.filter(status=status_value).count()
        }
    
    # Get overdue tasks
    overdue_tasks = tasks.filter(
        due_date__lt=timezone.now(),
        status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW]
    ).order_by('due_date')
    
    context = {
        'tasks_by_status': tasks_by_status,
        'overdue_tasks': overdue_tasks,
        'total_tasks': tasks.count(),
    }
    
    return render(request, 'task_management/tasks/my_tasks.html', context)