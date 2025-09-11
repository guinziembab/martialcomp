from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.utils import timezone

from ..models import Board, Column, Task, BoardTemplate, BoardType
from ..forms import BoardForm, ColumnForm, BoardFilterForm
from ..utils import check_board_access, get_user_organizations, get_board_statistics


@login_required
def board_list(request):
    """List all boards accessible to the user"""
    user_orgs = get_user_organizations(request.user)
    
    # Base queryset
    boards = Board.objects.filter(
        organization__in=user_orgs
    ).select_related('organization', 'created_by').annotate(
        task_count=Count('tasks'),
        completed_task_count=Count('tasks', filter=Q(tasks__status='done'))
    )
    
    # Apply filters
    filter_form = BoardFilterForm(request.GET, user=request.user)
    if filter_form.is_valid():
        board_type = filter_form.cleaned_data.get('board_type')
        organization = filter_form.cleaned_data.get('organization')
        include_archived = filter_form.cleaned_data.get('is_archived', False)
        
        if board_type:
            boards = boards.filter(board_type=board_type)
        
        if organization:
            boards = boards.filter(organization=organization)
        
        if not include_archived:
            boards = boards.filter(is_archived=False)
    else:
        # Default: exclude archived boards
        boards = boards.filter(is_archived=False)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        boards = boards.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Ordering
    order_by = request.GET.get('order', '-created_at')
    valid_orders = ['name', '-name', 'created_at', '-created_at', 'task_count', '-task_count']
    if order_by in valid_orders:
        boards = boards.order_by(order_by)
    
    # Pagination
    paginator = Paginator(boards, 12)  # 12 boards per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'boards': page_obj,
        'filter_form': filter_form,
        'search_query': search_query,
        'current_order': order_by,
        'board_types': BoardType.choices,
    }
    
    return render(request, 'task_management/boards/board_list.html', context)


