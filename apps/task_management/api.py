from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import PermissionDenied

from .models import Board, Task, Column, TaskComment, TaskAssignment, BoardTemplate
from .serializers import (
    BoardSerializer, BoardCreateUpdateSerializer,
    TaskSerializer, TaskCreateUpdateSerializer, TaskMoveSerializer,
    ColumnSerializer, TaskCommentSerializer, TaskAssignmentSerializer,
    BoardTemplateSerializer, BoardStatsSerializer, KanbanBoardSerializer
)
from .utils import check_board_access, get_user_organizations, move_task, get_board_statistics
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class TaskManagementPermission(permissions.BasePermission):
    """Custom permission for task management API"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Board):
            if view.action in ['retrieve', 'list']:
                return obj.can_access(request.user)
            elif view.action in ['update', 'partial_update']:
                return obj.can_edit(request.user)
            elif view.action in ['destroy', 'archive']:
                return check_board_access(request.user, obj, 'admin')
        
        elif isinstance(obj, Task):
            if view.action in ['retrieve', 'list']:
                return obj.board.can_access(request.user)
            elif view.action in ['update', 'partial_update', 'destroy']:
                return obj.can_edit(request.user)
        
        elif isinstance(obj, TaskComment):
            if view.action in ['retrieve', 'list']:
                return obj.task.board.can_access(request.user)
            elif view.action in ['update', 'partial_update', 'destroy']:
                return obj.can_edit(request.user)
        
        return False


class BoardViewSet(viewsets.ModelViewSet, OrganizationIsolationMixin):
    """API ViewSet for Board management"""
    permission_classes = [TaskManagementPermission]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BoardCreateUpdateSerializer
        return BoardSerializer
    
    def get_queryset(self):
        """Filtre les tableaux par organisation avec isolation"""
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(Board, self.request.user)
        
        return base_queryset.select_related(
            'organization', 'created_by', 'related_competition'
        ).prefetch_related(
            'columns', 'tasks'
        ).annotate(
            task_count=Count('tasks'),
            completed_task_count=Count('tasks', filter=Q(tasks__status='done'))
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive/unarchive a board"""
        board = self.get_object()
        board.is_archived = not board.is_archived
        board.save()
        
        action_text = 'archivé' if board.is_archived else 'désarchivé'
        return Response({
            'success': True,
            'is_archived': board.is_archived,
            'message': f"Tableau {action_text} avec succès."
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get board statistics"""
        board = self.get_object()
        stats = get_board_statistics(board)
        serializer = BoardStatsSerializer(stats)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def kanban(self, request, pk=None):
        """Get board data optimized for Kanban view"""
        board = self.get_object()
        
        # Apply filters
        filters = {
            'status': request.query_params.get('status'),
            'priority': request.query_params.get('priority'),
            'assignee': request.query_params.get('assignee'),
            'overdue': request.query_params.get('overdue') == '1',
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v}
        
        data = {
            'board': board,
            'filters': filters,
            'filters_applied': filters
        }
        
        serializer = KanbanBoardSerializer(data, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Export board data"""
        board = self.get_object()
        format_type = request.data.get('format', 'json').lower()
        
        from .utils import export_board_data
        
        try:
            data = export_board_data(board, format_type)
            return Response({
                'success': True,
                'data': data,
                'filename': f"{board.name}_export.{format_type}"
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a board"""
        board = self.get_object()
        
        # Check permission
        if not check_board_access(request.user, board, 'edit'):
            return Response({
                'error': 'Permission insuffisante'
            }, status=status.HTTP_403_FORBIDDEN)
        
        new_name = request.data.get('name', f"{board.name} - Copie")
        
        with transaction.atomic():
            # Create new board
            new_board = Board.objects.create(
                name=new_name,
                description=board.description,
                organization=board.organization,
                created_by=request.user,
                board_type=board.board_type,
                color_theme=board.color_theme,
                is_public=board.is_public,
                allowed_roles=board.allowed_roles.copy() if board.allowed_roles else [],
                enable_time_tracking=board.enable_time_tracking,
                enable_comments=board.enable_comments,
                enable_attachments=board.enable_attachments
            )
            
            # Duplicate columns
            column_mapping = {}
            for column in board.columns.all():
                new_column = Column.objects.create(
                    board=new_board,
                    name=column.name,
                    position=column.position,
                    color=column.color,
                    wip_limit=column.wip_limit,
                    is_done_column=column.is_done_column
                )
                column_mapping[column.id] = new_column
            
            # Optionally duplicate tasks
            if request.data.get('include_tasks', False):
                for task in board.tasks.all():
                    Task.objects.create(
                        board=new_board,
                        column=column_mapping[task.column.id],
                        title=task.title,
                        description=task.description,
                        priority=task.priority,
                        estimated_hours=task.estimated_hours,
                        labels=task.labels.copy() if task.labels else [],
                        created_by=request.user
                    )
        
        serializer = BoardSerializer(new_board, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TaskViewSet(viewsets.ModelViewSet):
    """API ViewSet for Task management"""
    permission_classes = [TaskManagementPermission]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TaskCreateUpdateSerializer
        return TaskSerializer
    
    def get_queryset(self):
        """Filtre les tâches avec isolation organisationnelle"""
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        # Filtrer par tableau si spécifié
        board_id = self.request.query_params.get('board')
        if board_id:
            base_queryset = base_queryset.filter(board_id=board_id)
        
        return base_queryset.select_related(
            'board', 'column', 'created_by', 'parent_task'
        ).prefetch_related(
            'assignments__assignee',
            'comments__author',
            'subtasks'
        )
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Move task to different column/position"""
        task = self.get_object()
        
        # Check permission
        if not check_board_access(request.user, task.board, 'edit'):
            return Response({
                'error': 'Permission insuffisante'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TaskMoveSerializer(
            data=request.data,
            context={'task': task}
        )
        
        if serializer.is_valid():
            column_id = serializer.validated_data['column_id']
            position = serializer.validated_data.get('position', 0)
            
            try:
                new_column = Column.objects.get(id=column_id, board=task.board)
            except Column.DoesNotExist:
                return Response({
                    'error': 'Colonne invalide'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check WIP limit
            if new_column.wip_limit and task.column != new_column:
                current_count = new_column.tasks.count()
                if current_count >= new_column.wip_limit:
                    return Response({
                        'error': f'Limite WIP atteinte pour cette colonne ({current_count}/{new_column.wip_limit})',
                        'wip_exceeded': True
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Move task
            old_status = task.status
            move_task(task, new_column, position)
            
            # Update status if moved to done column
            if new_column.is_done_column and task.status != 'done':
                task.status = 'done'
                if not task.completed_at:
                    task.completed_at = timezone.now()
                task.save()
            elif not new_column.is_done_column and task.status == 'done':
                task.status = 'in_progress'
                task.completed_at = None
                task.save()
            
            # Return updated task data
            serializer = TaskSerializer(task, context={'request': request})
            return Response({
                'success': True,
                'task': serializer.data,
                'status_changed': old_status != task.status,
                'column_stats': {
                    'task_count': new_column.tasks.count(),
                    'wip_status': new_column.get_wip_status(),
                }
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign users to task"""
        task = self.get_object()
        
        if not task.can_edit(request.user):
            return Response({
                'error': 'Permission insuffisante'
            }, status=status.HTTP_403_FORBIDDEN)
        
        assignee_ids = request.data.get('assignee_ids', [])
        
        with transaction.atomic():
            # Remove existing assignments
            task.assignments.all().delete()
            
            # Create new assignments
            for assignee_id in assignee_ids:
                try:
                    from django.contrib.auth import get_user_model
                    from apps.organizations.utils import get_user_organization
                    User = get_user_model()
                    assignee = User.objects.get(id=assignee_id)
                    TaskAssignment.objects.create(
                        task=task,
                        assignee=assignee,
                        assigned_by=request.user,
                        role=TaskAssignment.AssignmentRole.ASSIGNEE
                    )
                except User.DoesNotExist:
                    pass
        
        # Return updated task
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Get task activity history"""
        task = self.get_object()
        
        from .utils import get_task_activity
        days = int(request.query_params.get('days', 30))
        activity = get_task_activity(task, days)
        
        return Response({
            'activity': activity,
            'task_id': task.id,
            'days': days
        })


class TaskCommentViewSet(viewsets.ModelViewSet):
    """API ViewSet for Task Comments"""
    serializer_class = TaskCommentSerializer
    permission_classes = [TaskManagementPermission]
    
    def get_queryset(self):
        """Filtre les commentaires avec isolation organisationnelle"""
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        # Filtrer par tâche si spécifiée
        task_id = self.kwargs.get('task_pk') or self.request.query_params.get('task')
        if task_id:
            return base_queryset.filter(task_id=task_id).select_related('author', 'parent_comment').order_by('created_at')
        
        return base_queryset.none()
    
    def perform_create(self, serializer):
        task_id = self.kwargs.get('task_pk') or self.request.data.get('task')
        task = get_object_or_404(Task, id=task_id)
        
        # Check permission
        if not task.board.can_access(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Accès refusé à cette tâche")
        
        serializer.save(
            task=task,
            author=self.request.user
        )


class ColumnViewSet(viewsets.ModelViewSet):
    """API ViewSet for Column management"""
    serializer_class = ColumnSerializer
    permission_classes = [TaskManagementPermission]
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        board_id = self.kwargs.get('board_pk') or self.request.query_params.get('board')
        if board_id:
            # Check board access
            try:
                board = Board.objects.get(id=board_id)
                if not board.can_access(self.request.user):
                    return Column.objects.none()
                
                return board.columns.all().annotate(
                    task_count=Count('tasks')
                ).order_by('position')
            except Board.DoesNotExist:
                return Column.objects.none()
        
        return Column.objects.none()
    
    def perform_create(self, serializer):
        board_id = self.kwargs.get('board_pk')
        board = get_object_or_404(Board, id=board_id)
        
        # Check permission
        if not board.can_edit(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Permission insuffisante")
        
        # Set position if not provided
        if 'position' not in serializer.validated_data:
            max_position = board.columns.aggregate(
                max_pos=models.Max('position')
            )['max_pos'] or 0
            serializer.validated_data['position'] = max_position + 1
        
        serializer.save(board=board)
    
    @action(detail=True, methods=['post'])
    def update_wip(self, request, pk=None):
        """Update column WIP limit"""
        column = self.get_object()
        
        # Check permission
        if not check_board_access(request.user, column.board, 'admin'):
            return Response({
                'error': 'Permission insuffisante'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            wip_limit = request.data.get('wip_limit')
            if wip_limit is not None:
                wip_limit = int(wip_limit) if wip_limit else None
                if wip_limit is not None and wip_limit <= 0:
                    wip_limit = None
            
            column.wip_limit = wip_limit
            column.save()
            
            return Response({
                'success': True,
                'wip_limit': wip_limit,
                'wip_status': column.get_wip_status(),
                'current_count': column.task_count
            })
        
        except (ValueError, TypeError):
            return Response({
                'error': 'Limite WIP invalide'
            }, status=status.HTTP_400_BAD_REQUEST)


class BoardTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """API ViewSet for Board Templates (read-only)"""
    serializer_class = BoardTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtre les modèles de tableaux avec isolation organisationnelle"""
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        # Modèles publics
        return base_queryset.filter(is_public=True).order_by('-is_system_template', 'name')
    
    @action(detail=True, methods=['post'])
    def create_board(self, request, pk=None):
        """Create board from template"""
        template = self.get_object()
        
        name = request.data.get('name')
        description = request.data.get('description', template.description)
        organization_id = request.data.get('organization')
        
        if not name or not organization_id:
            return Response({
                'error': 'Nom et organisation requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Import here to avoid circular imports
            from apps.organizations.models import Organization, OrganizationMember
            
            organization = Organization.objects.get(id=organization_id)
            
            # Check user permission
            OrganizationMember.objects.get(
                user=request.user,
                organization=organization,
                is_active=True,
                role__in=['owner', 'admin']
            )
            
            # Create board from template
            from .utils import create_board_from_template
            board = create_board_from_template(
                template=template,
                organization=organization,
                user=request.user,
                name=name,
                description=description
            )
            
            serializer = BoardSerializer(board, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# Import models for aggregation
from django.db import models