@login_required
def board_detail(request, board_id):
    """Display board details with columns and tasks overview"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check access permission
    if not board.can_access(request.user):
        messages.error(request, _("Vous n'avez pas accès à ce tableau."))
        return redirect('task_management:board_list')
    
    # Get board statistics
    stats = get_board_statistics(board)
    
    # Get columns with task counts
    columns = board.columns.all().annotate(
        task_count=Count('tasks'),
        overdue_task_count=Count('tasks', filter=Q(
            tasks__due_date__lt=timezone.now(),
            tasks__status__in=['todo', 'in_progress', 'in_review']
        ))
    ).order_by('position')
    
    # Recent activity (last 10 items)
    from ..utils import get_task_activity
    recent_tasks = board.tasks.filter(
        updated_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).select_related('created_by').order_by('-updated_at')[:10]
    
    context = {
        'board': board,
        'columns': columns,
        'stats': stats,
        'recent_tasks': recent_tasks,
        'can_edit': check_board_access(request.user, board, 'edit'),
        'can_admin': check_board_access(request.user, board, 'admin'),
    }
    
    return render(request, 'task_management/boards/board_detail.html', context)


@login_required
def board_create(request):
    """Create a new board"""
    if request.method == 'POST':
        form = BoardForm(request.POST, user=request.user)
        if form.is_valid():
            board = form.save(commit=False)
            board.created_by = request.user
            board.save()
            
            # Handle allowed roles (many-to-many field)
            form.save_m2m()
            
            messages.success(request, _("Tableau créé avec succès."))
            return redirect('task_management:board_detail', board_id=board.id)
    else:
        form = BoardForm(user=request.user)
    
    # Get available templates
    templates = BoardTemplate.objects.filter(is_public=True).order_by(
        '-is_system_template', 'name'
    )
    
    context = {
        'form': form,
        'templates': templates,
        'board_types': BoardType.choices,
    }
    
    return render(request, 'task_management/boards/board_create.html', context)


@login_required
@require_POST
def board_create_from_template(request, template_id):
    """Create board from template via AJAX"""
    template = get_object_or_404(BoardTemplate, id=template_id, is_public=True)
    
    # Get form data
    name = request.POST.get('name')
    description = request.POST.get('description', template.description)
    organization_id = request.POST.get('organization')
    
    if not name or not organization_id:
        return JsonResponse({
            'success': False,
            'error': _('Nom et organisation requis')
        }, status=400)
    
    try:
        from apps.organizations.models import Organization, OrganizationMember
        
        # Verify user can create board in this organization
        organization = Organization.objects.get(id=organization_id)
        membership = OrganizationMember.objects.get(
            user=request.user,
            organization=organization,
            is_active=True,
            role__in=['owner', 'admin']
        )
        
        # Create board from template
        from ..utils import create_board_from_template
        board = create_board_from_template(
            template=template,
            organization=organization,
            user=request.user,
            name=name,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'board_id': board.id,
            'board_name': board.name,
            'redirect_url': f'/task-management/boards/{board.id}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def board_edit(request, board_id):
    """Edit board settings"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check edit permission
    if not check_board_access(request.user, board, 'edit'):
        messages.error(request, _("Vous n'avez pas la permission de modifier ce tableau."))
        return redirect('task_management:board_detail', board_id=board.id)
    
    if request.method == 'POST':
        form = BoardForm(request.POST, instance=board, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Tableau mis à jour avec succès."))
            return redirect('task_management:board_detail', board_id=board.id)
    else:
        form = BoardForm(instance=board, user=request.user)
    
    context = {
        'form': form,
        'board': board,
    }
    
    return render(request, 'task_management/boards/board_edit.html', context)


@login_required
@require_POST
def board_archive(request, board_id):
    """Archive/unarchive a board"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check admin permission
    if not check_board_access(request.user, board, 'admin'):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    board.is_archived = not board.is_archived
    board.save()
    
    action = _('archivé') if board.is_archived else _('désarchivé')
    messages.success(request, _("Tableau {} avec succès.").format(action))
    
    return JsonResponse({
        'success': True,
        'is_archived': board.is_archived,
        'message': _("Tableau {} avec succès.").format(action)
    })


@login_required
@require_POST
def board_delete(request, board_id):
    """Delete a board permanently"""
    board = get_object_or_404(Board, id=board_id)
    
    # Only board creator or org admin can delete
    if not (board.created_by == request.user or check_board_access(request.user, board, 'admin')):
        return JsonResponse({
            'success': False,
            'error': _('Permission insuffisante')
        }, status=403)
    
    board_name = board.name
    board.delete()
    
    messages.success(request, _("Tableau '{}' supprimé avec succès.").format(board_name))
    
    return JsonResponse({
        'success': True,
        'redirect_url': '/task-management/boards/'
    })


@login_required
def board_columns(request, board_id):
    """Manage board columns"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check edit permission
    if not check_board_access(request.user, board, 'edit'):
        messages.error(request, _("Vous n'avez pas la permission de modifier ce tableau."))
        return redirect('task_management:board_detail', board_id=board.id)
    
    columns = board.columns.all().order_by('position')
    
    if request.method == 'POST':
        form = ColumnForm(request.POST)
        if form.is_valid():
            column = form.save(commit=False)
            column.board = board
            
            # Set position
            max_position = columns.aggregate(max_pos=models.Max('position'))['max_pos'] or 0
            column.position = max_position + 1
            
            column.save()
            messages.success(request, _("Colonne ajoutée avec succès."))
            return redirect('task_management:board_columns', board_id=board.id)
    else:
        form = ColumnForm()
    
    context = {
        'board': board,
        'columns': columns,
        'form': form,
    }
    
    return render(request, 'task_management/boards/board_columns.html', context)


@login_required
@require_POST
def column_update_position(request, board_id):
    """Update column positions via AJAX"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check edit permission
    if not check_board_access(request.user, board, 'edit'):
        return JsonResponse({'success': False, 'error': _('Permission insuffisante')}, status=403)
    
    try:
        import json
        positions = json.loads(request.body)
        
        for column_data in positions:
            column_id = column_data.get('id')
            new_position = column_data.get('position')
            
            if column_id and new_position is not None:
                Column.objects.filter(
                    id=column_id,
                    board=board
                ).update(position=new_position)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def column_delete(request, board_id, column_id):
    """Delete a column"""
    board = get_object_or_404(Board, id=board_id)
    column = get_object_or_404(Column, id=column_id, board=board)
    
    # Check edit permission
    if not check_board_access(request.user, board, 'edit'):
        return JsonResponse({'success': False, 'error': _('Permission insuffisante')}, status=403)
    
    # Check if column has tasks
    if column.tasks.exists():
        return JsonResponse({
            'success': False,
            'error': _('Impossible de supprimer une colonne contenant des tâches')
        }, status=400)
    
    # Check if it's the last column
    if board.columns.count() <= 1:
        return JsonResponse({
            'success': False,
            'error': _('Un tableau doit avoir au moins une colonne')
        }, status=400)
    
    column_name = column.name
    column.delete()
    
    return JsonResponse({
        'success': True,
        'message': _("Colonne '{}' supprimée avec succès.").format(column_name)
    })


@login_required
def board_export(request, board_id):
    """Export board data"""
    board = get_object_or_404(Board, id=board_id)
    
    # Check access permission
    if not board.can_access(request.user):
        raise Http404(_("Tableau non trouvé"))
    
    format_type = request.GET.get('format', 'json').lower()
    
    from ..utils import export_board_data
    from django.http import HttpResponse
    
    try:
        data = export_board_data(board, format_type)
        
        if format_type == 'json':
            response = HttpResponse(data, content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{board.name}_export.json"'
        elif format_type == 'csv':
            response = HttpResponse(data, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{board.name}_export.csv"'
        else:
            return JsonResponse({'error': _('Format non supporté')}, status=400)
        
        return response
        
    except Exception as e:
        messages.error(request, _("Erreur lors de l'export: {}").format(str(e)))
        return redirect('task_management:board_detail', board_id=board.id)


# Import required models
from django.db import models
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset